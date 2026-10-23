"""Permutation test of alert yield (Methods 2.8; Results 3.3).
Within each player, injury onsets are moved to randomly chosen days on which the
player was monitored (eligible for any rule) and the PPV of each rule is recomputed.
One-sided p = (number of permuted PPVs >= observed + 1) / (B + 1)."""
import os
import numpy as np
import pandas as pd
from p2_core import primary, add_next7, stats, R, RESULTS

B = 2000
rng = np.random.default_rng(2026)
base, mon = primary()
d = base.drop(columns='oc')
obs = {r: stats(base, r, 'oc')[0] for r in R}
days = {p: g.date.values for p, g in d[d.elig_any].groupby('player')}
cnt = mon.player.value_counts()
perm = {r: [] for r in R}
for b in range(B):
    fake = pd.DataFrame([(p, t) for p, k in cnt.items() for t in rng.choice(days[p], k, replace=False)],
                        columns=['player', 'date'])
    x = add_next7(d.copy(), fake, 'oc')
    for r in R:
        perm[r].append(stats(x, r, 'oc')[0])
rows = []
for r in R:
    a = np.array(perm[r])
    rows.append(dict(rule=R[r], observed_PPV=obs[r] * 100, mean_permuted_PPV=a.mean() * 100,
                     p_one_sided=((a >= obs[r]).sum() + 1) / (B + 1)))
out = pd.DataFrame(rows); print(out.round(3).to_string(index=False))
out.to_csv(os.path.join(RESULTS, 'permutation.csv'), index=False)
