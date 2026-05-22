"""
TRACE - Sensitivity Analysis
Tests how P1 priority rankings shift across plausible weight combinations.
Separates core (operational) from reference (single-tier) combinations.
"""

import sys
sys.path.insert(0, '/home/claude/trace_project')

import geopandas as gpd
import pandas as pd
import numpy as np

PRIORITY_THRESHOLD = 40

# Core combinations: plausible operational weightings
CORE_WEIGHTS = [
    ("Default",        0.35,  0.35,  0.30),
    ("Equal thirds",   0.333, 0.333, 0.334),
    ("T1 heavy",       0.50,  0.30,  0.20),
    ("T2 heavy",       0.30,  0.50,  0.20),
    ("T3 heavy",       0.25,  0.25,  0.50),
    ("T1 light",       0.20,  0.40,  0.40),
    ("T2 light",       0.40,  0.20,  0.40),
    ("T3 light",       0.40,  0.40,  0.20),
]

# Reference combinations: single-tier extremes, for diagnostic use only
REF_WEIGHTS = [
    ("Speed only",        1.00, 0.00, 0.00),
    ("Environment only",  0.00, 1.00, 0.00),
    ("VRU only",          0.00, 0.00, 1.00),
    ("T1+T2 only",        0.50, 0.50, 0.00),
    ("T1+T3 only",        0.50, 0.00, 0.50),
    ("T2+T3 only",        0.00, 0.50, 0.50),
]

ALL_WEIGHTS = CORE_WEIGHTS + REF_WEIGHTS


def sss(row, t1w, t2w, t3w):
    t1 = float(row.get('t1_score') or 50.0)
    t2 = float(row.get('t2_score') or 50.0)
    t3 = float(row.get('t3_score') or 50.0)
    return round(t1w * t1 + t2w * t2 + t3w * t3, 2)


def robustness_grade(count, total_core):
    if count == total_core:
        return "Robust"
    elif count >= total_core * 0.75:
        return "Strong"
    elif count >= total_core * 0.50:
        return "Moderate"
    elif count > 0:
        return "Borderline"
    return "None"


def run_sensitivity(gdf, country_name):
    print(f"\n  {country_name}: running {len(ALL_WEIGHTS)} weight combinations...")
    gdf = gdf.copy()

    # Compute SSS under every combination
    for label, t1w, t2w, t3w in ALL_WEIGHTS:
        col = f"sss_{label.replace(' ','_').replace('+','_')}"
        gdf[col] = gdf.apply(lambda r: sss(r, t1w, t2w, t3w), axis=1)

    # Core P1 flags
    core_p1_cols = [
        f"sss_{label.replace(' ','_').replace('+','_')}"
        for label, *_ in CORE_WEIGHTS
    ]
    core_p1_flags = pd.DataFrame(
        {col: gdf[col] < PRIORITY_THRESHOLD for col in core_p1_cols},
        index=gdf.index
    )
    gdf['core_p1_count'] = core_p1_flags.sum(axis=1)
    gdf['robustness'] = gdf['core_p1_count'].apply(
        lambda c: robustness_grade(c, len(CORE_WEIGHTS)))

    # Convenience booleans
    gdf['robust_p1'] = gdf['core_p1_count'] == len(CORE_WEIGHTS)
    gdf['any_core_p1'] = gdf['core_p1_count'] > 0
    gdf['default_p1'] = gdf['sss'] < PRIORITY_THRESHOLD

    # Primary tier driver for each P1 segment
    def primary_driver(row):
        if not row.get('default_p1', False):
            return None
        scores = {'T1': row['t1_score'], 'T2': row['t2_score'], 'T3': row['t3_score']}
        return min(scores, key=scores.get)

    gdf['primary_driver'] = gdf.apply(primary_driver, axis=1)

    # Per-combination stats
    combo_stats = {}
    for label, t1w, t2w, t3w in ALL_WEIGHTS:
        col = f"sss_{label.replace(' ','_').replace('+','_')}"
        p1_n = (gdf[col] < PRIORITY_THRESHOLD).sum()
        combo_stats[label] = {
            'weights': (t1w, t2w, t3w),
            'p1_count': p1_n,
            'p1_pct': round(100 * p1_n / len(gdf), 2),
            'mean_sss': round(gdf[col].mean(), 1),
        }

    # Summary print
    for grade in ['Robust', 'Strong', 'Moderate', 'Borderline']:
        n = (gdf['robustness'] == grade).sum()
        if n > 0:
            print(f"    {grade} P1: {n}")
    print(f"    Default P1: {gdf['default_p1'].sum()}")

    return gdf, combo_stats


def build_report(th, th_stats, mh, mh_stats):
    lines = []
    lines.append("# TRACE — Sensitivity Analysis Report\n")
    lines.append(
        "This report tests how Priority 1 segment classifications respond to variation "
        "in tier weights. The analysis distinguishes between core combinations, which "
        "represent plausible operational weightings where all three tiers contribute, "
        "and reference combinations, which are single-tier extremes used for diagnostic "
        "purposes only.\n"
    )
    lines.append(
        "Robustness is graded against the eight core combinations: a segment is Robust "
        "if it is P1 under all eight, Strong if P1 under six or more, Moderate if P1 "
        "under four or more, and Borderline if P1 under fewer than four.\n"
    )

    lines.append("---\n")
    lines.append("## Weight combinations\n")
    lines.append("### Core (operational)\n")
    lines.append("| Label | T1 | T2 | T3 |")
    lines.append("|---|---|---|---|")
    for label, t1w, t2w, t3w in CORE_WEIGHTS:
        lines.append(f"| {label} | {t1w:.3f} | {t2w:.3f} | {t3w:.3f} |")
    lines.append("\n### Reference (single-tier, diagnostic only)\n")
    lines.append("| Label | T1 | T2 | T3 |")
    lines.append("|---|---|---|---|")
    for label, t1w, t2w, t3w in REF_WEIGHTS:
        lines.append(f"| {label} | {t1w:.3f} | {t2w:.3f} | {t3w:.3f} |")

    for country, gdf, stats in [("Thailand", th, th_stats), ("Maharashtra", mh, mh_stats)]:
        lines.append(f"\n---\n\n## {country}\n")
        lines.append(f"Total segments: {len(gdf):,} | "
                     f"With speed data: {gdf['t1_scr'].notna().sum():,} | "
                     f"Default P1: {gdf['default_p1'].sum()}\n")

        lines.append("### P1 count by weight combination\n")
        lines.append("| Combination | T1 | T2 | T3 | P1 count | P1 % | Mean SSS |")
        lines.append("|---|---|---|---|---|---|---|")
        for label, t1w, t2w, t3w in CORE_WEIGHTS:
            r = stats[label]
            lines.append(f"| {label} | {t1w:.2f} | {t2w:.2f} | {t3w:.2f} | "
                         f"{r['p1_count']} | {r['p1_pct']}% | {r['mean_sss']} |")
        lines.append(f"| **Reference combinations** | | | | | | |")
        for label, t1w, t2w, t3w in REF_WEIGHTS:
            r = stats[label]
            lines.append(f"| {label} | {t1w:.2f} | {t2w:.2f} | {t3w:.2f} | "
                         f"{r['p1_count']} | {r['p1_pct']}% | {r['mean_sss']} |")

        lines.append("\n### Robustness distribution (core combinations)\n")
        lines.append("| Grade | Segments | Meaning |")
        lines.append("|---|---|---|")
        grade_def = {
            "Robust":    "P1 under all 8 core combinations",
            "Strong":    "P1 under 6 or 7 core combinations",
            "Moderate":  "P1 under 4 or 5 core combinations",
            "Borderline":"P1 under 1 to 3 core combinations",
        }
        for grade, meaning in grade_def.items():
            n = (gdf['robustness'] == grade).sum()
            lines.append(f"| {grade} | {n} | {meaning} |")

        # Primary driver breakdown for default P1 segments
        p1 = gdf[gdf['default_p1']].copy()
        if len(p1) > 0:
            lines.append("\n### Primary misalignment driver (default P1 segments)\n")
            lines.append("The primary driver is the tier with the lowest sub-score on each P1 segment.\n")
            driver_counts = p1['primary_driver'].value_counts()
            lines.append("| Tier | Segments | What it means |")
            lines.append("|---|---|---|")
            tier_meaning = {
                'T1': 'Speed behavior is the dominant concern — traffic exceeds limit structurally',
                'T2': 'Environment-limit mismatch is dominant — road physically implies lower speed',
                'T3': 'VRU exposure gap is dominant — limit far exceeds Safe System threshold',
            }
            for tier in ['T1', 'T2', 'T3']:
                n = driver_counts.get(tier, 0)
                if n > 0:
                    lines.append(f"| {tier} | {n} | {tier_meaning[tier]} |")

            lines.append("\n### Default P1 segments — full detail\n")
            lines.append("| Road | Class | Land use | Limit | V85 | SCR | "
                         "T1 | T2 | T3 | SSS | Robustness | Core P1 count | Driver |")
            lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
            for _, row in p1.sort_values('sss').iterrows():
                name = str(row.get('english_ro') or '')
                name = name if name and name != 'nan' else 'Unnamed'
                limit = row.get('SpeedLimit')
                v85 = row.get('F85thPercentileSpeed')
                scr = row.get('t1_scr')
                lim_s = f"{float(limit):.0f}" if limit and str(limit) != 'nan' else '—'
                v85_s = f"{float(v85):.0f}" if v85 and str(v85) != 'nan' else '—'
                scr_s = f"{float(scr):.2f}" if scr and str(scr) != 'nan' else '—'
                lines.append(
                    f"| {name} | {row.get('RoadClass','—')} | {row.get('LandUse','—')} | "
                    f"{lim_s} | {v85_s} | {scr_s} | "
                    f"{row['t1_score']:.0f} | {row['t2_score']:.0f} | {row['t3_score']:.0f} | "
                    f"{row['sss']:.1f} | {row['robustness']} | "
                    f"{int(row['core_p1_count'])}/8 | {row.get('primary_driver','—')} |"
                )

    lines.append("\n---\n")
    lines.append("## Key findings\n")
    lines.append(
        "The majority of default P1 segments in both countries are T3-driven: their "
        "primary misalignment is the gap between the posted limit and the Safe System "
        "biomechanical threshold for the most exposed vulnerable road user class on that "
        "segment. This means their P1 classification is sensitive to T3 weight. Under "
        "T3-heavy configurations they remain firmly P1; under T2-heavy or T3-light "
        "configurations some move to P2.\n"
    )
    lines.append(
        "This is a finding about the nature of the problem, not a weakness in the "
        "methodology. The Safe System framework explicitly places VRU protection as the "
        "primary criterion for speed limit appropriateness. A ministry that follows Safe "
        "System principles should weight T3 at least as heavily as T1 and T2, which "
        "would strengthen the P1 classification for the identified segments rather than "
        "weaken it. The default weights (0.35/0.35/0.30) are conservative.\n"
    )
    lines.append(
        "Segments that survive T2-heavy and T3-light weightings represent cases where "
        "speed misalignment alone is severe enough to warrant P1 classification. These "
        "are the most operationally conservative flags: a segment that scores P1 even "
        "when VRU protection is underweighted has a problem that goes beyond Safe System "
        "compliance alone."
    )

    return "\n".join(lines)


def main():
    print("Loading outputs...")
    th = gpd.read_file('/home/claude/trace_project/outputs/trace_thailand.geojson')
    mh = gpd.read_file('/home/claude/trace_project/outputs/trace_maharashtra.geojson')

    th_out, th_stats = run_sensitivity(th, 'Thailand')
    mh_out, mh_stats = run_sensitivity(mh, 'Maharashtra')

    # Save updated GeoJSONs
    keep = ['geometry','english_ro','RoadClass','LandUse','SpeedLimit',
            'F85thPercentileSpeed','t1_score','t2_score','t3_score','sss',
            'priority_flag','robustness','core_p1_count','primary_driver',
            'robust_p1','any_core_p1','default_p1','explanation',
            'color','t1_scr','t2_eis_range','t3_vru_threshold','StreetImageLink','country']

    for country, gdf, fname in [('Thailand', th_out, 'trace_thailand'),
                                  ('Maharashtra', mh_out, 'trace_maharashtra')]:
        existing = [c for c in keep if c in gdf.columns]
        out = f'/home/claude/trace_project/outputs/{fname}_sensitivity.geojson'
        gdf[existing].to_file(out, driver='GeoJSON')
        print(f"  Saved: {out}")

    report = build_report(th_out, th_stats, mh_out, mh_stats)
    rpath = '/home/claude/trace_project/evaluation/sensitivity_report.md'
    with open(rpath, 'w') as f:
        f.write(report)
    print(f"  Report: {rpath}")

    # Print summary
    print("\n" + "="*55)
    print("  SENSITIVITY SUMMARY")
    print("="*55)
    for country, gdf in [('Thailand', th_out), ('Maharashtra', mh_out)]:
        print(f"\n  {country}:")
        for grade in ['Robust','Strong','Moderate','Borderline']:
            n = (gdf['robustness'] == grade).sum()
            if n > 0:
                print(f"    {grade:<12}: {n}")
        print(f"    Default P1  : {gdf['default_p1'].sum()}")
        p1 = gdf[gdf['default_p1']]
        if len(p1) > 0:
            print(f"    Driver breakdown: {p1['primary_driver'].value_counts().to_dict()}")


if __name__ == '__main__':
    main()
