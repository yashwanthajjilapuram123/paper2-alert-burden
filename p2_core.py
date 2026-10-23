"""Shared functions for Paper 2: loading the player-day panel, injury episodes,
monitored onsets, the 7-day outcome, alert yield (PPV), baseline, risk ratio and
the player-cluster bootstrap."""
import os
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, 'results'); os.makedirs(RESULTS, exist_ok=True)
R = {'acwr': 'ACWR > 1.5', 'spike': 'Weekly load +15%', 'well': 'Wellness z ≤ −1.5',
     'mono': 'Monotony > 2.0', 'any': 'Any rule'}


def load():
    """One row per player per day (50 players x 731 days)."""
    d = pd.read_csv(os.path.join(HERE, 'data', 'player_day_alerts.csv'), parse_dates=['date'])
    for c in d.columns:
        if c.startswith(('elig_', 'alert_', 'new_', 'onset_', 'inj_next', 'major_next')):
            d[c] = d[c].astype(bool)
    return d.sort_values(['player', 'date']).reset_index(drop=True)


def episodes(dd, gap=7):
    """Group injury reports into episodes: a new episode starts when more than `gap`
    days have passed since the player's previous report. Returns onset days."""
    rep = dd[dd.inj_report > 0][['player', 'date']].copy()
    rep['g'] = rep.groupby('player').date.diff().dt.days
    rep['new'] = rep.g.isna() | (rep.g > gap)
    return rep[rep.new][['player', 'date']].reset_index(drop=True)


def monitored_onsets(dd, ons, min_days=3):
    """Keep onsets with at least `min_days` eligible (monitored) days in the previous 7 days."""
    keep = []
    for _, r in ons.iterrows():
        w = dd[(dd.player == r.player) & (dd.date < r.date) & (dd.date >= r.date - pd.Timedelta(days=7))]
        if w.elig_any.sum() >= min_days:
            keep.append(r)
    return pd.DataFrame(keep, columns=['player', 'date']).reset_index(drop=True)


def add_next7(dd, ons, col):
    """col = True if an onset occurs on days t+1 to t+7 for that player."""
    s = set(zip(ons.player, ons.date))
    dd['_on'] = [(p, t) in s for p, t in zip(dd.player, dd.date)]

    def f7(x):
        a = x.values.astype(int); n = len(a); c = np.concatenate([[0], np.cumsum(a)])
        idx = np.arange(n)
        return pd.Series((c[np.minimum(idx + 8, n)] - c[idx + 1]) > 0, index=x.index)

    dd[col] = dd.groupby('player')['_on'].transform(f7)
    return dd.drop(columns='_on')


def stats(dd, r, oc):
    """PPV of new alerts, baseline on eligible days, risk ratio (alert vs non-alert days),
    number of new alerts and number followed by an onset."""
    e = dd[dd['elig_' + r]]; nw = e[e['new_' + r]]
    ppv = nw[oc].mean(); base = e[oc].mean()
    a = e[e['alert_' + r]][oc].mean(); n = e[~e['alert_' + r]][oc].mean()
    return ppv, base, (a / n if n > 0 else np.nan), len(nw), int(nw[oc].sum())


def boot(dd, r, oc, B=2000, seed=1):
    """Player-cluster bootstrap: 2.5th and 97.5th percentiles of (PPV, baseline, RR)."""
    rng = np.random.default_rng(seed); P = dd.player.unique()
    by = {p: g for p, g in dd.groupby('player')}
    out = []
    for _ in range(B):
        s = pd.concat([by[p] for p in rng.choice(P, len(P))])
        out.append(stats(s, r, oc)[:3])
    return np.nanpercentile(np.array(out, float), [2.5, 97.5], axis=0)


def primary():
    """Panel with the primary outcome column 'oc' (monitored onsets, episode gap 7 days)."""
    d = load()
    mon = monitored_onsets(d, episodes(d, 7))
    return add_next7(d, mon, 'oc'), mon
