import os
import pandas as pd
import numpy as np
import requests

DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'QueryResults.csv')


def load_pivot():
    df = pd.read_csv(DATA_PATH)
    df.columns = ['DATE', 'TAG', 'POSTS']
    df['DATE'] = pd.to_datetime(df['DATE'])
    pivot = df.pivot(index='DATE', columns='TAG', values='POSTS').fillna(0)
    return pivot


def compute_share_pivot(pivot):
    """Convert raw post counts to each language's % share of total monthly posts.
    This removes the platform-wide decline effect (SO usage dropped after ~2020)
    and shows which languages are gaining or losing ground relative to each other."""
    row_totals = pivot.sum(axis=1).replace(0, np.nan)
    return pivot.div(row_totals, axis=0) * 100


def compute_momentum(pivot, window=24):
    share = compute_share_pivot(pivot)
    scores = {}
    for lang in share.columns:
        series = share[lang]
        recent = series.iloc[-window:].mean()
        prior  = series.iloc[-window * 2:-window].mean()
        scores[lang] = round((recent - prior) / prior * 100, 1) if prior else None
    return pd.Series(scores, name='Momentum (%)').dropna().sort_values(ascending=False)


def classify_lifecycle(lang, total_posts, momentum_score, volume_threshold):
    vol = total_posts[lang]
    mom = momentum_score
    high = vol >= volume_threshold

    if mom > 20:
        return 'Rising'
    elif mom >= 0 and high:
        return 'Dominant'
    elif mom >= -20 and high:
        return 'Mature'
    elif mom < -20:
        return 'Declining'
    else:
        return 'Niche'


def build_strategy_table(pivot):
    scores      = compute_momentum(pivot)
    total_posts = pivot.sum()
    threshold   = total_posts.median()

    rows = []
    for lang in scores.index:
        lc = classify_lifecycle(lang, total_posts, scores[lang], threshold)
        rows.append({
            'language':    lang,
            'momentum':    scores[lang],
            'total_posts': int(total_posts[lang]),
            'lifecycle':   lc,
        })
    return pd.DataFrame(rows).set_index('language')


SEARCH_TERMS = {
    'python':     'python developer',
    'javascript': 'javascript developer',
    'java':       'java developer',
    'c#':         'c# developer',
    'php':        'php developer',
    'c++':        'c++ developer',
    'r':          'r data science',
    'swift':      'swift ios developer',
    'go':         'golang developer',
    'ruby':       'ruby developer',
    'perl':       'perl developer',
    'c':          'c systems developer',
    'assembly':   'assembly programmer',
    'delphi':     'delphi developer',
}


def fetch_job_count(lang, app_id, app_key, country='gb'):
    term = SEARCH_TERMS.get(lang, f'{lang} developer')
    url = (
        f'https://api.adzuna.com/v1/api/jobs/{country}/search/1'
        f'?app_id={app_id}&app_key={app_key}'
        f'&what={requests.utils.quote(term)}&results_per_page=1'
    )
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.json().get('count', 0)
    except Exception:
        return None
