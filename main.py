"""
TRACE (Main Pipeline Orchestrator)
Tiered Road Alignment and Composite Evaluation

Runs on Thailand and Maharashtra datasets from ADB AI for Safer Roads Innovation Challenge.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import geopandas as gpd
import pandas as pd
import yaml
import json

from tiers.tier1_speed import run_tier1
from tiers.tier2_environment import run_tier2
from tiers.tier3_vru import run_tier3
from scoring.compositor import run_scoring
from visualization.map_renderer import render_map


def load_config(path):
    with open(path) as f:
        return yaml.safe_load(f)


def load_thailand(config):
    print("\n[Thailand] Loading ADB_Results_D4 layer...")
    gdf = gpd.read_file(config['paths']['thailand_gpkg'], layer='ADB_Results_D4')
    # Only work with segments that have either speed data or can be analyzed by T2/T3
    # Keep all segments (T1 gives neutral score when no data)
    gdf['country'] = 'Thailand'
    print(f"  Loaded {len(gdf)} segments. CRS: {gdf.crs}")
    return gdf


def load_maharashtra(config):
    print("\n[Maharashtra] Loading OvertureNetwork_wResults layer...")
    gdf = gpd.read_file(config['paths']['maharashtra_gpkg'], layer='OvertureNetwork_wResults')
    # Rename geometry column if needed
    if 'SHAPE' in gdf.columns and 'geometry' not in gdf.columns:
        gdf = gdf.rename_geometry('geometry')
    gdf['country'] = 'Maharashtra'
    # Map 'class' to RoadClass if needed
    if 'class' in gdf.columns and 'RoadClass' not in gdf.columns:
        gdf['RoadClass'] = gdf['class']
    # names_primary -> english_ro equivalent
    if 'names_primary' in gdf.columns:
        gdf['english_ro'] = gdf['names_primary']
    print(f"  Loaded {len(gdf)} segments. CRS: {gdf.crs}")
    return gdf


def run_country(gdf, country_name, config, output_suffix):
    print(f"\n{'='*60}")
    print(f"  Running TRACE for: {country_name}")
    print(f"{'='*60}")

    weights = config['weights']
    use_urban_pc = 'UrbanPC' in gdf.columns

    # Run tiers
    print("\n[Tier 1] Operating Speed Alignment...")
    gdf = run_tier1(gdf)

    print("\n[Tier 2] Road Environment Alignment...")
    gdf = run_tier2(gdf, use_urban_pc=use_urban_pc)

    print("\n[Tier 3] VRU Protection Threshold...")
    gdf = run_tier3(gdf, country=country_name)

    print("\n[Scoring] Composite SSS...")
    gdf = run_scoring(gdf, weights)

    # Save GeoJSON
    out_dir = config['paths']['output_dir']
    os.makedirs(out_dir, exist_ok=True)

    out_geojson = f"{out_dir}/trace_{output_suffix}.geojson"
    out_map = f"{out_dir}/trace_{output_suffix}_map.html"

    # Export (keep key columns only for clean GeoJSON)
    export_cols = [
        'geometry', 'english_ro', 'RoadClass', 'LandUse', 'SpeedLimit',
        'MedianSpeed', 'F85thPercentileSpeed', 'PercentOverLimit',
        't1_score', 't1_scr', 't2_score', 't2_eis_range', 't2_source',
        't3_score', 't3_vru_threshold', 'sss', 'priority_flag',
        'color', 'explanation', 'StreetImageLink', 'country'
    ]
    if 'UrbanPC' in gdf.columns:
        export_cols.append('UrbanPC')

    existing_cols = [c for c in export_cols if c in gdf.columns]
    gdf_export = gdf[existing_cols].copy()
    gdf_export = gdf_export.to_crs(epsg=4326)
    gdf_export.to_file(out_geojson, driver='GeoJSON')
    print(f"\n  GeoJSON saved: {out_geojson}")

    # Render map
    print(f"\n[Visualization] Rendering map...")
    render_map(gdf_export, out_map, title=f"TRACE – {country_name} Speed Safety Score")

    # Print summary
    print(f"\n{'='*60}")
    print(f"  SUMMARY: {country_name}")
    print(f"{'='*60}")
    for flag in ['P1: Immediate Review', 'P2: Secondary Review', 'P3: Monitor', 'Acceptable']:
        n = (gdf['priority_flag'] == flag).sum()
        pct = 100 * n / len(gdf)
        print(f"  {flag:<30}: {n:>6} segments ({pct:.1f}%)")
    print(f"  Mean SSS: {gdf['sss'].mean():.1f}")
    print(f"  Segments with SCR data: {gdf['t1_scr'].notna().sum()}")

    return gdf


def main():
    config = load_config('/home/claude/trace_project/config/config.yaml')

    # Thailand
    th = load_thailand(config)
    th_result = run_country(th, 'Thailand', config, 'thailand')

    # Maharashtra
    mh = load_maharashtra(config)
    mh_result = run_country(mh, 'Maharashtra', config, 'maharashtra')

    # Combined summary
    print(f"\n{'='*60}")
    print("  COMBINED SUMMARY")
    print(f"{'='*60}")
    combined = pd.concat([
        th_result[['priority_flag', 'sss', 't1_score', 't2_score', 't3_score']],
        mh_result[['priority_flag', 'sss', 't1_score', 't2_score', 't3_score']]
    ])
    print(combined.groupby('priority_flag').agg(
        count=('sss', 'count'),
        mean_sss=('sss', 'mean'),
        mean_t1=('t1_score', 'mean'),
        mean_t2=('t2_score', 'mean'),
        mean_t3=('t3_score', 'mean'),
    ).round(1).to_string())

    print(f"\nAll outputs in: {config['paths']['output_dir']}")


if __name__ == '__main__':
    main()
