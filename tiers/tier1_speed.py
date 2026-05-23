"""
TRACE - Tier 1: Operating Speed Alignment
"""
import pandas as pd
import numpy as np


def _to_float(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return np.nan


def compute_scr(v85, speed_limit):
    sl = _to_float(speed_limit)
    v = _to_float(v85)
    if np.isnan(sl) or sl <= 0 or np.isnan(v):
        return np.nan
    return v / sl


def compute_svi(v85, v50, speed_limit):
    sl = _to_float(speed_limit)
    v8 = _to_float(v85)
    v5 = _to_float(v50)
    if np.isnan(sl) or sl <= 0 or np.isnan(v8) or np.isnan(v5):
        return np.nan
    return (v8 - v5) / sl


def scr_to_penalty(scr):
    if np.isnan(scr):
        return 0.3
    if scr <= 1.0:
        return 0.0
    elif scr <= 1.15:
        return ((scr - 1.0) / 0.15) * 0.5
    else:
        return min(1.0, 0.5 + ((scr - 1.15) / 0.35) * 0.5)


def svi_to_penalty(svi):
    if np.isnan(svi):
        return 0.1
    return min(1.0, max(0.0, (svi - 0.10) / 0.40))


def compute_t1_score(row):
    scr = compute_scr(row.get('F85thPercentileSpeed'), row.get('SpeedLimit'))
    svi = compute_svi(row.get('F85thPercentileSpeed'),
                      row.get('MedianSpeed'),
                      row.get('SpeedLimit'))
    v85 = _to_float(row.get('F85thPercentileSpeed'))
    v50 = _to_float(row.get('MedianSpeed'))
    if np.isnan(v85) and np.isnan(v50):
        return 50.0
    penalty = 0.70 * scr_to_penalty(scr) + 0.30 * svi_to_penalty(svi)
    return round(100 * (1 - penalty), 2)


def run_tier1(gdf):
    gdf = gdf.copy()
    gdf['t1_scr'] = gdf.apply(
        lambda r: compute_scr(r.get('F85thPercentileSpeed'), r.get('SpeedLimit')), axis=1)
    gdf['t1_svi'] = gdf.apply(
        lambda r: compute_svi(r.get('F85thPercentileSpeed'),
                              r.get('MedianSpeed'),
                              r.get('SpeedLimit')), axis=1)
    gdf['t1_score'] = gdf.apply(compute_t1_score, axis=1)
    scr_count = gdf['t1_scr'].notna().sum()
    print(f"  Tier 1 complete. Mean T1={gdf['t1_score'].mean():.1f}, "
          f"Segments with SCR data: {scr_count}")
    return gdf
