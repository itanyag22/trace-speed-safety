"""
TRACE - ESRI Export Module

Exports scored road network data in three formats for use in the ADB GIS Sandbox.

Outputs:
- GeoJSON: full network and priority-only layers for Experience Builder and Dashboard
- Shapefile: priority segments with 10-character field names for maximum compatibility
- CSV: segment centroids with all attributes for table joins

All outputs use WGS84 (EPSG:4326). Field names are mapped to ESRI-safe short names.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, 'outputs', 'esri')

import geopandas as gpd
import pandas as pd
import numpy as np
import json
import zipfile

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
    gdf = gdf.copy()
    if gdf.crs and gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(epsg=4326)
    rename = {orig: info[0] for orig, info in FIELD_MAP.items() if orig in gdf.columns}
    gdf = gdf.rename(columns=rename)
    float_cols = ['spd_limit', 'v85_kmh', 't1_scr', 't1_score', 't2_score', 't3_score', 'sss']
    int_cols   = ['vru_thr', 'p1_count']
    str_cols   = ['road_name', 'road_class', 'land_use', 'priority', 'driver',
                  'robustness', 'explain', 'country', 't2_eis', 'img_coords']
    for col in float_cols:
        if col in gdf.columns:
            gdf[col] = pd.to_numeric(gdf[col], errors='coerce').round(2)
    for col in int_cols:
        if col in gdf.columns:
            gdf[col] = pd.to_numeric(gdf[col], errors='coerce').fillna(0).astype(int)
    for col in str_cols:
        if col in gdf.columns:
            gdf[col] = gdf[col].apply(safe_val).fillna('')
    keep = [v[0] for v in FIELD_MAP.values() if v[0] in gdf.columns] + ['geometry']
    gdf = gdf[[c for c in keep if c in gdf.columns]]
    return gdf


def export_geojson_full(gdf, path, label):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    gdf.to_file(path, driver='GeoJSON')
    size_mb = os.path.getsize(path) / 1e6
    print(f"  [{label}] Full GeoJSON: {path} ({size_mb:.1f} MB, {len(gdf):,} segments)")


def export_geojson_priority(gdf, path, label):
    priority_gdf = gdf[gdf['priority'].isin([
        'P1: Immediate Review', 'P2: Secondary Review'
    ])].copy()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    priority_gdf.to_file(path, driver='GeoJSON')
    size_mb = os.path.getsize(path) / 1e6
    print(f"  [{label}] Priority GeoJSON: {path} ({size_mb:.1f} MB, {len(priority_gdf):,} segments)")


def export_shapefile(gdf, folder, label):
    os.makedirs(folder, exist_ok=True)
    shp_gdf = gdf.copy()
    rename_shp = {v: SHP_FIELD_MAP.get(v, v[:10]) for v in shp_gdf.columns if v != 'geometry'}
    shp_gdf = shp_gdf.rename(columns=rename_shp)
    if 'explain' in shp_gdf.columns:
        shp_gdf['explain'] = shp_gdf['explain'].str[:250]
    shp_path = os.path.join(folder, 'trace_priority.shp')
    shp_gdf.to_file(shp_path, driver='ESRI Shapefile')
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
    df = gdf.drop(columns=['geometry']).copy()
    centroids = gdf.geometry.centroid
    df['centroid_lon'] = centroids.x.round(6)
    df['centroid_lat'] = centroids.y.round(6)
    df.to_csv(path, index=False)
    size_kb = os.path.getsize(path) / 1e3
    print(f"  [{label}] Centroid CSV: {path} ({size_kb:.0f} KB, {len(df):,} rows)")


def write_esri_readme(path):
    content = """# TRACE - ESRI GIS Sandbox Import Guide

## Files in this package

| File | Use |
|---|---|
| `thailand_full.geojson` | Complete Thailand network (all segments) |
| `thailand_priority.geojson` | Thailand P1+P2 segments only |
| `maharashtra_full.geojson` | Complete Maharashtra network |
| `maharashtra_priority.geojson` | Maharashtra P1+P2 segments only |
| `thailand_shapefile.zip` | Thailand priority segments as Shapefile |
| `maharashtra_shapefile.zip` | Maharashtra priority segments as Shapefile |
| `thailand_centroids.csv` | Segment centroids with all attributes |
| `maharashtra_centroids.csv` | Same for Maharashtra |
| `field_dictionary.csv` | All field names and descriptions |

## Recommended import sequence

1. Upload `thailand_priority.geojson` and `maharashtra_priority.geojson` as Hosted Feature Layers.
2. Upload full network GeoJSON as a background layer set to grey with reduced opacity.
3. Configure popups using `field_dictionary.csv` for readable field labels.
4. Symbolize by `sss` using a 4-class colour ramp:
   - Red: sss < 40
   - Orange: sss 40-59
   - Yellow: sss 60-79
   - Green: sss >= 80

## CRS
All files are in WGS84 (EPSG:4326). No reprojection needed for ESRI Online.
"""
    with open(path, 'w') as f:
        f.write(content)
    print(f"  ESRI README: {path}")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    outputs_dir = os.path.join(BASE_DIR, 'outputs')

    print("Loading outputs...")
    try:
        th = gpd.read_file(os.path.join(outputs_dir, 'trace_thailand_sensitivity.geojson'))
        mh = gpd.read_file(os.path.join(outputs_dir, 'trace_maharashtra_sensitivity.geojson'))
    except Exception:
        th = gpd.read_file(os.path.join(outputs_dir, 'trace_thailand.geojson'))
        mh = gpd.read_file(os.path.join(outputs_dir, 'trace_maharashtra.geojson'))

    print("\nPreparing fields...")
    th_clean = prepare_gdf(th)
    mh_clean = prepare_gdf(mh)

    print("\nExporting GeoJSON layers...")
    export_geojson_full(th_clean, os.path.join(OUTPUT_DIR, 'thailand_full.geojson'), 'Thailand')
    export_geojson_priority(th_clean, os.path.join(OUTPUT_DIR, 'thailand_priority.geojson'), 'Thailand')
    export_geojson_full(mh_clean, os.path.join(OUTPUT_DIR, 'maharashtra_full.geojson'), 'Maharashtra')
    export_geojson_priority(mh_clean, os.path.join(OUTPUT_DIR, 'maharashtra_priority.geojson'), 'Maharashtra')

    print("\nExporting Shapefiles...")
    th_priority = th_clean[th_clean['priority'].isin(['P1: Immediate Review', 'P2: Secondary Review'])].copy()
    mh_priority = mh_clean[mh_clean['priority'].isin(['P1: Immediate Review', 'P2: Secondary Review'])].copy()
    export_shapefile(th_priority, os.path.join(OUTPUT_DIR, 'thailand_shapefile'), 'Thailand')
    export_shapefile(mh_priority, os.path.join(OUTPUT_DIR, 'maharashtra_shapefile'), 'Maharashtra')

    print("\nExporting centroid CSVs...")
    export_centroid_csv(th_priority, os.path.join(OUTPUT_DIR, 'thailand_centroids.csv'), 'Thailand')
    export_centroid_csv(mh_priority, os.path.join(OUTPUT_DIR, 'maharashtra_centroids.csv'), 'Maharashtra')

    print("\nWriting field dictionary and README...")
    export_field_dictionary(os.path.join(OUTPUT_DIR, 'field_dictionary.csv'))
    write_esri_readme(os.path.join(OUTPUT_DIR, 'ESRI_IMPORT_GUIDE.md'))

    # Final zip of all ESRI outputs
    print("\nZipping ESRI package...")
    zip_path = os.path.join(outputs_dir, 'TRACE_ESRI_package.zip')
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for fname in os.listdir(OUTPUT_DIR):
            fp = os.path.join(OUTPUT_DIR, fname)
            if os.path.isfile(fp):
                zf.write(fp, fname)
        for country in ['thailand', 'maharashtra']:
            cp = os.path.join(outputs_dir, f'corridor_priority_{country}.csv')
            if os.path.exists(cp):
                zf.write(cp, f'corridor_priority_{country}.csv')

    size_mb = os.path.getsize(zip_path) / 1e6
    print(f"\n  ESRI package: {zip_path} ({size_mb:.1f} MB)")
    print("\n  Done.")


if __name__ == '__main__':
    main()
