"""
TRACE - ESRI-Ready Export
Produces three output formats for ADB GIS Sandbox (ESRI):

1. GeoJSON feature layers — for Experience Builder / Dashboard
   - Full network (all segments)
   - P1+P2 priority segments only (lighter, faster load)

2. CSV with lat/lon centroid — for ESRI table join or hosted table
   - Corridor priority table

3. Shapefile — maximum ESRI compatibility fallback
   - Priority segments only (field names truncated to 10 chars)

Field mapping: verbose names -> ESRI-safe short names
All fields typed explicitly. CRS locked to EPSG:4326.
"""

import sys
sys.path.insert(0, '/home/claude/trace_project')

import geopandas as gpd
import pandas as pd
import numpy as np
import json
import os
import zipfile

OUTPUT_DIR = '/home/claude/trace_project/outputs/esri'


# ── Field mapping: original -> (esri_name, description) ─────────────────────
FIELD_MAP = {
    'english_ro':           ('road_name',   'Road name'),
    'RoadClass':            ('road_class',  'Road functional class'),
    'LandUse':              ('land_use',    'Land use classification'),
    'SpeedLimit':           ('spd_limit',   'Posted speed limit (km/h)'),
    'F85thPercentileSpeed': ('v85_kmh',     '85th percentile operating speed (km/h)'),
    't1_scr':               ('t1_scr',      'Speed Compliance Ratio (V85/limit)'),
    't1_score':             ('t1_score',    'Tier 1: Operating speed alignment (0-100)'),
    't2_score':             ('t2_score',    'Tier 2: Road environment alignment (0-100)'),
    't2_eis_range':         ('t2_eis',      'Environment-implied speed range (km/h)'),
    't3_score':             ('t3_score',    'Tier 3: VRU protection alignment (0-100)'),
    't3_vru_threshold':     ('vru_thr',     'Safe System VRU threshold (km/h)'),
    'sss':                  ('sss',         'Speed Safety Score (0-100)'),
    'priority_flag':        ('priority',    'Priority classification'),
    'primary_driver':       ('driver',      'Primary misalignment tier'),
    'robustness':           ('robustness',  'Sensitivity robustness grade'),
    'core_p1_count':        ('p1_count',    'P1 flag count across 8 weight combinations'),
    'explanation':          ('explain',     'Plain-language misalignment description'),
    'StreetImageLink':      ('img_coords',  'Mapillary image coordinates'),
    'country':              ('country',     'Country'),
}

# Shapefile names must be <=10 chars
SHP_FIELD_MAP = {
    'road_name':  'road_name',
    'road_class': 'road_cls',
    'land_use':   'land_use',
    'spd_limit':  'spd_lim',
    'v85_kmh':    'v85_kmh',
    't1_scr':     't1_scr',
    't1_score':   't1_score',
    't2_score':   't2_score',
    't2_eis':     't2_eis',
    't3_score':   't3_score',
    'vru_thr':    'vru_thr',
    'sss':        'sss',
    'priority':   'priority',
    'driver':     'driver',
    'robustness': 'robust',
    'p1_count':   'p1_count',
    'explain':    'explain',
    'country':    'country',
}


def safe_val(x):
    """Convert mixed types to clean Python native for JSON serialization."""
    if x is None:
        return None
    if isinstance(x, float) and np.isnan(x):
        return None
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (np.floating,)):
        return round(float(x), 4)
    if isinstance(x, bool):
        return x
    s = str(x)
    return None if s.lower() in ('nan', 'none', '') else s


def prepare_gdf(gdf):
    """Rename fields, clean types, ensure WGS84."""
    gdf = gdf.copy()

    # Ensure WGS84
    if gdf.crs and gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(epsg=4326)

    # Rename to ESRI-safe names
    rename = {orig: info[0] for orig, info in FIELD_MAP.items() if orig in gdf.columns}
    gdf = gdf.rename(columns=rename)

    # Clean types
    float_cols = ['spd_limit', 'v85_kmh', 't1_scr', 't1_score', 't2_score',
                  't3_score', 'sss']
    int_cols   = ['vru_thr', 'p1_count']
    str_cols   = ['road_name', 'road_class', 'land_use', 'priority',
                  'driver', 'robustness', 'explain', 'country', 't2_eis', 'img_coords']

    for col in float_cols:
        if col in gdf.columns:
            gdf[col] = pd.to_numeric(gdf[col], errors='coerce').round(2)

    for col in int_cols:
        if col in gdf.columns:
            gdf[col] = pd.to_numeric(gdf[col], errors='coerce').fillna(0).astype(int)

    for col in str_cols:
        if col in gdf.columns:
            gdf[col] = gdf[col].apply(safe_val).fillna('')

    # Keep only mapped columns + geometry
    keep = [v[0] for v in FIELD_MAP.values() if v[0] in gdf.columns] + ['geometry']
    gdf = gdf[[c for c in keep if c in gdf.columns]]

    return gdf


def export_geojson_full(gdf, path, label):
    """Export complete network as GeoJSON."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    gdf.to_file(path, driver='GeoJSON')
    size_mb = os.path.getsize(path) / 1e6
    print(f"  [{label}] Full GeoJSON: {path} ({size_mb:.1f} MB, {len(gdf):,} segments)")


def export_geojson_priority(gdf, path, label):
    """Export P1+P2 segments only — lighter layer for dashboard."""
    priority_gdf = gdf[gdf['priority'].isin([
        'P1: Immediate Review', 'P2: Secondary Review'
    ])].copy()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    priority_gdf.to_file(path, driver='GeoJSON')
    size_mb = os.path.getsize(path) / 1e6
    print(f"  [{label}] Priority GeoJSON: {path} ({size_mb:.1f} MB, {len(priority_gdf):,} segments)")


def export_shapefile(gdf, folder, label):
    """Export as shapefile with <=10 char field names."""
    os.makedirs(folder, exist_ok=True)
    shp_gdf = gdf.copy()

    # Apply shapefile name truncation
    rename_shp = {v: SHP_FIELD_MAP.get(v, v[:10]) for v in shp_gdf.columns if v != 'geometry'}
    shp_gdf = shp_gdf.rename(columns=rename_shp)

    # Truncate explain field for shapefile (254 char limit)
    if 'explain' in shp_gdf.columns:
        shp_gdf['explain'] = shp_gdf['explain'].str[:250]

    shp_path = os.path.join(folder, 'trace_priority.shp')
    shp_gdf.to_file(shp_path, driver='ESRI Shapefile')

    # Zip shapefile components
    zip_path = folder + '.zip'
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for ext in ['.shp', '.shx', '.dbf', '.prj', '.cpg']:
            fp = shp_path.replace('.shp', ext)
            if os.path.exists(fp):
                zf.write(fp, os.path.basename(fp))

    size_mb = os.path.getsize(zip_path) / 1e6
    print(f"  [{label}] Shapefile zip: {zip_path} ({size_mb:.1f} MB)")
    return zip_path


def export_field_dictionary(path):
    """Write a field dictionary CSV for ESRI popup configuration."""
    rows = []
    for orig, (esri_name, desc) in FIELD_MAP.items():
        shp_name = SHP_FIELD_MAP.get(esri_name, esri_name[:10])
        rows.append({
            'esri_field_name':      esri_name,
            'shapefile_field_name': shp_name,
            'original_field_name':  orig,
            'description':          desc,
        })
    df = pd.DataFrame(rows)
    df.to_csv(path, index=False)
    print(f"  Field dictionary: {path}")


def export_centroid_csv(gdf, path, label):
    """CSV with segment centroid lat/lon for ESRI table joins."""
    df = gdf.drop(columns=['geometry']).copy()
    centroids = gdf.geometry.centroid
    df['centroid_lon'] = centroids.x.round(6)
    df['centroid_lat'] = centroids.y.round(6)
    df.to_csv(path, index=False)
    size_kb = os.path.getsize(path) / 1e3
    print(f"  [{label}] Centroid CSV: {path} ({size_kb:.0f} KB, {len(df):,} rows)")


def write_esri_readme(path):
    content = """# TRACE — ESRI GIS Sandbox Import Guide

## Files in this package

| File | Use |
|---|---|
| `thailand_full.geojson` | Complete Thailand network (all segments) |
| `thailand_priority.geojson` | Thailand P1+P2 segments only — use this for the main dashboard layer |
| `maharashtra_full.geojson` | Complete Maharashtra network |
| `maharashtra_priority.geojson` | Maharashtra P1+P2 segments only |
| `thailand_shapefile.zip` | Thailand priority segments as Shapefile |
| `maharashtra_shapefile.zip` | Maharashtra priority segments as Shapefile |
| `thailand_centroids.csv` | Segment centroids with all attributes (for table joins) |
| `maharashtra_centroids.csv` | Same for Maharashtra |
| `field_dictionary.csv` | All field names and descriptions |

## Recommended import sequence for ESRI Experience Builder

1. Upload `thailand_priority.geojson` and `maharashtra_priority.geojson` as Hosted Feature Layers.
2. For full network context, upload `thailand_full.geojson` as a second layer — set default symbology to grey and reduce opacity.
3. Configure popup using `field_dictionary.csv` for human-readable field labels.
4. In Experience Builder or Dashboard, symbolize by `sss` (Speed Safety Score) using a 4-class colour ramp:
   - Red (#d62728): sss < 40
   - Orange (#ff7f0e): sss 40–59
   - Yellow (#bcbd22): sss 60–79
   - Green (#2ca02c): sss >= 80

## Recommended popup fields (in order)

1. `road_name` — Road name
2. `priority` — Priority classification
3. `sss` — Speed Safety Score
4. `t1_score`, `t2_score`, `t3_score` — Tier sub-scores
5. `spd_limit` — Posted speed limit
6. `v85_kmh` — 85th percentile operating speed
7. `t1_scr` — Speed Compliance Ratio
8. `vru_thr` — Safe System VRU threshold
9. `t2_eis` — Environment-implied speed range
10. `explain` — Plain-language explanation

## CRS
All files are in WGS84 (EPSG:4326). No reprojection needed for ESRI Online.

## File size note
Full GeoJSON files are large (Thailand ~80MB). If upload limits apply,
use the priority-only GeoJSONs or the shapefiles.
"""
    with open(path, 'w') as f:
        f.write(content)
    print(f"  ESRI README: {path}")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("Loading outputs...")
    try:
        th = gpd.read_file('/home/claude/trace_project/outputs/trace_thailand_sensitivity.geojson')
        mh = gpd.read_file('/home/claude/trace_project/outputs/trace_maharashtra_sensitivity.geojson')
    except Exception:
        th = gpd.read_file('/home/claude/trace_project/outputs/trace_thailand.geojson')
        mh = gpd.read_file('/home/claude/trace_project/outputs/trace_maharashtra.geojson')

    print("\nPreparing fields...")
    th_clean = prepare_gdf(th)
    mh_clean = prepare_gdf(mh)
    print(f"  Thailand: {len(th_clean):,} segments | Fields: {list(th_clean.columns)}")
    print(f"  Maharashtra: {len(mh_clean):,} segments")

    print("\nExporting GeoJSON layers...")
    export_geojson_full(th_clean,
        f'{OUTPUT_DIR}/thailand_full.geojson', 'Thailand')
    export_geojson_priority(th_clean,
        f'{OUTPUT_DIR}/thailand_priority.geojson', 'Thailand')
    export_geojson_full(mh_clean,
        f'{OUTPUT_DIR}/maharashtra_full.geojson', 'Maharashtra')
    export_geojson_priority(mh_clean,
        f'{OUTPUT_DIR}/maharashtra_priority.geojson', 'Maharashtra')

    print("\nExporting Shapefiles...")
    th_priority = th_clean[th_clean['priority'].isin(
        ['P1: Immediate Review', 'P2: Secondary Review'])].copy()
    mh_priority = mh_clean[mh_clean['priority'].isin(
        ['P1: Immediate Review', 'P2: Secondary Review'])].copy()
    export_shapefile(th_priority,
        f'{OUTPUT_DIR}/thailand_shapefile', 'Thailand')
    export_shapefile(mh_priority,
        f'{OUTPUT_DIR}/maharashtra_shapefile', 'Maharashtra')

    print("\nExporting centroid CSVs...")
    export_centroid_csv(th_priority,
        f'{OUTPUT_DIR}/thailand_centroids.csv', 'Thailand')
    export_centroid_csv(mh_priority,
        f'{OUTPUT_DIR}/maharashtra_centroids.csv', 'Maharashtra')

    print("\nWriting field dictionary and README...")
    export_field_dictionary(f'{OUTPUT_DIR}/field_dictionary.csv')
    write_esri_readme(f'{OUTPUT_DIR}/ESRI_IMPORT_GUIDE.md')

    # Final zip of all ESRI outputs
    print("\nZipping ESRI package...")
    zip_path = '/home/claude/trace_project/outputs/TRACE_ESRI_package.zip'
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for fname in os.listdir(OUTPUT_DIR):
            fp = os.path.join(OUTPUT_DIR, fname)
            if os.path.isfile(fp):
                zf.write(fp, fname)
        # Also include corridor CSVs
        for country in ['thailand', 'maharashtra']:
            cp = f'/home/claude/trace_project/outputs/corridor_priority_{country}.csv'
            if os.path.exists(cp):
                zf.write(cp, f'corridor_priority_{country}.csv')

    size_mb = os.path.getsize(zip_path) / 1e6
    print(f"\n  ESRI package: {zip_path} ({size_mb:.1f} MB)")
    print("\n  Done.")


if __name__ == '__main__':
    main()
