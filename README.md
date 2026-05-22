# TRACE

**Tiered Road Alignment and Composite Evaluation**

A three-tier analytical framework for assessing whether posted speed limits are appropriate given real-world operating speeds, the physical road environment, and Safe System injury thresholds for vulnerable road users.

Built for the ADB AI for Safer Roads Innovation Challenge, applied to road network datasets from Thailand and Maharashtra, India.

---

## What this is

Most speed audit tools ask whether drivers are complying with the posted limit. This is not that. TRACE asks whether the limit itself is appropriate, which is a different question and a harder one.

The framework evaluates each road segment against three independent evidence streams:

- **Tier 1** — Does the 85th percentile operating speed (V85) align with the posted limit, or does the gap between them suggest the limit is structurally out of step with how the road is actually used?
- **Tier 2** — Does the road environment (derived from network attributes and, where available, street-level imagery) support the posted limit, or does the physical character of the road imply a lower safe speed?
- **Tier 3** — Is the posted limit consistent with Safe System biomechanical thresholds given the estimated exposure of pedestrians, cyclists, and powered two-wheeler users on that segment?

Each tier produces a sub-score from 0 to 100. The three are combined into a composite Speed Safety Score (SSS). Every segment output includes the sub-scores, a plain-language explanation of what is driving the result, and a priority flag.

---

## Results on ADB challenge datasets

| Country | Segments scored | With speed data | Mean SSS | P1: Immediate Review | P2: Secondary Review |
|---|---|---|---|---|---|
| Thailand | 55,884 | 11,134 | 61.0 | 33 | 45,683 |
| Maharashtra | 14,082 | 3,577 | 64.1 | 1 | 10,190 |

In Thailand, 20.4% of segments with speed data have a Speed Compliance Ratio above 1.15, meaning V85 exceeds the posted limit by more than 15%. In Maharashtra, that figure is 37.2%. The worst Thailand segment scores SSS 31.7, a secondary urban road where V85 runs at 114 km/h on a 66 km/h road, in an environment the model classifies as safe for 30 to 50 km/h.

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
git clone https://github.com/your-username/trace-speed-safety
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

For each country/dataset:

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

Since labeled crash outcomes are not available in the challenge dataset, the evaluation uses three tracks:

**Internal consistency** — Score distributions are checked against expected road type hierarchies (motorway segments should score differently from residential), and the priority flag distribution is checked for degeneracy.

**Sensitivity analysis** — The priority ranking is re-run across a range of weight combinations (each weight varied ±0.10 while others are held constant). Segments that remain in P1 across all tested configurations are flagged as robust priority flags.

**Spot-check validation** — For a sample of 50 segments across the priority spectrum, the plain-language explanation is reviewed against the raw speed and network data to confirm the stated mismatch is present and the score direction is correct.

---

## Limitations

Tier 2 currently uses road network attributes as a proxy for road environment in all segments where Mapillary imagery is unavailable or sparse. This means the environment scoring reflects road classification and land use categories rather than the physical visual character of the road. The CV integration (see `tiers/tier2_environment.py`) is designed to replace this proxy once a Mapillary API token is available.

VRU exposure in Tier 3 is estimated from land use, road class, and proximity to activity generators rather than from observed pedestrian or cyclist counts. In road environments where these proxies are weak (e.g., peri-urban transition zones with ambiguous classification), the T3 score should be interpreted with caution.

Segments without posted speed limit data receive a neutral T1 score of 50. These segments appear predominantly in the P2 band and are not false P1 flags, but they represent a data gap that limits the precision of the composite score for those locations.

---

## License

MIT License. See `LICENSE` for details.

The Safe System speed thresholds used in Tier 3 are drawn from published WHO and ITF guidance on Safe System principles, which are freely available reference material.
