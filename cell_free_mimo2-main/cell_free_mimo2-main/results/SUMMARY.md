# Benchmark summary

## Claims derived from the numbers

1. Bug fixes changed the QNN (cloud + edge) min rate by +33.3% (0.479 → 0.638), p = nan: **not a significant improvement**.
2. Bug fixes changed the QNN assignment + MR min rate by -40.2% (1.367 → 0.818), p = nan: **not a significant improvement**.
3. QNN (cloud + edge) reaches 20.1% (i.i.d.) vs 7.9% (V2X) of the search-based min rate → change of -12.2 points: **moderately affected** on the realistic channel.
4. QNN assignment + MR reaches 32.1% (i.i.d.) vs 16.1% (V2X) of the search-based min rate → change of -16.0 points: **degrades** on the realistic channel.
5. QNN assignment + MR: a decision stays within 90% of its fresh min rate for 5 ms at 20 km/h, 2 ms at 40 km/h, 2 ms at 80 km/h, 1 ms at 120 km/h → at 40 km/h the cloud should re-decide every 2 ms (grid resolution: 0, 0.25, 0.5, 1, 2, 5 ms).
6. Search-based + MR: a decision stays within 90% of its fresh min rate for 0.25 ms at 20 km/h, < 0.25 ms at 40 km/h, < 0.25 ms at 80 km/h, < 0.25 ms at 120 km/h → at 40 km/h the cloud should re-decide every < 0.25 ms (grid resolution: 0, 0.25, 0.5, 1, 2, 5 ms).
7. Training QNN (cloud + edge) on V2X instead of i.i.d. data changes its V2X min rate by +0.2% (p = nan, not significant).
8. Training QNN assignment + MR on V2X instead of i.i.d. data changes its V2X min rate by +0.0% (p = nan, not significant).
9. The V2X channel reproduces the SOP.m physics: antenna correlation 0.98 (i.i.d.: 0.02), time correlation follows Clarke's J0 (coherence ≈ 1.9 ms at 40 km/h), delay spread 200 ns.

Seeds: 1, epochs: 2, training samples: 10, test samples: 5 per seed. Values are mean ± std over seeds. All rates in bits/s/Hz with the corrected gain |hᵀv|².

## E0 — Bug fixes (original Rayleigh channel)

| Method | Legacy code | Fixed code |
|---|---|---|
| QNN (cloud + edge) (min rate) | 0.479 ± 0.000 | 0.638 ± 0.000 |
| QNN assignment + MR (min rate) | 1.367 ± 0.000 | 0.818 ± 0.000 |
| Search-based + MR (min rate) | 2.376 ± 0.000 | 2.536 ± 0.000 |
| Strongest channel + MR (min rate) | 1.744 ± 0.000 | 1.744 ± 0.000 |
| Random + MR (min rate) | 1.716 ± 0.000 | 1.716 ± 0.000 |

Old code's own printout of the QNN min rate (wrong gain formula): 0.509 ± 0.000; with the correct formula: 0.479 ± 0.000.

## E1 — i.i.d. Rayleigh vs V2X (same layout and pathloss, fixed code)

| Method | Min rate i.i.d. | Min rate V2X | Sum rate i.i.d. | Sum rate V2X | Jain V2X | Decision time [ms] |
|---|---|---|---|---|---|---|
| QNN (cloud + edge) | 0.632 ± 0.000 | 0.179 ± 0.000 | 4.317 ± 0.000 | 4.402 ± 0.000 | 0.645 | 44.43 |
| QNN assignment + MR | 1.010 ± 0.000 | 0.368 ± 0.000 | 5.358 ± 0.000 | 5.726 ± 0.000 | 0.684 | 19.43 |
| Search-based + MR | 3.150 ± 0.000 | 2.282 ± 0.000 | 13.485 ± 0.000 | 12.493 ± 0.000 | 0.791 | 0.51 |
| Strongest channel + MR | 1.876 ± 0.000 | 1.877 ± 0.000 | 14.344 ± 0.000 | 15.205 ± 0.000 | 0.798 | 0.31 |
| Random + MR | 1.142 ± 0.000 | 1.106 ± 0.000 | 10.354 ± 0.000 | 8.206 ± 0.000 | 0.702 | 0.22 |

- QNN (cloud + edge) reaches **20.1%** of search-based min rate on i.i.d. and **7.9%** on V2X.
- QNN assignment + MR reaches **32.1%** of search-based min rate on i.i.d. and **16.1%** on V2X.

## E2 — CSI ageing on V2X (decision on H(0), rates on H(Δ))

Min rate (mean over seeds):

**QNN assignment + MR**

| Speed \ Δ [ms] | 0 | 0.25 | 0.5 | 1 | 2 | 5 | Lifetime (≥90%) |
|---|---|---|---|---|---|---|---|
| 20 km/h | 0.368 | 0.371 | 0.363 | 0.367 | 0.445 | 0.662 | 5 ms |
| 40 km/h | 0.368 | 0.363 | 0.367 | 0.446 | 0.343 | 0.303 | 2 ms |
| 80 km/h | 0.368 | 0.367 | 0.446 | 0.343 | 0.588 | 0.317 | 2 ms |
| 120 km/h | 0.368 | 0.413 | 0.389 | 0.508 | 0.171 | 0.744 | 1 ms |

**Search-based + MR**

| Speed \ Δ [ms] | 0 | 0.25 | 0.5 | 1 | 2 | 5 | Lifetime (≥90%) |
|---|---|---|---|---|---|---|---|
| 20 km/h | 2.282 | 2.147 | 1.977 | 1.226 | 1.519 | 1.207 | 0.25 ms |
| 40 km/h | 2.282 | 1.977 | 1.225 | 1.518 | 0.971 | 1.074 | < 0.25 ms |
| 80 km/h | 2.282 | 1.225 | 1.518 | 0.973 | 1.495 | 1.612 | < 0.25 ms |
| 120 km/h | 2.282 | 1.423 | 1.522 | 1.376 | 1.556 | 1.349 | < 0.25 ms |

**QNN (cloud + edge)**

| Speed \ Δ [ms] | 0 | 0.25 | 0.5 | 1 | 2 | 5 | Lifetime (≥90%) |
|---|---|---|---|---|---|---|---|
| 20 km/h | 0.179 | 0.223 | 0.276 | 0.363 | 0.335 | 0.437 | 5 ms |
| 40 km/h | 0.179 | 0.276 | 0.363 | 0.336 | 0.215 | 0.182 | 5 ms |
| 80 km/h | 0.179 | 0.363 | 0.337 | 0.215 | 0.322 | 0.193 | 5 ms |
| 120 km/h | 0.179 | 0.383 | 0.263 | 0.267 | 0.131 | 0.381 | 1 ms |

## E3 — Generalisation (tested on V2X)

| Method | Trained on i.i.d. | Trained on V2X |
|---|---|---|
| QNN (cloud + edge) | 0.179 ± 0.000 | 0.179 ± 0.000 |
| QNN assignment + MR | 0.368 ± 0.000 | 0.368 ± 0.000 |

## E4 — Channel structure (normalized by large-scale gain)

| | i.i.d. | V2X |
|---|---|---|
| Mean ‖h‖²/(β·N_TX) | 0.845 | 1.057 |
| 10th percentile (deep fades) | 0.276 | 0.066 |
| Beam leakage to other users | 0.420 | 0.700 |

## Channel validation (validate_channel.py)

```
{
  "power_ratio_mean": 0.9962920836468482,
  "power_ratio_ok": true,
  "antenna_corr_v2x": 0.9803650819200218,
  "antenna_corr_iid": 0.02383887871773978,
  "f_max_hz": 218.66979574101077,
  "ray_doppler_max_hz": 220.49946847306717,
  "doppler_ok": true,
  "time_corr_delays_ms": [
    0.0,
    0.25,
    0.5,
    1.0,
    2.0,
    5.0
  ],
  "time_corr_measured": [
    1.0,
    0.957,
    0.861,
    0.547,
    0.17,
    0.307
  ],
  "time_corr_clarke": [
    1.0,
    0.971,
    0.885,
    0.581,
    0.163,
    0.297
  ],
  "time_corr_ok": true,
  "coherence_time_ms": 1.9344235383152544,
  "accel_phase_max_rad": 0.0618268447595793,
  "accel_phase_bound_rad": 0.06182742814757461,
  "delay_spread_max_ns": 200.13735564220607,
  "delay_spread_bound_ns": 200.1384571188912,
  "delay_ok": true,
  "median_link_snr_db": 11.824649058413023
}
```
