# TRACE (Methodology)

**Tiered Road Alignment and Composite Evaluation**

---

## The core question

Speed limits across much of Asia and the Pacific Region were set under engineering conventions that used observed traffic speeds as the primary criterion. The most common method was to survey free-flow speeds and set the limit at or near the 85th percentile. This approach has a structural flaw, as it normalizes whatever speeds drivers have already adopted on a road rather than asking what speed that road should support given the mix of people using it. The result, in many corridors, is limits that reflect how fast vehicles moved decades ago on roads that were designed primarily for motor vehicles and have since been absorbed into denser, more complex environments shared with pedestrians, cyclists, and motorcycle riders.

TRACE is built around a different question. Rather than asking whether drivers are complying with the posted limit, it asks whether the posted limit is set at the right level for the road it governs, the people who travel on it, and the people most at risk when something goes wrong.

---

## Why three tiers?

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

Tier 2 evaluates two things in combination. The first is whether the posted limit exceeds what the road environment implies is safe. The second is whether V85, the speed at which most traffic moves, also exceeds that implied ceiling. The V85 signal carries slightly less weight than the limit signal because operating speeds reflect driver behavior as much as road design, and the framework is primarily concerned with the limit rather than the driver. The two signals are averaged into the final T2 score.

**CV extension**

The methodology is designed so that Tier 2 can be upgraded from network-attribute proxies to computer vision analysis of Mapillary street imagery. The `tiers/tier2_environment.py` module contains the integration skeleton. When a Mapillary API token is available, the pipeline samples images for each segment using the coordinates in the `StreetImageLink` field, classifies them using a CLIP-based zero-shot model across five environment features (pedestrian infrastructure presence, crossing infrastructure, land use adjacency, road width class, roadside activity), and converts the resulting feature profile to an environment-implied speed range. Segments scored with CV analysis are flagged as `t2_source = 'cv'` in the output. Segments scored with network proxies are flagged as `t2_source = 'network_proxy'`.

**What a low T2 score means**

A T2 score below 50 means the posted limit, or the actual traffic speed, is substantially higher than what the road environment implies is safe for mixed-traffic interaction. The most diagnostic cases are urban secondary roads where the environment-implied speed is 30 to 50 km/h and the posted limit is 60 to 80 km/h. These segments typically have market frontages, residential adjacency, or crossing activity that is visually inconsistent with the speed the sign specifies.

---

## Tier 3: VRU protection threshold

**The Safe System basis**

The Safe System approach to road safety starts from a basic physical fact that the human body can only absorb so much force in a collision before the injuries become fatal. For pedestrians, that threshold is around 30 km/h. For cyclists it is around 40 km/h. And for powered two-wheeler riders the threshold for severe injury sits around 50 km/h, though the risk of death rises at lower speeds because motorcycles and scooters offer no structural protection in a crash.

These thresholds are not design targets in the sense that roads should always be limited to these speeds. They are injury thresholds in the sense that, wherever vulnerable road users are present and exposed to vehicle traffic, speed limits above these thresholds mean the system is not tolerant of human error. A pedestrian who steps into a 60 km/h traffic stream is in a situation where a driver error of one second is likely to be fatal.

**VRU exposure estimation**

Tier 3 applies these thresholds weighted by an estimated VRU exposure score for each segment. Exposure is estimated from available proxy variables:

- *Pedestrian exposure* is estimated from population density (where available), land use classification, and proximity to activity generators including schools and markets. It is higher on urban and secondary roads and lower on motorways and rural trunk roads.

- *Cyclist exposure* is estimated from intersection density (high intersection density correlates with cycling activity in urban areas) and urban classification.

- *PTW exposure* is set at elevated baseline levels for both datasets, reflecting the high market penetration of powered two-wheelers in Thailand and Maharashtra. The Maharashtra baseline is adjusted upward further, based on available survey data showing significantly higher PTW use on rural roads in the region.

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

If Mapillary imagery is unavailable, Tier 2 uses network attribute proxies instead. If contextual layers are absent, Tier 3 uses road class and land use defaults for VRU exposure. If probe data is missing for some segments, those segments receive neutral T1 scores and are scored on T2 and T3 only. If road class or land use classification is incomplete (as it is for approximately 71% of Maharashtra segments), the fallback environment profile is used and flagged in the output.

This means the same pipeline can be applied to a data-rich national dataset and a data-sparse district dataset, producing outputs at different confidence levels but using the same methodology. Cross-country score comparison requires recalibration of the weights and thresholds to account for different data environments, which is why these parameters are externalized to a configuration file rather than hardcoded.

---

## Evaluation approach

Three evaluation tracks are used in the absence of crash ground truth:

- **Internal consistency** checks that the distribution of scores across road type hierarchies is directionally correct (i.e., motorways should score differently from residential roads), that the priority flag distribution is not degenerate, and that the plain-language explanations accurately describe the raw data driving the score.

- **Sensitivity analysis** reruns the composite scoring across weight combinations where each tier weight is varied by ±0.10 while the others are adjusted proportionally. Segments that remain P1 across all tested configurations are labeled as robust priority flags. Segments that move between P1 and P2 depending on weights are labeled as borderline and noted in the output.

- **Spot-check validation** manually reviews a stratified sample of 50 segments (10 P1, 20 P2, 10 P3, 10 Acceptable) against the raw speed and network data to confirm the score direction is correct and the explanation is accurate. Results are documented in `evaluation/spot_check_report.md`.

---

## Calibration guidance for new countries

When applying TRACE to a new country, work through the following steps before treating any outputs as ready for policy use.

> [!IMPORTANT]
> Complete all five steps in order. Skipping calibration before sharing outputs with government counterparts risks misidentifying priority segments.

1. **Check the environment-implied speed table against local road standards.** The defaults in `tiers/tier2_environment.py` are calibrated for mixed-traffic Asian road environments where motorized and non-motorized users share the same surface. Countries with more developed pedestrian and cycling infrastructure may need lower implied speed ceilings for urban road classes.

2. **Review powered two-wheeler exposure baselines.** PTW penetration varies significantly across the region. Countries where motorcycle use is low, such as Australia, New Zealand, or Japan in urban areas, should reduce the PTW exposure baseline in `tiers/tier3_vru.py` to avoid overstating VRU risk on roads where riders are rarely present.

3. **Update the helmet compliance values.** The helmet SPI modifier in `config/config.yaml` has a direct effect on Tier 3 scores. Set it to reflect the most recent country-level survey data. In low-compliance environments the modifier amplifies the T3 penalty, which is intentional, but it should be grounded in evidence rather than left at the default.

4. **Run the sensitivity analysis before finalizing outputs.** If more than 30% of segments are classified as borderline, the default weights may not be well suited to the local data environment. Adjust and rerun before sharing results with government counterparts.

> [!TIP]
> Run python `evaluation/sensitivity_analysis.py` after any weight change. The borderline proportion is printed to the console at the end of the run.

5. **Validate against crash records where they exist.** If crash density data is available at the segment level, compare it against the P1 and P2 priority rankings. Segments with high crash density that do not appear in the priority list indicate a calibration gap that needs to be investigated before the outputs are used to inform decisions.
