"""
TRACE - Tier 3: VRU Protection Threshold
Applies Safe System biomechanical speed thresholds weighted by VRU exposure.
Incorporates helmet SPI as a risk multiplier for PTW users.
"""

import pandas as pd
import numpy as np

SAFE_SYSTEM = {
    'pedestrian': 30,
    'cyclist':    40,
    'ptw':        50,
}


def compute_vru_exposure(row, country='Thailand'):
    """
    Estimate VRU exposure (0–1) per user class from available proxy variables.
    Returns dict: {pedestrian: float, cyclist: float, ptw: float}
    """
    # Urban factor
    urban_pc = row.get('UrbanPC')
    if urban_pc is not None and not pd.isna(urban_pc):
        urban_factor = float(urban_pc)
    else:
        land_use = row.get('LandUse', '')
        urban_factor = 0.65 if str(land_use).upper() == 'URBAN' else 0.25

    road_class = str(row.get('RoadClass', '')).lower()

    # Pedestrian exposure: higher on urban roads, especially lower-class
    ped_base = {
        'motorway': 0.05, 'trunk': 0.15, 'primary': 0.30,
        'secondary': 0.45, 'tertiary': 0.55, 'residential': 0.75,
    }.get(road_class, 0.30)
    ped_exp = min(1.0, ped_base * (0.5 + urban_factor))

    # Cyclist exposure: moderate, peaks on secondary/tertiary urban
    cyc_base = {
        'motorway': 0.02, 'trunk': 0.10, 'primary': 0.20,
        'secondary': 0.35, 'tertiary': 0.45, 'residential': 0.50,
    }.get(road_class, 0.25)
    cyc_exp = min(1.0, cyc_base * (0.5 + urban_factor * 0.8))

    # PTW exposure: very high across Asia, especially rural secondary
    # Maharashtra PTW exposure much higher than Thailand
    ptw_multiplier = 1.4 if country == 'Maharashtra' else 1.0
    ptw_base = {
        'motorway': 0.20, 'trunk': 0.50, 'primary': 0.55,
        'secondary': 0.60, 'tertiary': 0.60, 'residential': 0.50,
    }.get(road_class, 0.50)
    ptw_exp = min(1.0, ptw_base * ptw_multiplier)

    return {'pedestrian': ped_exp, 'cyclist': cyc_exp, 'ptw': ptw_exp}


def compute_vru_threshold(exposures, exposure_cutoff=0.20):
    """Determine applicable Safe System threshold from active exposures."""
    applicable = [
        SAFE_SYSTEM[user]
        for user, exp in exposures.items()
        if exp >= exposure_cutoff
    ]
    return min(applicable) if applicable else 60


def helmet_risk_multiplier(country, land_use):
    """
    Boost T3 penalty in low-helmet environments.
    Maharashtra rural passengers: 2.2% helmet use - severe multiplier.
    """
    base = {
        'Thailand': {'URBAN': 1.05, 'RURAL': 1.15, None: 1.10},
        'Maharashtra': {'URBAN': 1.30, 'RURAL': 1.50, None: 1.40},
    }
    lu = str(land_use).upper() if land_use and not pd.isna(land_use) else None
    country_map = base.get(country, base['Thailand'])
    return country_map.get(lu, country_map.get(None, 1.0))


def compute_t3_score(row, country='Thailand'):
    """
    T3 score (0–100): does the posted limit protect VRUs at Safe System thresholds?
    """
    def _sf(x):
        try: return float(x)
        except: return float('nan')
    posted = _sf(row.get('SpeedLimit'))
    import math
    if posted is None or math.isnan(posted) or posted <= 0:
        return 50.0  # Neutral when no limit

    exposures = compute_vru_exposure(row, country)
    vru_threshold = compute_vru_threshold(exposures)
    max_exposure = max(exposures.values())

    gap = max(0.0, posted - vru_threshold)
    if gap == 0:
        return 100.0

    # Base penalty: gap as fraction of threshold, scaled by exposure
    base_penalty = min(1.0, (gap / vru_threshold) * max_exposure)

    # Apply helmet risk multiplier
    multiplier = helmet_risk_multiplier(country, row.get('LandUse'))
    adjusted_penalty = min(1.0, base_penalty * multiplier)

    score = round(100 * (1 - adjusted_penalty), 2)
    return max(0.0, score)


def run_tier3(gdf, country='Thailand'):
    gdf = gdf.copy()
    gdf['t3_score'] = gdf.apply(lambda r: compute_t3_score(r, country), axis=1)

    # Store VRU threshold for output readability
    def get_threshold(row):
        exp = compute_vru_exposure(row, country)
        return compute_vru_threshold(exp)

    gdf['t3_vru_threshold'] = gdf.apply(get_threshold, axis=1)
    print(f"  Tier 3 complete. Mean T3={gdf['t3_score'].mean():.1f}, "
          f"Country: {country}")
    return gdf
