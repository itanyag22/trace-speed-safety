"""TRACE - Score Compositor and Explainer"""
import pandas as pd
import numpy as np


def _sf(x):
    try:
        v = float(x)
        return v if not np.isnan(v) else None
    except (TypeError, ValueError):
        return None


def composite_sss(row, weights):
    t1 = _sf(row.get('t1_score')) or 50.0
    t2 = _sf(row.get('t2_score')) or 50.0
    t3 = _sf(row.get('t3_score')) or 50.0
    return round(weights['t1'] * t1 + weights['t2'] * t2 + weights['t3'] * t3, 2)


def classify_priority(sss):
    if sss < 40:
        return 'P1: Immediate Review'
    elif sss < 60:
        return 'P2: Secondary Review'
    elif sss < 80:
        return 'P3: Monitor'
    return 'Acceptable'


def priority_color(flag):
    return {
        'P1: Immediate Review': '#d62728',
        'P2: Secondary Review': '#ff7f0e',
        'P3: Monitor':          '#bcbd22',
        'Acceptable':           '#2ca02c',
    }.get(flag, '#aec7e8')


def generate_explanation(row):
    parts = []
    t1 = _sf(row.get('t1_score')) or 50.0
    t2 = _sf(row.get('t2_score')) or 50.0
    t3 = _sf(row.get('t3_score')) or 50.0
    limit = _sf(row.get('SpeedLimit'))
    v85   = _sf(row.get('F85thPercentileSpeed'))
    vru_t = _sf(row.get('t3_vru_threshold'))
    scr   = _sf(row.get('t1_scr'))
    eis   = row.get('t2_eis_range', 'N/A')

    if t1 < 60 and v85 and limit:
        scr_str = f"{scr:.2f}" if scr else 'N/A'
        parts.append(
            f"Traffic moves at {v85:.0f} km/h (V85) on a road posted at "
            f"{limit:.0f} km/h (SCR={scr_str})."
        )
    if t2 < 60 and limit:
        parts.append(
            f"Road environment implies a safe speed of {eis} km/h, "
            f"below the posted {limit:.0f} km/h."
        )
    if t3 < 60 and limit and vru_t:
        parts.append(
            f"Posted limit {limit:.0f} km/h exceeds Safe System VRU threshold "
            f"of {vru_t:.0f} km/h given estimated exposure."
        )
    return " ".join(parts) if parts else "No significant misalignment detected."


def run_scoring(gdf, weights):
    gdf = gdf.copy()
    gdf['sss'] = gdf.apply(lambda r: composite_sss(r, weights), axis=1)
    gdf['priority_flag'] = gdf['sss'].apply(classify_priority)
    gdf['color'] = gdf['priority_flag'].apply(priority_color)
    gdf['explanation'] = gdf.apply(generate_explanation, axis=1)
    p1 = (gdf['priority_flag'] == 'P1: Immediate Review').sum()
    p2 = (gdf['priority_flag'] == 'P2: Secondary Review').sum()
    total = len(gdf)
    print(f"  Scoring complete. P1={p1} ({100*p1/total:.1f}%), "
          f"P2={p2} ({100*p2/total:.1f}%), total={total}")
    return gdf
# explanation generator updated
