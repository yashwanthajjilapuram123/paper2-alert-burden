#!/usr/bin/env bash
# Reproduce every number, table and figure in Paper 2 from data/player_day_alerts.csv.
set -e
cd "$(dirname "$0")"
python3 build_alerts.py     # definitions + reproducibility check  -> data/reproducibility_check.csv
python3 p2_burden.py        # data available + alert burden        -> results/table2_burden.csv
python3 p2_yield.py         # alert yield, bootstrap CIs           -> results/table2_yield.csv
python3 p2_sensitivity.py   # Table 3, 3-player exclusion, MDE     -> results/table3_sensitivity.csv, ...
python3 p2_permutation.py   # permutation test                     -> results/permutation.csv
python3 make_figs_p2.py     # Figures 1-4                          -> figs/
