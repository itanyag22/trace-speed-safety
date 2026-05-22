# TRACE Methodology

**Tiered Road Alignment and Composite Evaluation**

---

## The core question

Speed limits across much of Asia and the Pacific were set under engineering conventions that used observed traffic speeds as the primary criterion. The most common method, setting the limit at or near the 85th percentile of free-flow speeds, has a structural flaw: it normalizes whatever speeds drivers have already adopted rather than asking what speed the road should support given the mix of users on it. The result, in many corridors, is limits that reflect historical driving behavior on roads that were designed primarily for motor vehicles and have since been absorbed into denser, mixed-traffic environments.

TRACE is built around a different question: not whether drivers comply with the posted limit, but whether the posted limit is set at the right level given the road's physical context, its operating speed profile, and the vulnerability of the people who use it.

---

## Why three tiers

A single evidence stream cannot answer this question reliably.

Operating speed data (V85) tells you what traffic does but not why. A road where V85 exceeds the posted limit by 30% might have a limit that is unreasonably low for the road type, or it might have a limit that is correct but a road design that invites dangerous speeds. Without additional context, these two situations produce the same compliance ratio but call for different interventions.

Road environment data tells you what the physical setting implies about safe speed, but without speed data you cannot tell whether the limit is consistent with actual behavior or merely with the infrastructure.

Safe System thresholds tell you what the human body can survive in an impact at a given speed, and for which user types. But applied uniformly to all roads, they would flag every urban road in Asia, which is not a useful prioritization.

The three tiers are designed to triangulate. A segment that scores poorly on all three is one where traffic behavior, physical environment, and biomechanical risk are all pointing in the same direction: the limit is too high for this road and these users. A segment that scores poorly on one tier but not the others warrants a different kind of attention, and the decomposition shows which.

---

## Tier 1: Operating speed alignment

**What it measures**

Tier 1 assesses the relationship between the posted speed limit and the distribution of observed operating speeds. The primary signal is the Speed Compliance Ratio:

```
SCR = V85 / SpeedLimit
```

Where V85 is the 85th percentile operating speed from GPS probe data. A secondary signal is the Speed Variance Index:

```
SVI = (V85 - V50) / SpeedLimit
```

Where V50 is the median operating speed. High variance between the median and 85th percentile, relative to the posted limit, indicates an unstable speed environment where the limit is not producing a coherent speed regime.

**Scoring logic**

SCR at or below 1.0 produces no T1 penalty. A moderate penalty begins at SCR above 1.0 and reaches 50% of the maximum at SCR of 1.15. Above 1.15, the penalty increases more steeply, reaching 100% at SCR of approximately 1.50. The 1.15 threshold is drawn from accepted traffic engineering practice: deviations beyond this level are generally taken to indicate structural misalignment between the limit and the road's design speed, rather than random non-compliance.

SVI contributes 30% of the T1 penalty. High variance is independently concerning because it reflects a speed distribution where a significant share of traffic is moving much faster than the typical driver, which increases the relative speed differential in overtaking and following situations.

Segments without probe data receive a neutral T1 score of 50.

**What a low T1 score means**

A T1 score below 50 means traffic on this segment is operating consistently above what the posted limit specifies, to a degree that suggests the limit is not functioning as an effective speed constraint. This can happen because the limit was set too low for the road's design speed (in which case the correct intervention may be to revise the limit upward or redesign the road to match a lower limit), or because the road has physical characteristics that encourage high speeds regardless of the posted limit (in which case environmental intervention is warranted in addition to or instead of limit revision).

---

## Tier 2: Road environment alignment

**What it measures**

Tier 2 assesses whether the posted limit, and the actual operating speed, are consistent with what the physical road environment implies about safe speeds. The concept being operationalized is that road environments send speed signals to drivers through geometry, adjacency, and infrastructure: a narrow road with market frontages and visible pedestrians signals a low-speed environment regardless of what the sign says. When the posted limit is inconsistent with that signal, the road is structurally set up to produce unsafe interactions.

**Environment-implied speed ranges**

In the current implementation, environment-implied speeds are derived from road network attributes: functional class (motorway, trunk, primary, secondary, tertiary, residential), land use classification (urban, peri-urban, rural), and where available the UrbanPC field (a continuous 0-1 urban density indicator from the Maharashtra dataset). These are mapped to safe speed ranges calibrated for the Asian road context, which are lower than equivalent European or North American ranges due to the higher share of non-motorized and two-wheeled traffic in mixed corridors.

| Road class | Rural | Urban |
|---|---|---|
| Motorway | 90–110 km/h | 70–90 km/h |
| Trunk | 70–90 km/h | 50–70 km/h |
| Primary | 60–80 km/h | 40–60 km/h |
| Secondary | 50–70 km/h | 30–50 km/h |
| Tertiary | 40–60 km/h | 20–40 km/h |
| Residential | — | 20–30 km/h |

Peri-urban segments receive a 15% reduction on the upper bound of the rural equivalent.

T2 evaluates two sub-signals: whether the posted limit exceeds the environment-implied upper bound, and whether V85 exceeds the environment-implied upper bound. The V85 sub-signal is weighted at 60% of its raw penalty to reflect the fact that operating speeds are influenced by driver behavior as well as environment. The two sub-signals are averaged.

**CV extension**

The methodology is designed so that Tier 2 can be upgraded from network-attribute proxies to computer vision analysis of Mapillary street imagery. The `tiers/tier2_environment.py` module contains the integration skeleton. When a Mapillary API token is available, the pipeline samples images for each segment using the coordinates in the `StreetImageLink` field, classifies them using a CLIP-based zero-shot model across five environment features (pedestrian infrastructure presence, crossing infrastructure, land use adjacency, road width class, roadside activity), and converts the resulting feature profile to an environment-implied speed range. Segments scored with CV analysis are flagged as `t2_source = 'cv'` in the output. Segments scored with network proxies are flagged as `t2_source = 'network_proxy'`.

**What a low T2 score means**

A T2 score below 50 means the posted limit, or the actual traffic speed, is substantially higher than what the road environment implies is safe for mixed-traffic interaction. The most diagnostic cases are urban secondary roads where the environment-implied speed is 30 to 50 km/h and the posted limit is 60 to 80 km/h. These segments typically have market frontages, residential adjacency, or crossing activity that is visually inconsistent with the speed the sign specifies.

---

## Tier 3: VRU protection threshold

**The Safe System basis**

The Safe System approach to road safety starts from a physiological fact: the human body can only absorb a limited impact force before catastrophic injury becomes likely. For pedestrians, the threshold above which fatality becomes probable in a frontal vehicle impact is approximately 30 km/h. For cyclists, it is approximately 40 km/h. For powered two-wheeler users, the relevant threshold for severe injury is approximately 50 km/h, though fatality risk rises at lower speeds due to the absence of crash protection.

These thresholds are not design targets in the sense that roads should always be limited to these speeds. They are injury thresholds in the sense that, wherever vulnerable road users are present and exposed to vehicle traffic, speed limits above these thresholds mean the system is not tolerant of human error. A pedestrian who steps into a 60 km/h traffic stream is in a situation where a driver error of one second is likely to be fatal.

**VRU exposure estimation**

Tier 3 applies these thresholds weighted by an estimated VRU exposure score for each segment. Exposure is estimated from available proxy variables:

*Pedestrian exposure* is estimated from population density (where available), land use classification, and proximity to activity generators including schools and markets. It is higher on urban and secondary roads and lower on motorways and rural trunk roads.

*Cyclist exposure* is estimated from intersection density (high intersection density correlates with cycling activity in urban areas) and urban classification.

*PTW exposure* is set at elevated baseline levels for both datasets, reflecting the high market penetration of powered two-wheelers in Thailand and Maharashtra. The Maharashtra baseline is adjusted upward further, based on available survey data showing significantly higher PTW use on rural roads in the region.

**The helmet SPI modifier**

The Tier 3 penalty is multiplied by a helmet risk factor derived from the helmet-wearing Safety Performance Index (SPI) in the provided dataset. Maharashtra's overall helmet SPI is 0.209, meaning fewer than one in four riders wears a helmet. For rural passengers in Maharashtra, the SPI is 0.022. At speeds above 30 km/h, an unhelmeted PTW rider faces dramatically higher injury severity than a helmeted one. The helmet modifier increases the T3 penalty in low-helmet-compliance environments to reflect this additional systemic risk.

| Country | Overall helmet SPI | Modifier (urban) | Modifier (rural) |
|---|---|---|---|
| Thailand | 0.778 | 1.05x | 1.15x |
| Maharashtra | 0.209 | 1.30x | 1.50x |

**Threshold application**

For each segment, the applicable Safe System threshold is determined by which user classes have estimated exposure above 0.20 (on a 0-1 scale). The most protective threshold among active user classes is applied. The T3 penalty is the gap between the posted limit and this threshold, scaled by the maximum exposure level across user classes, multiplied by the helmet modifier.

**What a low T3 score means**

A T3 score below 50 means the posted limit substantially exceeds the Safe System threshold for the most exposed vulnerable user class on that segment. On urban primary roads posted at 80 km/h with high pedestrian exposure, the T3 score will be very low regardless of what T1 and T2 show, because 80 km/h is 2.7 times the pedestrian injury threshold. This is by design: the Safe System framework treats tolerance for human error as a system requirement, not a driver responsibility.

---

## Score composition

The composite Speed Safety Score is:

```
SSS = 0.35 * T1 + 0.35 * T2 + 0.30 * T3
```

Weights are equal between T1 and T2 because both address the appropriateness of the limit from different directions: one from observed behavior, one from physical environment. T3 carries slightly lower weight because VRU exposure is estimated from proxies rather than observed counts, which introduces more uncertainty into that tier.

All weights are configurable in `config/config.yaml` and should be reviewed by in-country road safety experts before operational use. The sensitivity analysis output documents how much the priority ranking changes across plausible weight ranges.

**Priority classification**

| SSS range | Flag | Interpretation |
|---|---|---|
| 0–39 | P1: Immediate Review | Three-tier misalignment is severe. Recommended for immediate speed limit review or road safety audit. |
| 40–59 | P2: Secondary Review | Meaningful misalignment on at least one tier. Recommended for inclusion in the next scheduled review cycle. |
| 60–79 | P3: Monitor | Some misalignment present but not at priority intervention level. Flag for monitoring. |
| 80–100 | Acceptable | No significant misalignment detected across the three tiers. |

---

## Data confidence flags

Each scored segment carries a `data_confidence` indicator based on data availability:

- **High**: Probe data (V85, V50) present, SpeedLimit present, StreetImageLink present
- **Medium**: At least probe data or SpeedLimit present
- **Low**: No probe data and no SpeedLimit; T1 and parts of T3 are based on defaults

Segments with Low confidence should not be used for individual-segment prioritization decisions. They can be used for network-level coverage analysis and to identify where data collection should be prioritized.

---

## Scalability design

The framework is designed to degrade gracefully in data-poor environments rather than fail.

If Mapillary imagery is unavailable, Tier 2 uses network attribute proxies. If contextual layers are absent, Tier 3 uses road class and land use defaults for VRU exposure. If probe data is missing for some segments, those segments receive neutral T1 scores and are scored on T2 and T3 only. If road class or land use classification is incomplete (as it is for approximately 71% of Maharashtra segments), the fallback environment profile is used and flagged in the output.

This means the same pipeline can be applied to a data-rich national dataset and a data-sparse district dataset, producing outputs at different confidence levels but using the same methodology. Cross-country score comparison requires recalibration of the weights and thresholds to account for different data environments, which is why these parameters are externalized to a configuration file rather than hardcoded.

---

## Evaluation approach

Three evaluation tracks are used in the absence of crash ground truth:

**Internal consistency** checks that the distribution of scores across road type hierarchies is directionally correct (motorways should score differently from residential roads), that the priority flag distribution is not degenerate, and that the plain-language explanations accurately describe the raw data driving the score.

**Sensitivity analysis** reruns the composite scoring across weight combinations where each tier weight is varied by ±0.10 while the others are adjusted proportionally. Segments that remain P1 across all tested configurations are labeled as robust priority flags. Segments that move between P1 and P2 depending on weights are labeled as borderline and noted in the output.

**Spot-check validation** manually reviews a stratified sample of 50 segments (10 P1, 20 P2, 10 P3, 10 Acceptable) against the raw speed and network data to confirm the score direction is correct and the explanation is accurate. Results are documented in `evaluation/spot_check_report.md`.

---

## Calibration guidance for new countries

When applying TRACE to a new country dataset:

1. Review the environment-implied speed table in `tiers/tier2_environment.py` against local road design standards. The defaults are calibrated for mixed-traffic Asian road environments and may not be appropriate for countries with stricter separation between motor vehicle and non-motorized infrastructure.

2. Review the VRU exposure baselines in `tiers/tier3_vru.py`. PTW penetration varies widely across the region. Countries with low PTW use (Australia, New Zealand, Japan in urban areas) should reduce the PTW exposure baseline.

3. Set the helmet SPI values in `config/config.yaml` to reflect country-level survey data. The helmet modifier has a material effect on T3 scores in low-compliance environments.

4. Run the sensitivity analysis and review the borderline-flag proportion. A proportion above 30% suggests the default weights may not be well-calibrated for the data environment.

5. Where crash data is available, validate the priority ranking against crash density by segment. Segments with high crash density that do not appear in P1 or P2 indicate a calibration gap.
