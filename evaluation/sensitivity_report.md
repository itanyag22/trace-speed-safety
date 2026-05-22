# TRACE — Sensitivity Analysis Report

This report tests how Priority 1 segment classifications respond to variation in tier weights. The analysis distinguishes between core combinations, which represent plausible operational weightings where all three tiers contribute, and reference combinations, which are single-tier extremes used for diagnostic purposes only.

Robustness is graded against the eight core combinations: a segment is Robust if it is P1 under all eight, Strong if P1 under six or more, Moderate if P1 under four or more, and Borderline if P1 under fewer than four.

---

## Weight combinations

### Core (operational)

| Label | T1 | T2 | T3 |
|---|---|---|---|
| Default | 0.350 | 0.350 | 0.300 |
| Equal thirds | 0.333 | 0.333 | 0.334 |
| T1 heavy | 0.500 | 0.300 | 0.200 |
| T2 heavy | 0.300 | 0.500 | 0.200 |
| T3 heavy | 0.250 | 0.250 | 0.500 |
| T1 light | 0.200 | 0.400 | 0.400 |
| T2 light | 0.400 | 0.200 | 0.400 |
| T3 light | 0.400 | 0.400 | 0.200 |

### Reference (single-tier, diagnostic only)

| Label | T1 | T2 | T3 |
|---|---|---|---|
| Speed only | 1.000 | 0.000 | 0.000 |
| Environment only | 0.000 | 1.000 | 0.000 |
| VRU only | 0.000 | 0.000 | 1.000 |
| T1+T2 only | 0.500 | 0.500 | 0.000 |
| T1+T3 only | 0.500 | 0.000 | 0.500 |
| T2+T3 only | 0.000 | 0.500 | 0.500 |

---

## Thailand

Total segments: 55,884 | With speed data: 11,134 | Default P1: 33

### P1 count by weight combination

| Combination | T1 | T2 | T3 | P1 count | P1 % | Mean SSS |
|---|---|---|---|---|---|---|
| Default | 0.35 | 0.35 | 0.30 | 33 | 0.06% | 61.0 |
| Equal thirds | 0.33 | 0.33 | 0.33 | 62 | 0.11% | 60.4 |
| T1 heavy | 0.50 | 0.30 | 0.20 | 12 | 0.02% | 60.7 |
| T2 heavy | 0.30 | 0.50 | 0.20 | 2 | 0.0% | 64.5 |
| T3 heavy | 0.25 | 0.25 | 0.50 | 309 | 0.55% | 57.8 |
| T1 light | 0.20 | 0.40 | 0.40 | 136 | 0.24% | 61.3 |
| T2 light | 0.40 | 0.20 | 0.40 | 189 | 0.34% | 57.5 |
| T3 light | 0.40 | 0.40 | 0.20 | 5 | 0.01% | 62.6 |
| **Reference combinations** | | | | | | |
| Speed only | 1.00 | 0.00 | 0.00 | 528 | 0.94% | 56.3 |
| Environment only | 0.00 | 1.00 | 0.00 | 405 | 0.72% | 75.3 |
| VRU only | 0.00 | 0.00 | 1.00 | 1209 | 2.16% | 49.7 |
| T1+T2 only | 0.50 | 0.50 | 0.00 | 5 | 0.01% | 65.8 |
| T1+T3 only | 0.50 | 0.00 | 0.50 | 462 | 0.83% | 53.0 |
| T2+T3 only | 0.00 | 0.50 | 0.50 | 516 | 0.92% | 62.5 |

### Robustness distribution (core combinations)

| Grade | Segments | Meaning |
|---|---|---|
| Robust | 2 | P1 under all 8 core combinations |
| Strong | 6 | P1 under 6 or 7 core combinations |
| Moderate | 54 | P1 under 4 or 5 core combinations |
| Borderline | 263 | P1 under 1 to 3 core combinations |

### Primary misalignment driver (default P1 segments)

The primary driver is the tier with the lowest sub-score on each P1 segment.

| Tier | Segments | What it means |
|---|---|---|
| T1 | 2 | Speed behavior is the dominant concern — traffic exceeds limit structurally |
| T3 | 31 | VRU exposure gap is dominant — limit far exceeds Safe System threshold |

### Default P1 segments — full detail

| Road | Class | Land use | Limit | V85 | SCR | T1 | T2 | T3 | SSS | Robustness | Core P1 count | Driver |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
|   | secondary | URBAN | 66 | 114 | 1.72 | 16 | 54 | 24 | 31.7 | Robust | 8/8 | T1 |
|   | secondary | URBAN | 70 | 99 | 1.42 | 27 | 50 | 16 | 32.0 | Robust | 8/8 | T3 |
|   | primary | URBAN | 80 | 109 | 1.36 | 35 | 59 | 4 | 34.0 | Strong | 7/8 | T3 |
|   | primary | URBAN | 80 | 110 | 1.38 | 36 | 58 | 4 | 34.1 | Strong | 7/8 | T3 |
|   | primary | URBAN | 80 | 106 | 1.32 | 40 | 60 | 4 | 36.2 | Strong | 6/8 | T3 |
|   | primary | URBAN | 80 | 106 | 1.32 | 40 | 60 | 4 | 36.2 | Strong | 6/8 | T3 |
|   | primary | URBAN | 80 | 105 | 1.31 | 41 | 61 | 4 | 36.7 | Strong | 6/8 | T3 |
|   | primary | URBAN | 80 | 105 | 1.31 | 42 | 61 | 4 | 37.3 | Moderate | 5/8 | T3 |
|   | primary | URBAN | 80 | 105 | 1.31 | 43 | 61 | 4 | 37.4 | Moderate | 5/8 | T3 |
|   | primary | URBAN | 80 | 104 | 1.30 | 43 | 61 | 4 | 37.5 | Moderate | 5/8 | T3 |
|   | primary | URBAN | 80 | 104 | 1.30 | 43 | 61 | 4 | 37.7 | Moderate | 5/8 | T3 |
|   | primary | URBAN | 80 | 103 | 1.29 | 43 | 62 | 4 | 37.7 | Moderate | 5/8 | T3 |
|   | primary | URBAN | 80 | 101 | 1.26 | 44 | 63 | 4 | 38.5 | Moderate | 5/8 | T3 |
|   | primary | URBAN | 80 | 102 | 1.27 | 45 | 62 | 4 | 38.6 | Moderate | 5/8 | T3 |
|   | secondary | RURAL | 70 | 109 | 1.56 | 21 | 83 | 8 | 38.8 | Moderate | 5/8 | T3 |
|   | secondary | URBAN | 60 | 94 | 1.57 | 16 | 64 | 37 | 38.9 | Strong | 6/8 | T1 |
|   | primary | URBAN | 80 | 102 | 1.27 | 46 | 62 | 4 | 38.9 | Moderate | 5/8 | T3 |
| Nakhon In Road | primary | URBAN | 80 | 102 | 1.27 | 46 | 63 | 4 | 39.0 | Moderate | 5/8 | T3 |
|   | primary | URBAN | 80 | 102 | 1.27 | 46 | 62 | 4 | 39.0 | Moderate | 5/8 | T3 |
| Phatthanakan Khu Khwang Road | primary | URBAN | 80 | 102 | 1.27 | 46 | 62 | 4 | 39.0 | Moderate | 5/8 | T3 |
|   | primary | URBAN | 80 | 101 | 1.26 | 46 | 63 | 4 | 39.2 | Moderate | 5/8 | T3 |
|   | primary | URBAN | 80 | 102 | 1.27 | 46 | 62 | 4 | 39.2 | Moderate | 5/8 | T3 |
|   | primary | URBAN | 80 | 101 | 1.26 | 46 | 63 | 4 | 39.4 | Moderate | 5/8 | T3 |
|   | primary | URBAN | 80 | 101 | 1.26 | 46 | 63 | 4 | 39.4 | Moderate | 5/8 | T3 |
|   | primary | URBAN | 80 | 101 | 1.26 | 46 | 63 | 4 | 39.4 | Moderate | 5/8 | T3 |
|   | primary | URBAN | 80 | 100 | 1.25 | 46 | 63 | 4 | 39.4 | Moderate | 5/8 | T3 |
|   | primary | URBAN | 80 | 100 | 1.25 | 46 | 63 | 4 | 39.5 | Moderate | 5/8 | T3 |
|   | secondary | URBAN | 70 | 90 | 1.29 | 43 | 56 | 16 | 39.5 | Moderate | 5/8 | T3 |
|   | primary | URBAN | 80 | 101 | 1.26 | 47 | 63 | 4 | 39.7 | Moderate | 5/8 | T3 |
|   | primary | URBAN | 80 | 101 | 1.26 | 48 | 63 | 4 | 39.8 | Moderate | 5/8 | T3 |
|   | primary | URBAN | 80 | 101 | 1.26 | 48 | 63 | 4 | 39.8 | Moderate | 5/8 | T3 |
| Borommaratchachonnani Elevated Highway | primary | URBAN | 80 | 100 | 1.25 | 47 | 63 | 4 | 39.8 | Moderate | 5/8 | T3 |
|   | primary | URBAN | 80 | 101 | 1.26 | 48 | 63 | 4 | 39.9 | Moderate | 5/8 | T3 |

---

## Maharashtra

Total segments: 14,082 | With speed data: 3,577 | Default P1: 1

### P1 count by weight combination

| Combination | T1 | T2 | T3 | P1 count | P1 % | Mean SSS |
|---|---|---|---|---|---|---|
| Default | 0.35 | 0.35 | 0.30 | 1 | 0.01% | 64.1 |
| Equal thirds | 0.33 | 0.33 | 0.33 | 3 | 0.02% | 63.6 |
| T1 heavy | 0.50 | 0.30 | 0.20 | 3 | 0.02% | 62.8 |
| T2 heavy | 0.30 | 0.50 | 0.20 | 0 | 0.0% | 68.1 |
| T3 heavy | 0.25 | 0.25 | 0.50 | 16 | 0.11% | 61.2 |
| T1 light | 0.20 | 0.40 | 0.40 | 1 | 0.01% | 65.3 |
| T2 light | 0.40 | 0.20 | 0.40 | 16 | 0.11% | 60.0 |
| T3 light | 0.40 | 0.40 | 0.20 | 1 | 0.01% | 65.5 |
| **Reference combinations** | | | | | | |
| Speed only | 1.00 | 0.00 | 0.00 | 880 | 6.25% | 55.1 |
| Environment only | 0.00 | 1.00 | 0.00 | 0 | 0.0% | 81.6 |
| VRU only | 0.00 | 0.00 | 1.00 | 452 | 3.21% | 54.0 |
| T1+T2 only | 0.50 | 0.50 | 0.00 | 0 | 0.0% | 68.3 |
| T1+T3 only | 0.50 | 0.00 | 0.50 | 120 | 0.85% | 54.6 |
| T2+T3 only | 0.00 | 0.50 | 0.50 | 0 | 0.0% | 67.8 |

### Robustness distribution (core combinations)

| Grade | Segments | Meaning |
|---|---|---|
| Robust | 0 | P1 under all 8 core combinations |
| Strong | 1 | P1 under 6 or 7 core combinations |
| Moderate | 2 | P1 under 4 or 5 core combinations |
| Borderline | 16 | P1 under 1 to 3 core combinations |

### Primary misalignment driver (default P1 segments)

The primary driver is the tier with the lowest sub-score on each P1 segment.

| Tier | Segments | What it means |
|---|---|---|
| T3 | 1 | VRU exposure gap is dominant — limit far exceeds Safe System threshold |

### Default P1 segments — full detail

| Road | Class | Land use | Limit | V85 | SCR | T1 | T2 | T3 | SSS | Robustness | Core P1 count | Driver |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Unnamed | secondary | URBAN | 55 | 80 | 1.45 | 18 | 77 | 9 | 36.0 | Strong | 7/8 | T3 |

---

## Key findings

The majority of default P1 segments in both countries are T3-driven: their primary misalignment is the gap between the posted limit and the Safe System biomechanical threshold for the most exposed vulnerable road user class on that segment. This means their P1 classification is sensitive to T3 weight. Under T3-heavy configurations they remain firmly P1; under T2-heavy or T3-light configurations some move to P2.

This is a finding about the nature of the problem, not a weakness in the methodology. The Safe System framework explicitly places VRU protection as the primary criterion for speed limit appropriateness. A ministry that follows Safe System principles should weight T3 at least as heavily as T1 and T2, which would strengthen the P1 classification for the identified segments rather than weaken it. The default weights (0.35/0.35/0.30) are conservative.

Segments that survive T2-heavy and T3-light weightings represent cases where speed misalignment alone is severe enough to warrant P1 classification. These are the most operationally conservative flags: a segment that scores P1 even when VRU protection is underweighted has a problem that goes beyond Safe System compliance alone.