"""Step 2 of the pipeline: rebuild every load variable and alert flag from the daily panel.

Input : data/player_day_alerts.csv  (uses only player, team, date, daily_load, well_z, inj_report)
Output: printed agreement with the stored columns, and data/reproducibility_check.csv

This script documents the exact definitions used in the paper and is the
reproducibility check reported in the Methods and Results:
  weekly load  = sum of daily load over 7 days (ending on and including the current day)
  chronic load = mean daily load over 28 days (ending on and including the current day)
  ACWR         = (weekly load / 7) / chronic load            (coupled ACWR)
  monotony     = 7-day mean daily load / 7-day SD (population form)
Days without a load entry carry a daily load of zero.
"""
import os
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
d = pd.read_csv(os.path.join(HERE, 'data', 'player_day_alerts.csv'), parse_dates=['date'])
d = d.sort_values(['player', 'date']).reset_index(drop=True)
g = d.groupby('player')

# ---- load variables -------------------------------------------------------
r = pd.DataFrame(index=d.index)
r['weekly_load'] = g.daily_load.transform(lambda s: s.rolling(7, min_periods=1).sum())
r['ctl28'] = g.daily_load.transform(lambda s: s.rolling(28, min_periods=1).sum() / 28)
r['acwr'] = np.where(r.ctl28 > 0, (r.weekly_load / 7) / r.ctl28.where(r.ctl28 > 0), 0.0)
sd7 = g.daily_load.transform(lambda s: s.rolling(7, min_periods=1).std(ddof=0))
r['monotony'] = np.where(sd7 > 0, (r.weekly_load / 7) / sd7.where(sd7 > 0), 0.0)

# ---- eligibility, alert days and new alerts ---------------------------------
first_load = d[d.daily_load > 0].groupby('player').date.min()
days_since_first = (d.date - d.player.map(first_load)).dt.days
prev_week = r.groupby(d.player).weekly_load.shift(7)

r['elig_acwr'] = (days_since_first >= 28) & (r.ctl28 > 0) & (r.weekly_load > 0)
r['alert_acwr'] = r.elig_acwr & (r.acwr > 1.5)
r['elig_spike'] = (r.weekly_load > 0) & (prev_week > 0)
r['alert_spike'] = r.elig_spike & (r.weekly_load / prev_week > 1.15)
r['elig_well'] = d.well_z.notna()
r['alert_well'] = r.elig_well & (d.well_z <= -1.5)
r['elig_mono'] = r.weekly_load > 0
r['alert_mono'] = r.elig_mono & (r.monotony > 2.0)
r['elig_any'] = r.elig_acwr | r.elig_spike | r.elig_well | r.elig_mono
r['alert_any'] = r.alert_acwr | r.alert_spike | r.alert_well | r.alert_mono
for k in ['acwr', 'spike', 'well', 'mono', 'any']:
    prev = r['alert_' + k].groupby(d.player).shift(1, fill_value=False).astype(bool)
    r['new_' + k] = r['alert_' + k] & ~prev        # first day of each run of alert days

# ---- compare with the stored columns ----------------------------------------
def close(a, b, rel=1e-3, abs_=0.006):
    return (np.abs(a - b) <= np.maximum(abs_, rel * np.abs(b))) | (a.isna() & b.isna())

load_ok = (close(r.weekly_load, d.weekly_load) & close(r.ctl28, d.ctl28) &
           close(pd.Series(r.monotony, index=d.index), d.monotony))
per_player = load_ok.groupby(d.player).agg(['size', 'sum'])
per_player['mismatched_days'] = per_player['size'] - per_player['sum']
mism = per_player[per_player.mismatched_days > 0.05 * per_player['size']]
print(f'Players whose stored load variables are reproduced (>=95% of days): '
      f'{d.player.nunique() - len(mism)} of {d.player.nunique()}')
good = ~d.player.isin(mism.index)
print(f'Agreement on those players: {load_ok[good].mean() * 100:.2f}% of player-days')
for p, row in mism.iterrows():
    print(f'  not reproduced: {p}  ({int(row.mismatched_days)} of {int(row["size"])} days)')
print(f'  total: {int(mism.mismatched_days.sum())} of {int(mism["size"].sum())} player-days')

print('\nAgreement of rule flags with stored flags (players reproduced):')
for c in [c for c in r.columns if c.startswith(('elig_', 'alert_', 'new_'))]:
    print(f'  {c:12s} {(r.loc[good, c].astype(bool) == d.loc[good, c].astype(bool)).mean() * 100:6.2f}%')

per_player.rename(columns={'size': 'days', 'sum': 'days_reproduced'}).to_csv(
    os.path.join(HERE, 'data', 'reproducibility_check.csv'))
