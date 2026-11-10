# Measured results

All values below come from saved experiment artifacts.

Demo selected using development only: **hybrid**.

## Development outer CV

| Method | Precision | Recall | F1 mean ± sample SD | FPR | AP |
|---|---:|---:|---:|---:|---:|
| rules | 1.000000 | 0.542602 | 0.703459 ± 0.007700 | 0.000000 | N/A |
| structural | 1.000000 | 0.998965 | 0.999482 ± 0.000173 | 0.000000 | 0.999933 |
| text | 0.999884 | 0.996094 | 0.997985 ± 0.000429 | 0.000065 | 0.999889 |
| hybrid | 1.000000 | 0.999311 | 0.999655 ± 0.000171 | 0.000000 | 0.999934 |
| kbest | 0.998153 | 0.995057 | 0.996602 ± 0.000664 | 0.001036 | 0.999848 |
| ga | 1.000000 | 0.995067 | 0.997525 ± 0.001757 | 0.000000 | 0.999863 |
| gwo_s | 0.998961 | 0.994837 | 0.996892 ± 0.001746 | 0.000583 | 0.999881 |
| gwo_v | 0.999308 | 0.997470 | 0.998388 ± 0.000723 | 0.000389 | 0.999916 |
| random | 0.999538 | 0.996786 | 0.998159 ± 0.000692 | 0.000259 | 0.999911 |

## Cost and seed variation

Each search has 60 objective calls; each nonempty call fits three LRs.
12 outer + 12 full-development searches use 1,440 objective calls.
Nonsearch methods do not incur those costs. Final scoring performs no fits.

| Method | Outer fits | Search s | Full-dev fits | Fitness seeds 0/1/2 | Features |
|---|---:|---:|---:|---|---:|
| rules | 0 | 0.000 | 0 | N/A | 0 |
| structural | 3 | 0.000 | 1 | N/A | 20 |
| text | 3 | 0.000 | 1 | N/A | 0 |
| hybrid | 3 | 0.000 | 1 | N/A | 20 |
| kbest | 3 | 0.000 | 1 | N/A | 8 |
| ga | 543 | 24.204 | 541 | 0.010858/0.009051/0.008446 | 7 |
| gwo_s | 543 | 24.048 | 541 | 0.008878/0.008449/0.009859 | 6 |
| gwo_v | 543 | 24.821 | 541 | 0.008878/0.007339/0.007973 | 5 |
| random | 543 | 24.085 | 541 | 0.009439/0.011494/0.010220 | 8 |

Masks, seed counts, metrics, timings, CSR bytes and strata are in `results/`.
CSR bytes measure buffers, not peak RAM. Folds/seeds are correlated;
SD is descriptive and no statistical significance or deployment effectiveness is claimed.

## Development grouping stress test

Primary groups: 24124; stress groups: 14998. Stress-group overlap in primary outer folds: [416, 420, 400].
- hybrid: stress-disjoint F1 0.999049 ± 0.000754.
- structural: stress-disjoint F1 0.999003 ± 0.000694.
- text: stress-disjoint F1 0.989559 ± 0.005820.

The heuristic merges strings aggressively and is not a source-separated holdout.
No primary duplicates: representative-group metrics equal row metrics.
Benign CSIC values and sqlmap-generated SQLi remain source-confounded. High scores are
not evidence of generalization to deployed attacks. The rule baseline's misses and every
optimizer's unfavorable comparisons are retained. False positives use aggregate
length/encoding/keyword strata only; no third-party payloads are republished.

![F1 comparison](../results/plots/f1.png)

![Full-development search traces](../results/plots/convergence.png)
