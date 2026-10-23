"""Paper 2 figures: alert burden and alert yield of common monitoring rules (SoccerMon).
Input : data/player_day_alerts.csv
Output: figs/Figure1-4 (.pdf for LaTeX, .png for preview)
"""
import os, sys
import numpy as np, pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from figstyle import style, INK, MUTED
from p2_core import load, episodes, monitored_onsets, add_next7, stats, boot, RESULTS
d = load()

style()
plt.rcParams.update({'font.size': 7.5, 'axes.labelsize': 7.5, 'xtick.labelsize': 7, 'ytick.labelsize': 7.5,
                     'legend.fontsize': 7})
OUT = os.path.join(HERE, 'figs') + '/'; os.makedirs(OUT, exist_ok=True)

RULES = ['acwr', 'spike', 'well', 'mono', 'any']
LAB = {'acwr': 'ACWR > 1.5', 'spike': 'Weekly load +15%', 'well': 'Wellness z ≤ −1.5',
       'mono': 'Monotony > 2.0', 'any': 'Any rule'}
COL = {'acwr': '#0072B2', 'spike': '#E69F00', 'well': '#CC79A7', 'mono': '#009E73', 'any': '#4D4D4D'}
MK = {'acwr': 'o', 'spike': 's', 'well': 'D', 'mono': '^', 'any': 'o'}

def wilson(k, n, z=1.96):
    if n == 0: return np.nan, np.nan
    p = k / n; den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den; h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return max(0, c - h), c + h

def save(fig, name):
    fig.savefig(OUT + name + '.pdf'); fig.savefig(OUT + name + '.png', dpi=400); plt.close(fig)

mon = monitored_onsets(d, episodes(d, 7))
dd = add_next7(d.copy(), mon, 'oc').sort_values(['player', 'date'])
dd['week'] = dd.date.dt.to_period('W-SUN')

# ======================= Figure 1: one player's season =======================
vc = mon.player.value_counts()
p = sorted(vc[vc == vc.max()].index)[0]          # deterministic choice among players with the most onsets
t0, t1 = pd.Timestamp('2020-05-01'), pd.Timestamp('2020-11-30')
g = dd[(dd.player == p) & (dd.date >= t0) & (dd.date <= t1)].set_index('date')
rows = ['acwr', 'spike', 'well', 'mono', 'inj']
n = len(rows)
fig, ax = plt.subplots(figsize=(6.85, 2.5))
for i, r in enumerate(rows):
    y = n - 1 - i
    ax.axhspan(y - 0.5, y + 0.5, color='#F4F4F4' if i % 2 == 0 else 'white', zorder=0, lw=0)
    if r == 'inj':
        for t in g.index[g.inj_report > 0]:
            ax.broken_barh([(mdates.date2num(t), 1)], (y - 0.28, 0.56), facecolors=INK, edgecolor='none')
        continue
    a = g['alert_' + r].astype(int)
    starts = a.index[(a.diff().fillna(a.iloc[0]) == 1)]
    ends = a.index[(a.diff(-1).fillna(a.iloc[-1]) == 1)]
    spans = [(mdates.date2num(s), mdates.date2num(e) - mdates.date2num(s) + 1) for s, e in zip(starts, ends)]
    ax.broken_barh(spans, (y - 0.28, 0.56), facecolors=COL[r], edgecolor='none')
allon = episodes(d, 7)
allon = allon[(allon.player == p) & (allon.date >= t0) & (allon.date <= t1)].date
monset = set(mon[mon.player == p].date)
for t in allon:
    used = t in monset
    ax.axvline(mdates.date2num(t) + 0.5, color=INK if used else MUTED, lw=0.9,
               ls=(0, (2.5, 2)) if used else (0, (1, 1.5)), zorder=3)
    ax.plot(mdates.date2num(t) + 0.5, n - 0.32, marker='v', ms=5, zorder=4, clip_on=False,
            color=INK if used else 'white', mec=INK if used else MUTED, mew=0.9)
labels = {**LAB, 'inj': 'Injury report'}
ax.set_yticks(range(n)); ax.set_yticklabels([labels[r] for r in rows][::-1])
ax.set_ylim(-0.5, n - 0.2); ax.set_xlim(t0, t1 + pd.Timedelta(days=1))
ax.xaxis.set_major_locator(mdates.MonthLocator()); ax.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
ax.grid(False); ax.tick_params(axis='y', length=0)
for sp in ['left', 'top', 'right']: ax.spines[sp].set_visible(False)
ax.set_xlabel('2020 season (May–November)')
ax.legend(handles=[Patch(facecolor='#9A9A9A', label='Alert active'),
                   Line2D([0], [0], color=INK, lw=0.9, ls=(0, (2.5, 2)), marker='v', ms=5, label='Injury onset (analysed)'),
                   Line2D([0], [0], color=MUTED, lw=0.9, ls=(0, (1, 1.5)), marker='v', ms=5, mfc='white', mec=MUTED,
                          label='Onset not analysed (<3 monitored days before)')],
          loc='lower center', bbox_to_anchor=(0.5, 1.0), ncol=3, frameon=False, handlelength=2.2, columnspacing=1.2)
save(fig, 'Figure1')

# ======================= Figure 2: alert burden per week =======================
rng = np.random.default_rng(1)
fig, ax = plt.subplots(figsize=(6.4, 2.7))
for k, r in enumerate(RULES):
    y = len(RULES) - 1 - k
    e = dd[dd['elig_' + r]]
    wk = e.groupby('week').agg(pl=('player', 'nunique'), n=('new_' + r, 'sum'))
    v = (wk.n / wk.pl * 25)[wk.pl >= 5].values
    ax.scatter(v, y + 0.14 + rng.uniform(-0.13, 0.13, len(v)), s=4, color=COL[r], alpha=0.5, lw=0, rasterized=True)
    ax.boxplot([v], positions=[y - 0.2], orientation='horizontal', widths=0.14, whis=(5, 95), showfliers=False,
               medianprops=dict(color=INK, lw=1.4), boxprops=dict(color=INK, lw=0.7),
               whiskerprops=dict(color=INK, lw=0.7), capprops=dict(color=INK, lw=0.7))
    ax.text(1.02, y, f'{np.median(v):.1f}', transform=ax.get_yaxis_transform(), va='center', ha='left',
            fontsize=7, color=INK)
ax.axhline(0.5, color='#BBBBBB', lw=0.6)
ax.set_yticks(range(len(RULES))); ax.set_yticklabels([LAB[r] for r in RULES][::-1])
ax.set_ylim(-0.55, len(RULES) - 0.45); ax.set_xlim(-0.8, 36); ax.grid(axis='y', visible=False)
ax.tick_params(axis='y', length=0)
ax.text(1.02, len(RULES) - 0.45, 'Median', transform=ax.get_yaxis_transform(), va='bottom', ha='left',
        fontsize=6.6, color=MUTED)
ax.set_xlabel('New alerts per week, scaled to a 25-player squad')
save(fig, 'Figure2')

# ======================= Figure 3: alert yield vs baseline =======================
vals = []
for r in RULES:
    ppv, base, rr, n, h = stats(dd, r, 'oc'); ci = boot(dd, r, 'oc', B=2000, seed=1)
    vals.append(dict(rule=r, PPV=ppv * 100, lo=ci[0][0] * 100, hi=ci[1][0] * 100, base=base * 100, new=n, followed=h))
v3 = pd.DataFrame(vals); v3.to_csv(os.path.join(RESULTS, 'fig3_values.csv'), index=False)
fig, ax = plt.subplots(figsize=(6.0, 2.5))
for k, row in v3.iterrows():
    y = len(RULES) - 1 - k; r = row.rule
    ax.plot([row.lo, row.hi], [y, y], color=COL[r], lw=1.8, solid_capstyle='round')
    ax.plot(row.PPV, y, MK[r], color=COL[r], ms=6, mec='white', mew=0.6, zorder=5)
    ax.plot([row.base, row.base], [y - 0.24, y + 0.24], color=INK, lw=1.2, zorder=4)
    ax.text(1.03, y, f'{int(row.followed)} / {int(row.new):,}', transform=ax.get_yaxis_transform(),
            va='center', ha='left', fontsize=7, color=INK)
ax.text(1.03, len(RULES) - 0.5, 'Followed /\nnew alerts', transform=ax.get_yaxis_transform(),
        va='bottom', ha='left', fontsize=6.6, color=MUTED, linespacing=1.1)
ax.axhline(0.5, color='#BBBBBB', lw=0.6)
ax.set_yticks(range(len(RULES))); ax.set_yticklabels([LAB[r] for r in RULES][::-1]); ax.tick_params(axis='y', length=0)
ax.set_xlim(-0.05, 2.6); ax.set_ylim(-0.55, len(RULES) - 0.3); ax.grid(axis='y', visible=False)
ax.set_xlabel('New alerts followed by an injury report within 7 days (%)')
ax.legend(handles=[Line2D([0], [0], color=MUTED, marker='o', lw=1.8, ms=5, mec='white', label='Alerts (95% CI)'),
                   Line2D([0], [0], color=INK, lw=1.2, marker='|', ms=9, ls='none', label='Baseline: any monitored day')],
          loc='lower center', bbox_to_anchor=(0.45, 1.0), ncol=2, frameon=False)
save(fig, 'Figure3')

# ======================= Figure 4: threshold sensitivity =======================
wl = dd.weekly_load.where(dd.weekly_load > 0)
dd['spike_ratio'] = wl / dd.groupby('player').weekly_load.shift(7).where(lambda s: s > 0) - 1
GRID = {'acwr': ('ACWR', 'acwr', [1.3, 1.5, 2.0], '>', lambda x, t: x > t),
        'spike': ('Weekly load change', 'spike_ratio', [0.10, 0.15, 0.30], '>', lambda x, t: x > t),
        'well': ('Wellness z-score', 'well_z', [-1.0, -1.5, -2.0], '≤', lambda x, t: x <= t),
        'mono': ('Training monotony', 'monotony', [1.5, 2.0, 2.5], '>', lambda x, t: x > t)}
sens = []
for r, (name, col, thr, sym, f) in GRID.items():
    e = dd['elig_' + r]
    for t in thr:
        a = e & f(dd[col], t)
        prev = a.groupby(dd.player).shift(1, fill_value=False).astype(bool)
        new = a & ~prev
        pw = new[e].groupby([dd.player[e], dd.week[e]]).sum().mean()
        k, n = int(dd.oc[new].sum()), int(new.sum()); lo, hi = wilson(k, n)
        lab = (f'{t*100:.0f}%' if r == 'spike' else f'{t:g}'.replace('-', '−'))
        sens.append(dict(rule=r, threshold=t, label=f'{sym} {lab}', new=n, followed=k, alerts_pw=pw,
                         PPV=k / n * 100, lo=lo * 100, hi=hi * 100, base=dd.oc[e].mean() * 100))
sens = pd.DataFrame(sens); sens.to_csv(os.path.join(RESULTS, 'fig4_threshold_values.csv'), index=False)

fig, axes = plt.subplots(1, 4, figsize=(6.85, 2.6), sharey=True, gridspec_kw=dict(wspace=0.10))
for ax, (r, (name, *_)) in zip(axes, GRID.items()):
    s = sens[sens.rule == r].reset_index(drop=True)
    x = np.arange(len(s))
    ax.axhline(s.base.iloc[0], color=INK, lw=0.8, ls=(0, (3, 2)), zorder=1)
    ax.vlines(x, s.lo, s.hi, color=COL[r], lw=1.4, zorder=2)
    ax.plot(x, s.PPV, MK[r], color=COL[r], ms=4.5, mec=INK, mew=0.5, ls='none', zorder=3, clip_on=False)
    ax.set_xticks(x)
    ax.set_xticklabels([f'{l}\n{k}/{n}' for l, k, n in zip(s.label, s.followed, s.new)], linespacing=1.5)
    for t in ax.get_xticklabels(): t.set_fontsize(6.3)
    ax.set_xlim(-0.55, len(s) - 0.45); ax.set_ylim(0, 7)
    ax.set_title(name, fontsize=7.5, fontweight='bold', color=COL[r])
    ax.grid(axis='x', visible=False); ax.tick_params(axis='x', length=0, pad=2)
axes[0].set_ylabel('Alerts followed by injury (%, 95% CI)')
fig.supxlabel('Alert threshold, stricter to the right (second line: followed / new alerts)', fontsize=7.5, y=-0.10)
axes[0].legend(handles=[Line2D([0], [0], color=INK, lw=0.8, ls=(0, (3, 2)), label='Baseline')],
                loc='upper right', frameon=False)
save(fig, 'Figure4')
print(v3.round(2).to_string(index=False)); print(sens.round(2).to_string(index=False))
