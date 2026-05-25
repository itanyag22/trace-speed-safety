# TRACE

**Tiered Road Alignment and Composite Evaluation**

Speed limits across much of Asia and the Pacific were set decades ago using engineering methods that treated observed traffic speeds as the standard. They were not designed around what the human body can survive in a collision, and they were not updated when roads that once served mainly motor vehicles became corridors shared with pedestrians, cyclists, and powered two-wheeler riders.

TRACE is an analytical framework that asks whether the posted limit is set at the right level for the road it governs, rather than whether drivers are complying with it.

It does this by evaluating each road segment against three independent evidence streams. The first is how fast traffic actually moves. The second is what the physical road environment implies about safe speed. The third is whether the posted limit protects the most vulnerable users at the injury thresholds defined by Safe System principles. The three produce a composite Speed Safety Score from 0 to 100 for every segment in a network, with a plain-language explanation of what is driving the result and a priority flag that tells a transport official where to act first.

The framework was developed and applied to road network datasets from Thailand and Maharashtra, India, covering approximately 70,000 road segments across both national highway networks and dense urban and peri-urban road environments. The datasets were provided through the AI for Safer Roads Innovation Challenge organized by the Asian Development Bank (ADB), in collaboration with the World Bank Development Impact Group, International Telecommunication Union (ITU), and AI for Good.

---

## What this is

Most speed audit tools are built around compliance by measuring whether drivers are exceeding the posted limit and flagging segments where speeding is frequent. Tools like iRAP assessments, commercial telematics risk scores, and enforcement-oriented analytics all start from the assumption that the limit is correct and the driver is the problem. TRACE treats the limit itself as the thing that needs to be examined, asking whether it was ever set at the right level for the road, its users, and the people most at risk on it.

The framework evaluates each road segment against three independent evidence streams.

Tier 1 assesses whether the 85th percentile operating speed aligns with the posted limit, or whether the gap between them suggests the limit is structurally out of step with how the road is actually used.

Tier 2 assesses whether the physical road environment supports the posted limit, drawing on road network attributes and, where available, street-level imagery analysis.

Tier 3 assesses whether the posted limit is consistent with Safe System biomechanical thresholds given the estimated exposure of pedestrians, cyclists, and powered two-wheeler users on that segment.

Each tier produces a sub-score from 0 to 100. The three are combined into a composite Speed Safety Score. Every segment output includes the three sub-scores, a plain-language explanation of what is driving the result, and a priority flag indicating whether the segment warrants immediate review, secondary review, monitoring, or no action.

---

## Proof-of-concept outputs

The proof-of-concept outputs below illustrate how TRACE generates segment-level Speed Safety Scores when applied to the ADB AI for Safer Roads Innovation Challenge datasets for Thailand and Maharashtra, India. These outputs are intended to show the scoring logic, map interface, and interpretability features of the framework. TRACE is designed to be reusable across other countries or road networks, provided that compatible road network, speed, and contextual datasets are available.

| Country | Segments scored | With speed data | Mean SSS | P1: Immediate Review | P2: Secondary Review |
|---|---|---|---|---|---|
| Thailand | 55,884 | 11,134 | 61.0 | 33 | 45,683 |
| Maharashtra | 14,082 | 3,577 | 64.1 | 1 | 10,190 |

In Thailand, 20.4% of segments with speed data have a Speed Compliance Ratio above 1.15, meaning V85 exceeds the posted limit by more than 15%. In Maharashtra, that figure is 37.2%. The worst Thailand segment scores SSS 31.7, a secondary urban road where V85 runs at 114 km/h on a 66 km/h road, in an environment the model classifies as safe for 30 to 50 km/h.

---

## Interactive maps

The maps below are proof-of-concept visualizations of the Speed Safety Score outputs. Each road segment is color-coded by priority classification. Hovering over a segment shows a tooltip with its score breakdown. Clicking a P1 segment opens a full panel with all three tier scores, the posted limit, the 85th percentile operating speed, and an explanation of the misalignment.

**[Thailand — Speed Safety Score Map](https://itanyag22.github.io/trace-speed-safety/thailand.html)**

**[Maharashtra — Speed Safety Score Map](https://itanyag22.github.io/trace-speed-safety/maharashtra.html)**

### Reading the map

| Color | Priority flag | Score range | What it means |
|---|---|---|---|
| 🔴  Red | P1: Immediate Review | SSS below 40 | Severe misalignment across multiple tiers. Recommended for immediate speed limit review or road safety audit. |
| 🟠  Orange | P2: Secondary Review | SSS 40 to 59 | Meaningful misalignment on at least one tier. Include in the next scheduled review cycle. |
| 🟡 Yellow | P3: Monitor | SSS 60 to 79 | Some misalignment present but not yet at priority intervention level. Flag for monitoring. |
| 🟢 Green | Acceptable | SSS 80 and above | No significant misalignment detected across the three tiers. |

### What the tooltip shows

When you hover over or click any road segment, the following fields appear:

| Field | What it means |
|---|---|
| **Road** | Road name where available |
| **SSS** | Composite Speed Safety Score from 0 to 100. Lower means more misaligned. |
| **T1** | Tier 1 score. Measures how well the 85th percentile operating speed aligns with the posted limit. Low score means traffic moves significantly faster than the limit suggests it should. |
| **T2** | Tier 2 score. Measures whether the physical road environment supports the posted limit. Low score means the road type and land use imply a lower safe speed than what is posted. |
| **T3** | Tier 3 score. Measures whether the posted limit protects vulnerable road users at Safe System injury thresholds. Low score means the limit substantially exceeds the biomechanical tolerance for pedestrians, cyclists, or powered two-wheeler users on that segment. |
| **Posted limit** | The speed limit sign on that road in km/h. |
| **V85** | The speed at or below which 85% of vehicles travel on that segment, from GPS probe data. |

---

## Data inputs

The pipeline expects the following inputs, configured via `config/config.yaml`:

| Input | Format | Required | Description |
|---|---|---|---|
| Road network | GeoPackage (.gpkg) | Yes | Segment geometries with RoadClass, LandUse, SpeedLimit |
| GPS probe data | Attached to network or CSV | Yes | V50, V85, MedianSpeed, PercentOverLimit per segment |
| Contextual layers | GeoPackage or CSV | Optional | Population density, school/market proximity, PTW indicators |
| Street imagery | Mapillary (via StreetImageLink coordinates) | Optional | Used for CV-based Tier 2; network proxy used when absent |

The provided ADB datasets include a `StreetImageLink` field containing endpoint coordinates in the format `lon1,lat1,lon2,lat2`. These can be used to query the Mapillary API for nearby images. See `tiers/tier2_environment.py` for the CV integration skeleton.

---

## Installation

```bash
git clone https://github.com/itanyag22/trace-speed-safety
cd trace-speed-safety
pip install -r requirements.txt
```

**Requirements:**
```
geopandas>=0.14
pandas>=2.0
numpy>=1.24
folium>=0.15
PyYAML>=6.0
openpyxl>=3.1
fiona>=1.9
shapely>=2.0
```

For the CV/Mapillary extension (optional):
```
torch>=2.0
transformers>=4.35
Pillow>=10.0
```

---

## Usage

1. Edit `config/config.yaml` to point to your data files.
2. Run the pipeline:

```bash
python main.py
```

Outputs are written to the directory specified in `config.yaml` under `paths.output_dir`.

---

## Output files

For each country or dataset:

| File | Description |
|---|---|
| `trace_{country}.geojson` | Full scored road network, all fields |
| `TRACE_{Country}_map.html` | Interactive Folium map, click segments for full decomposition |

### GeoJSON schema

Each road segment record contains:

| Field | Type | Description |
|---|---|---|
| `t1_score` | float | Tier 1 operating speed alignment (0–100) |
| `t1_scr` | float | Speed Compliance Ratio (V85 / SpeedLimit) |
| `t2_score` | float | Tier 2 road environment alignment (0–100) |
| `t2_eis_range` | string | Environment-implied speed range in km/h |
| `t2_source` | string | `cv` or `network_proxy` |
| `t3_score` | float | Tier 3 VRU protection alignment (0–100) |
| `t3_vru_threshold` | float | Applied Safe System threshold in km/h |
| `sss` | float | Composite Speed Safety Score (0–100) |
| `priority_flag` | string | P1 / P2 / P3 / Acceptable |
| `explanation` | string | Plain-language description of misalignments |

---

## Configuration

`config/config.yaml` controls all scoring parameters:

```yaml
weights:
  t1: 0.35   # Operating speed alignment
  t2: 0.35   # Road environment alignment
  t3: 0.30   # VRU protection threshold

safe_system_speeds:
  pedestrian: 30   # km/h
  cyclist:    40
  ptw:        50

priority_thresholds:
  immediate: 40    # SSS below this -> P1
  secondary: 60    # SSS below this -> P2
  monitor:   80    # SSS below this -> P3
```

Weights and thresholds are designed to be calibrated by in-country road safety experts. The defaults reflect equal weight on operating behavior and physical environment, with slightly lower weight on the VRU threshold tier because VRU exposure is estimated from proxies rather than observed counts. See `METHODOLOGY.md` for calibration guidance.

---

## Project structure

```
trace/
├── config/
│   └── config.yaml
├── tiers/
│   ├── tier1_speed.py         # V85 alignment scoring
│   ├── tier2_environment.py   # Road environment scoring + CV skeleton
│   └── tier3_vru.py           # Safe System VRU threshold scoring
├── scoring/
│   └── compositor.py          # Composite SSS, priority flags, explanations
├── visualization/
│   └── map_renderer.py        # Folium interactive map output
├── main.py                    # Pipeline orchestrator
├── README.md
├── METHODOLOGY.md
└── requirements.txt
```

---

## Evaluation approach

Since labeled crash outcomes are not available in the challenge dataset, the evaluation uses three tracks.

Internal consistency checks that score distributions across road type hierarchies are directionally correct, and that the priority flag distribution is not degenerate.

Sensitivity analysis reruns the composite scoring across a range of weight combinations, varying each tier weight while holding others constant. Segments that remain in P1 across all tested configurations are flagged as robust priority flags.

Spot-check validation manually reviews a stratified sample of segments across the priority spectrum, confirming that the plain-language explanation accurately describes the raw data driving the score.

---

## Limitations

Tier 2 currently uses road network attributes as a proxy for road environment in all segments where Mapillary imagery is unavailable or sparse. This means the environment scoring reflects road classification and land use categories rather than the physical visual character of the road. The CV integration (see `tiers/tier2_environment.py`) is designed to replace this proxy once a Mapillary API token is available.

VRU exposure in Tier 3 is estimated from land use, road class, and proximity to activity generators rather than from observed pedestrian or cyclist counts. In road environments where these proxies are weak, such as peri-urban transition zones with ambiguous classification, the T3 score should be interpreted with caution.

Segments without posted speed limit data receive a neutral T1 score of 50. These segments appear predominantly in the P2 band and are not false P1 flags, but they represent a data gap that limits the precision of the composite score for those locations.

---

## License

MIT License. See `LICENSE` for details.

The speed thresholds applied in Tier 3 are drawn from published guidance by the World Health Organization (WHO) and the International Transport Forum (ITF) on Safe System principles in road safety. Both sources are publicly available reference material.
