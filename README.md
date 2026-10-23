# Many Alerts, Few Injuries: alert burden and yield of common monitoring rules

Code and derived data to reproduce all results in:

> Ajjilapuram, Y. (2026). *Many Alerts, Few Injuries: Alert Burden and Yield of Common Training-Load and Wellness Rules in Elite Women's Football.* Preprint, SportRxiv. [DOI to be added]

## What this study does
Football clubs often turn daily training-load and wellness data into simple alerts (for example, "ACWR above 1.5"). This study applies four common rules to two seasons of open data from two elite Norwegian women's football teams (SoccerMon; 50 players, 2020–2021) and asks two practical questions:

- **Alert burden:** how often does each rule fire? (new alerts per week for a 25-player squad)
- **Alert yield:** how many of those alerts are followed by a self-reported injury within 7 days, compared with the baseline on any monitored day?

| Rule | Alert when |
|---|---|
| ACWR > 1.5 | 7-day mean load ÷ 28-day mean load > 1.5 |
| Weekly load +15% | 7-day load more than 15% higher than one week earlier |
| Wellness z ≤ −1.5 | composite wellness z-score (6 items, own 28-day baseline) ≤ −1.5 |
| Monotony > 2.0 | 7-day mean load ÷ 7-day SD > 2.0 |
| Any rule | at least one of the four |

**Key results:** the weekly-load rule was true on 35.4% of eligible days and gave a median of 16.4 new alerts per squad-week; the other rules gave about 3.5 each. Only 0.2–1.2% of new alerts were followed by an injury report (29 monitored onsets), close to the 0.85–0.93% baseline, and no rule beat chance in a permutation test.

## How to run

**Option A – Google Colab (no installation).** Open `paper2_reproduce.ipynb` in Colab and choose Runtime → Run all (about 15–25 minutes).

**Option B – your own computer** (Python 3.10 or later):
```
pip install -r requirements.txt
bash run_all.sh
```
or run the steps one by one:
```
python build_alerts.py     # 1. definitions + reproducibility check
python p2_burden.py        # 2. data available + alert burden
python p2_yield.py         # 3. alert yield with bootstrap CIs
python p2_sensitivity.py   # 4. sensitivity analyses + sample-size sensitivity
python p2_permutation.py   # 5. permutation test
python make_figs_p2.py     # 6. Figures 1–4
```
All results are written to `results/` and figures to `figs/`. Random seeds are fixed, so the numbers match the paper exactly.

## Where each result in the paper comes from
| Paper | Script | Output |
|---|---|---|
| Methods 2.2–2.3 (definitions), Table 1 | `build_alerts.py` | printed |
| Methods 2.7 (sample size sensitivity) | `p2_sensitivity.py` | `results/sample_size_sensitivity.csv` |
| Results 3.1 (data available) | `p2_burden.py` | printed |
| Table 2 – burden columns, Results 3.2 | `p2_burden.py` | `results/table2_burden.csv` |
| Table 2 – yield columns, Results 3.3 | `p2_yield.py` | `results/table2_yield.csv` |
| Results 3.3 – permutation test | `p2_permutation.py` | `results/permutation.csv` |
| Table 3, Results 3.4 | `p2_sensitivity.py` | `results/table3_sensitivity.csv` |
| Results 3.4 – reproducibility check | `build_alerts.py`, `p2_sensitivity.py` | `data/reproducibility_check.csv`, `results/excluding_nonreproduced_players.csv` |
| Figure 1 – one player's season | `make_figs_p2.py` | `figs/Figure1` |
| Figure 2 – alert burden | `make_figs_p2.py` | `figs/Figure2` |
| Figure 3 – alert yield | `make_figs_p2.py` | `figs/Figure3`, `results/fig3_values.csv` |
| Figure 4 – threshold sensitivity | `make_figs_p2.py` | `figs/Figure4`, `results/fig4_threshold_values.csv` |

## Repository contents
| File | Purpose |
|---|---|
| `paper2_reproduce.ipynb` | Colab notebook that runs steps 1–6 and shows the figures |
| `soccermon_build_panel.ipynb` | Colab notebook that downloads SoccerMon and builds `data/player_day_alerts.csv` from the raw files |
| `p2_core.py` | Shared functions: loading, injury episodes, monitored onsets, 7-day outcome, PPV, baseline, risk ratio, player-cluster bootstrap |
| `build_alerts.py` | Exact definitions of every load variable and alert flag, recomputed from the daily data and checked against the stored values |
| `p2_burden.py`, `p2_yield.py`, `p2_sensitivity.py`, `p2_permutation.py` | Analyses (see table above) |
| `make_figs_p2.py`, `figstyle.py` | Figures 1–4 (colour-blind-safe Okabe–Ito palette, same style as Paper 1) |
| `data/player_day_alerts.csv` | One row per player per day (50 players × 731 days = 36,550 rows) |
| `data/injury_episodes.csv` | 40 injury episodes (new episode after a gap of more than 7 days) |
| `run_all.sh`, `requirements.txt` | Run everything; package list |

### Columns in `data/player_day_alerts.csv`
| Column | Meaning |
|---|---|
| `player`, `team`, `date` | anonymised player ID (as in SoccerMon), team (TeamA/TeamB), calendar day |
| `daily_load` | daily training load from SoccerMon, derived from session RPE and duration (arbitrary units; 0 = no load entry) |
| `weekly_load` | sum of daily load over 7 days (ending on the current day) |
| `ctl28` | mean daily load over 28 days (chronic load) |
| `acwr` | (weekly_load / 7) / ctl28 |
| `monotony` | 7-day mean daily load / 7-day SD (population form) |
| `well_z` | composite wellness z-score (blank = no valid baseline) |
| `inj_report` | 1 = injury report on that day |
| `onset_any`, `onset_major`, `inj_next7`, `major_next7` | injury onset flags from the build notebook (the paper recomputes onsets in `p2_core.py`) |
| `elig_<rule>` | rule could be computed on that day |
| `alert_<rule>` | rule was true on that day |
| `new_<rule>` | first day of a run of alert days (a *new alert*) |

`<rule>` is `acwr`, `spike` (weekly load +15%), `well`, `mono` or `any`.

## Key definitions
- **Injury onset:** first day of an episode; a new episode starts when more than 7 days have passed since the player's previous injury report.
- **Monitored onset (primary analysis):** an onset with at least 3 eligible days in the preceding 7 days (29 of 40 onsets).
- **Outcome:** a monitored onset on days t+1 to t+7.
- **Alert yield (PPV):** % of new alerts followed by the outcome. **Baseline:** the same % across all eligible days.
- **Risk ratio:** outcome rate on alert days ÷ outcome rate on eligible non-alert days.
- **CIs:** 2,000 bootstrap resamples of players (percentile method).

## Reproducibility note
`build_alerts.py` reproduces the stored load variables for 47 of the 50 players (99.97% of their player-days). For three players the stored values do not match the daily loads on 850 of 2,193 player-days, which suggests a duplicated or misaligned record in the source data. Excluding these players does not change the findings (`results/excluding_nonreproduced_players.csv`); this is reported in the paper.

## Data source
The raw data are **not** included here. They come from the SoccerMon dataset (subjective data, `subjective.zip`), Zenodo record 10033832, CC-BY 4.0:

- Midoglu, C., Winther, A. K., Boeker, M., et al. (2024). A large-scale multivariate soccer athlete health, performance, and position monitoring dataset. *Scientific Data*, 11, 553. https://doi.org/10.1038/s41597-024-03386-x

Injury reports in SoccerMon are self-reported (body map, minor/major) and are not medical diagnoses. The derived files in `data/` are shared under the same CC-BY 4.0 licence; please cite Midoglu et al. (2024) if you use them.

## Citation
See `CITATION.cff`.

## Licence
Code in this repository: MIT. Data keep their original CC-BY 4.0 licence.
