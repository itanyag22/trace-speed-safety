"""
TRACE - Tier 2: Road Environment Alignment
Assesses whether posted limit AND operating speed align with what the road
environment physically supports. Uses network attributes as proxy for CV.
"""
import pandas as pd
import numpy as np

# Environment-implied safe speed ranges for Asian road context
# Calibrated conservatively for mixed-traffic, high-VRU environments
ENVIRONMENT_SPEED_TABLE = {
    ('motorway',   'RURAL'): (90, 110),
    ('motorway',   'URBAN'): (70,  90),
    ('trunk',      'RURAL'): (70,  90),
    ('trunk',      'URBAN'): (50,  70),
    ('primary',    'RURAL'): (60,  80),
    ('primary',    'URBAN'): (40,  60),
    ('secondary',  'RURAL'): (50,  70),
    ('secondary',  'URBAN'): (30,  50),
    ('tertiary',   'RURAL'): (40,  60),
    ('tertiary',   'URBAN'): (20,  40),
    ('residential','URBAN'): (20,  30),
}
# Peri-urban gets midpoint
PERI_ADJUSTMENT = 0.85   # 15% reduction on upper bound for peri-urban

FALLBACK_SPEED = (50, 70)


def _sf(x):
    try:
        v = float(x)
        return v if not np.isnan(v) else None
    except (TypeError, ValueError):
        return None


def urban_bin(row):
    """Classify urban type from UrbanPC (continuous) or LandUse (string)."""
    urban_pc = _sf(row.get('UrbanPC'))
    if urban_pc is not None:
        if urban_pc >= 0.70:
            return 'URBAN'
        elif urban_pc >= 0.20:
            return 'PERI'
        return 'RURAL'
    lu = str(row.get('LandUse', '')).upper()
    return lu if lu in ('URBAN', 'RURAL') else 'RURAL'


def get_eis(row):
    """Return (eis_lower, eis_upper) for a road segment."""
    rc = str(row.get('RoadClass', '')).lower().strip()
    u_type = urban_bin(row)

    # Try exact match
    key = (rc, u_type if u_type != 'PERI' else 'RURAL')
    eis = ENVIRONMENT_SPEED_TABLE.get(key, FALLBACK_SPEED)

    # Peri-urban: reduce upper bound slightly
    if u_type == 'PERI':
        eis = (eis[0], int(eis[1] * PERI_ADJUSTMENT))

    return eis


def compute_t2_score(row):
    """
    T2 considers two sub-signals:
    (a) Does the posted limit fit within the EIS range?
    (b) Does V85 fit within the EIS range?
    The V85 component adds penalty when traffic exceeds what the environment
    physically supports, even if the limit appears reasonable.
    """
    posted = _sf(row.get('SpeedLimit'))
    v85 = _sf(row.get('F85thPercentileSpeed'))
    eis = get_eis(row)
    eis_lower, eis_upper = eis

    penalties = []

    # Sub-signal (a): Posted limit vs EIS
    if posted and posted > 0:
        if posted <= eis_upper:
            penalties.append(0.0)
        else:
            gap = posted - eis_upper
            penalties.append(min(1.0, gap / eis_upper))
    else:
        penalties.append(0.25)  # Unknown limit = mild concern

    # Sub-signal (b): V85 vs EIS (weighted less heavily)
    if v85 and v85 > 0:
        if v85 <= eis_upper:
            penalties.append(0.0)
        else:
            gap = v85 - eis_upper
            penalties.append(min(1.0, gap / eis_upper) * 0.6)  # 60% weight
    # If no V85 data, skip this sub-signal

    penalty = sum(penalties) / len(penalties) if penalties else 0.25
    return round(max(0.0, 100 * (1 - min(1.0, penalty))), 2)


def run_tier2(gdf, mapillary_token=None, use_urban_pc=False):
    gdf = gdf.copy()
    gdf['t2_eis_range'] = gdf.apply(
        lambda r: f"{get_eis(r)[0]}-{get_eis(r)[1]}", axis=1)
    gdf['t2_score'] = gdf.apply(compute_t2_score, axis=1)
    gdf['t2_source'] = 'network_proxy'
    print(f"  Tier 2 complete. Mean T2={gdf['t2_score'].mean():.1f}, "
          f"CV used: 0.0%, Network proxy: 100.0%")
    return gdf
