"""Sensitivity analyses (Table 3), exclusion of the three players whose load variables
could not be reproduced (Results 3.4), and the sample-size sensitivity analysis (Methods 2.7)."""
import os
import numpy as np
import pandas as pd
from scipy.stats import binom
from scipy.optimize import brentq
from p2_core import load, episodes, monitored_onsets, add_next7, stats, R, RESULTS

d = load()


def scenario(name, dd, ons):
    x = add_next7(dd.copy(), ons, 'oc')
    out = []
    for r, lab in R.items():
        ppv, base, rr, n, h = stats(x, r, 'oc')
        out.append(dict(scenario=name, rule=lab, onsets=len(ons), PPV=ppv * 100, base=base * 100, RR=rr))
    return out


ep7 = episodes(d, 7); mon = monitored_onsets(d, ep7)
top2 = ep7.player.value_counts().head(2).index
first = mon.sort_values('date').groupby('player').head(1)
teamA = d[d.team == 'TeamA']
rows = []
rows += scenario('Primary: monitored onsets', d, mon)
rows += scenario('Excl. 2 most frequent reporters', d[~d.player.isin(top2)], mon[~mon.player.isin(top2)])
rows += scenario('First onset per player', d, first)
for gap in (14, 28):
    rows += scenario(f'Episode gap {gap} days', d, monitored_onsets(d, episodes(d, gap)))
rows += scenario('Team A only', teamA, monitored_onsets(teamA, episodes(teamA, 7)))
t = pd.DataFrame(rows)
print(t.round(2).to_string(index=False))
t.to_csv(os.path.join(RESULTS, 'table3_sensitivity.csv'), index=False)

# Players whose stored load variables could not be reproduced (see build_alerts.py)
chk = pd.read_csv(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'reproducibility_check.csv'))
bad = chk[chk.days - chk.days_reproduced > 0.05 * chk.days].player
x = d[~d.player.isin(bad)]; m = mon[~mon.player.isin(bad)]
print(f'\nExcluding {len(bad)} non-reproduced players: {len(m)} monitored onsets in {m.player.nunique()} players')
ex = pd.DataFrame(scenario('Excl. 3 non-reproduced players', x, m))
ex['alert_days_pct'] = [x[x['elig_' + r]]['alert_' + r].mean() * 100 for r in R]
print(ex.round(2).to_string(index=False))
ex.to_csv(os.path.join(RESULTS, 'excluding_nonreproduced_players.csv'), index=False)

# Sample-size sensitivity: smallest PPV detectable with a one-sided exact binomial test
# (alpha 0.025, power 0.80), treating new alerts as independent.
print('\nMinimum detectable PPV:')
p0s = {r: stats(add_next7(d.copy(), mon, 'oc'), r, 'oc') for r in R}
mde = []
for r, lab in R.items():
    _, p0, _, n, _ = p0s[r]
    k = int(binom.ppf(0.975, n, p0)) + 1
    while binom.sf(k - 1, n, p0) > 0.025:
        k += 1
    p1 = brentq(lambda p: binom.sf(k - 1, n, p) - 0.80, p0, 0.5)
    mde.append(dict(rule=lab, new_alerts=n, baseline=p0 * 100, min_detectable_PPV=p1 * 100, RR=p1 / p0))
mde = pd.DataFrame(mde); print(mde.round(2).to_string(index=False))
mde.to_csv(os.path.join(RESULTS, 'sample_size_sensitivity.csv'), index=False)
