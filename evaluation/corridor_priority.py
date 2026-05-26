"""
TRACE (Corridor-Level Priority Table)
Groups road segments into corridors by named road or road-class/land-use cluster.
Ranked by priority level then total length.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

import geopandas as gpd
import pandas as pd
import numpy as np

PRIORITY_LEVELS = ['P1: Immediate Review', 'P2: Secondary Review']


def safe_float(x):
    try:
        v = float(x)
        return v if not np.isnan(v) else np.nan
    except (TypeError, ValueError):
        return np.nan


def clean_name(val):
    if val is None:
        return None
    s = str(val).strip()
    return s if s and s.lower() != 'nan' else None


def segment_length_km(geom):
    try:
        coords = (list(geom.coords) if geom.geom_type == 'LineString'
                  else [c for part in geom.geoms for c in part.coords])
        if len(coords) < 2:
            return 0.0
        lat = np.mean([c[1] for c in coords])
        kplon = 111.0 * np.cos(np.radians(lat))
        kplat = 111.0
        total = sum(
            np.sqrt(((coords[i+1][0]-coords[i][0])*kplon)**2 +
                    ((coords[i+1][1]-coords[i][1])*kplat)**2)
            for i in range(len(coords)-1)
        )
        return round(total, 4)
    except Exception:
        return 0.0


def build_corridors(gdf, priority_levels):
    priority_gdf = gdf[gdf['priority_flag'].isin(priority_levels)].copy()
    priority_gdf['length_km'] = priority_gdf.geometry.apply(segment_length_km)
    priority_gdf['road_name_clean'] = priority_gdf['english_ro'].apply(clean_name)
    priority_gdf['road_class'] = priority_gdf['RoadClass'].fillna('unknown')
    priority_gdf['land_use']   = priority_gdf['LandUse'].fillna('unknown')

    corridors = []

    named = priority_gdf[priority_gdf['road_name_clean'].notna()].copy()
    for (road_name, road_class), group in named.groupby(
            ['road_name_clean', 'road_class'], sort=False):
        corridors.append(_corridor_stats(group, road_name, road_class, named=True))

    unnamed = priority_gdf[priority_gdf['road_name_clean'].isna()].copy()
    for (road_class, land_use), group in unnamed.groupby(
            ['road_class', 'land_use'], sort=False):
        label = f"[Unnamed {road_class} / {land_use}]"
        corridors.append(_corridor_stats(group, label, road_class, named=False))

    df = pd.DataFrame(corridors)
    df['has_p1'] = df['p1_segments'] > 0
    df = df.sort_values(['has_p1', 'total_length_km'], ascending=[False, False])
    df = df.drop(columns=['has_p1'])
    df.insert(0, 'rank', range(1, len(df)+1))
    return df


def _corridor_stats(group, road_name, road_class, named=True):
    p1_n = (group['priority_flag'] == 'P1: Immediate Review').sum()
    p2_n = (group['priority_flag'] == 'P2: Secondary Review').sum()
    mean_sss  = round(group['sss'].mean(), 1)
    min_sss   = round(group['sss'].min(), 1)
    mean_t1   = round(group['t1_score'].mean(), 1)
    mean_t2   = round(group['t2_score'].mean(), 1)
    mean_t3   = round(group['t3_score'].mean(), 1)
    land_use  = group['land_use'].mode()[0] if len(group) > 0 else 'unknown'
    total_len = round(group['length_km'].sum(), 2)

    speed_rows = group[group['t1_scr'].notna()]
    mean_v85   = round(speed_rows['F85thPercentileSpeed'].apply(safe_float).mean(), 1) \
                 if len(speed_rows) else None
    mean_limit = round(speed_rows['SpeedLimit'].apply(safe_float).mean(), 1) \
                 if len(speed_rows) else None
    mean_scr   = round(speed_rows['t1_scr'].mean(), 2) if len(speed_rows) else None

    vru_vals = group['t3_vru_threshold'].apply(safe_float)
    vru_t = int(vru_vals.min()) if not vru_vals.isna().all() else None

    driver = min(
        {'T1': mean_t1, 'T2': mean_t2, 'T3': mean_t3},
        key=lambda k: {'T1': mean_t1, 'T2': mean_t2, 'T3': mean_t3}[k]
    )
    robust = group['robustness'].mode()[0] if 'robustness' in group.columns else 'N/A'

    return {
        'road_name':         road_name,
        'road_class':        road_class,
        'land_use':          land_use,
        'named':             named,
        'p1_segments':       int(p1_n),
        'p2_segments':       int(p2_n),
        'total_segments':    len(group),
        'total_length_km':   total_len,
        'mean_sss':          mean_sss,
        'min_sss':           min_sss,
        'mean_t1':           mean_t1,
        'mean_t2':           mean_t2,
        'mean_t3':           mean_t3,
        'primary_driver':    driver,
        'mean_v85_kmh':      mean_v85,
        'mean_limit_kmh':    mean_limit,
        'mean_scr':          mean_scr,
        'vru_threshold_kmh': vru_t,
        'robustness':        robust,
    }


def build_report(th_df, mh_df):
    lines = []
    lines.append("# TRACE - Corridor Priority Table\n")
    lines.append(
        "Priority segments are aggregated into corridors for ministry-level action. "
        "Named roads are grouped by road name and class. Segments without a road name "
        "are grouped by road class and land use. Corridors are ranked by priority level "
        "(P1-containing first) then total length.\n\n"
        "**Columns:** SCR = V85 / posted limit. Driver = tier with lowest mean score "
        "(T1 speed, T2 environment, T3 VRU protection). VRU threshold = applicable "
        "Safe System biomechanical limit in km/h.\n"
    )
    lines.append("---\n")

    for country, df in [("Thailand", th_df), ("Maharashtra", mh_df)]:
        p1_corr  = df[df['p1_segments'] > 0]
        p2_corr  = df[(df['p1_segments'] == 0) & (df['p2_segments'] > 0)]
        p1_km    = p1_corr['total_length_km'].sum()
        p2_km    = p2_corr['total_length_km'].sum()
        named_p1 = p1_corr[p1_corr['named']]['road_name'].nunique()

        lines.append(f"## {country}\n")
        lines.append(f"Priority corridors: {len(df):,} total | "
                     f"P1 corridors: {len(p1_corr)} ({p1_km:.1f} km) | "
                     f"P2 corridors: {len(p2_corr)} ({p2_km:.1f} km) | "
                     f"Named P1 roads: {named_p1}\n")

        if len(p1_corr) > 0:
            lines.append("### P1 corridors\n")
            lines.append("| Rank | Road | Class | Land use | P1 segs | P2 segs | "
                         "Length km | Min SSS | Mean SSS | V85 | Limit | SCR | VRU threshold | Driver |")
            lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
            for _, r in p1_corr.iterrows():
                v85 = f"{r['mean_v85_kmh']:.0f}" if r['mean_v85_kmh'] else "—"
                lim = f"{r['mean_limit_kmh']:.0f}" if r['mean_limit_kmh'] else "—"
                scr = f"{r['mean_scr']:.2f}" if r['mean_scr'] else "—"
                vru = f"{r['vru_threshold_kmh']} km/h" if r['vru_threshold_kmh'] else "—"
                lines.append(
                    f"| {r['rank']} | {r['road_name']} | {r['road_class']} | {r['land_use']} "
                    f"| **{r['p1_segments']}** | {r['p2_segments']} | {r['total_length_km']} "
                    f"| {r['min_sss']} | {r['mean_sss']} | {v85} | {lim} | {scr} | {vru} | {r['primary_driver']} |"
                )

        p2_named = p2_corr[p2_corr['named']].head(20)
        if len(p2_named) > 0:
            lines.append("\n### P2 corridors - named roads, top 20 by length\n")
            lines.append("| Rank | Road | Class | Land use | P2 segs | Length km | "
                         "Mean SSS | V85 | Limit | SCR | Driver |")
            lines.append("|---|---|---|---|---|---|---|---|---|---|---|")
            for _, r in p2_named.iterrows():
                v85 = f"{r['mean_v85_kmh']:.0f}" if r['mean_v85_kmh'] else "—"
                lim = f"{r['mean_limit_kmh']:.0f}" if r['mean_limit_kmh'] else "—"
                scr = f"{r['mean_scr']:.2f}" if r['mean_scr'] else "—"
                lines.append(
                    f"| {r['rank']} | {r['road_name']} | {r['road_class']} | {r['land_use']} "
                    f"| {r['p2_segments']} | {r['total_length_km']} | {r['mean_sss']} "
                    f"| {v85} | {lim} | {scr} | {r['primary_driver']} |"
                )
        lines.append("\n---\n")

    return "\n".join(lines)


def main():
    outputs_dir = os.path.join(BASE_DIR, 'outputs')
    eval_dir    = os.path.join(BASE_DIR, 'evaluation')

    print("Loading outputs...")
    try:
        th = gpd.read_file(os.path.join(outputs_dir, 'trace_thailand_sensitivity.geojson'))
        mh = gpd.read_file(os.path.join(outputs_dir, 'trace_maharashtra_sensitivity.geojson'))
    except Exception:
        th = gpd.read_file(os.path.join(outputs_dir, 'trace_thailand.geojson'))
        mh = gpd.read_file(os.path.join(outputs_dir, 'trace_maharashtra.geojson'))

    print("Building Thailand corridors...")
    th_df = build_corridors(th, PRIORITY_LEVELS)
    print(f"  {len(th_df)} corridors | P1: {len(th_df[th_df['p1_segments']>0])}")

    print("Building Maharashtra corridors...")
    mh_df = build_corridors(mh, PRIORITY_LEVELS)
    print(f"  {len(mh_df)} corridors | P1: {len(mh_df[mh_df['p1_segments']>0])}")

    for country, df in [('thailand', th_df), ('maharashtra', mh_df)]:
        path = os.path.join(outputs_dir, f'corridor_priority_{country}.csv')
        df.to_csv(path, index=False)
        print(f"  CSV: {path}")

    report = build_report(th_df, mh_df)
    rpath = os.path.join(eval_dir, 'corridor_priority_report.md')
    with open(rpath, 'w') as f:
        f.write(report)
    print(f"  Report: {rpath}")

    cols = ['rank', 'road_name', 'road_class', 'land_use', 'p1_segments',
            'total_length_km', 'min_sss', 'mean_sss', 'mean_v85_kmh',
            'mean_limit_kmh', 'mean_scr', 'vru_threshold_kmh', 'primary_driver']

    print("\n=== THAILAND P1 CORRIDORS ===")
    print(th_df[th_df['p1_segments']>0][cols].to_string(index=False))

    print("\n=== MAHARASHTRA P1 CORRIDORS ===")
    print(mh_df[mh_df['p1_segments']>0][cols].to_string(index=False))


if __name__ == '__main__':
    main()
    
