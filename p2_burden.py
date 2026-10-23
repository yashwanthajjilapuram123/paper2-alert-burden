"""Data available and alert burden (Results 3.1-3.2; Table 2 burden columns; Figure 2 medians)."""
import os
import numpy as np
import pandas as pd
from p2_core import load, episodes, monitored_onsets, R, RESULTS

d = load()
d['week'] = d.date.dt.to_period('W-SUN')
print(f'Player-days: {len(d):,}; players: {d.player.nunique()} '
      f'({d.groupby("team").player.nunique().to_dict()})')
e = d[d.elig_any]
print(f'Eligible for at least one rule: {len(e):,} player-days ({len(e) / len(d) * 100:.1f}%), '
      f'{e.groupby(["player", "week"]).ngroups:,} player-weeks')

ep = episodes(d, 7); mon = monitored_onsets(d, ep)
print(f'Injury episodes: {len(ep)} in {ep.player.nunique()} players '
      f'(Team A {ep.player.str.startswith("TeamA").sum()}); '
      f'two most frequent reporters: {ep.player.value_counts().head(2).sum()} episodes')
print(f'Monitored onsets: {len(mon)} in {mon.player.nunique()} players '
      f'(Team A {mon.player.str.startswith("TeamA").sum()}); '
      f'two most frequent: {mon.player.value_counts().head(2).sum()}')

rows = []
for r, lab in R.items():
    el = d[d['elig_' + r]]
    wk = el.groupby('week').agg(pl=('player', 'nunique'), n=('new_' + r, 'sum'))
    sq = (wk.n / wk.pl * 25)[wk.pl >= 5]                 # new alerts per week, 25-player squad
    pw = el.groupby(['player', 'week'])['new_' + r].any()
    rows.append(dict(rule=lab, eligible_days=len(el), alert_days_pct=el['alert_' + r].mean() * 100,
                     new_alerts=int(el['new_' + r].sum()), median_per_squad_week=np.median(sq),
                     player_weeks_with_new_alert_pct=pw.mean() * 100))
t = pd.DataFrame(rows)
print(t.round(1).to_string(index=False))
t.to_csv(os.path.join(RESULTS, 'table2_burden.csv'), index=False)
