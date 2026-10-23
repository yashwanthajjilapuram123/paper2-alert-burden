"""Alert yield (Table 2 yield columns; Results 3.3): PPV of new alerts, baseline,
risk ratio and 95% CIs from 2,000 player-cluster bootstrap resamples."""
import os
import numpy as np
import pandas as pd
from p2_core import primary, stats, boot, R, RESULTS

d, mon = primary()
rows = []
for r, lab in R.items():
    ppv, base, rr, n, h = stats(d, r, 'oc')
    ci = boot(d, r, 'oc', B=2000, seed=1)
    rows.append(dict(rule=lab, new_alerts=n, followed=h, PPV=ppv * 100,
                     PPV_lo=ci[0][0] * 100, PPV_hi=ci[1][0] * 100, baseline=base * 100,
                     RR=rr, RR_lo=ci[0][2], RR_hi=ci[1][2],
                     alerts_per_alert_followed=n / h if h else np.inf))
t = pd.DataFrame(rows)
print(t.round(2).to_string(index=False))
t.to_csv(os.path.join(RESULTS, 'table2_yield.csv'), index=False)
