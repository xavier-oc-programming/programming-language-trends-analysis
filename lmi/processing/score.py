"""
Scoring — applies configurable weights to normalised scores to produce
the composite Language Market Index.

Default weights (must sum to 1.0):
  adzuna_total:    0.35  — what the market is paying for
  github_repos:    0.30  — what developers are actually building
  so_survey_usage: 0.25  — what developers say they use
  tiobe_rating:    0.10  — industry recognition index

Outputs data/processed/index.csv with composite score and lifecycle stage.
"""

import os
import pandas as pd
import numpy as np
from datetime import date

NORMALIZED_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'processed', 'normalized.csv')
OUT_PATH        = os.path.join(os.path.dirname(__file__), '..', 'data', 'processed', 'index.csv')

DEFAULT_WEIGHTS = {
    'adzuna_total':    0.35,
    'github_repos':    0.30,
    'so_survey_usage': 0.25,
    'tiobe_rating':    0.10,
}

LANGUAGES = [
    'python', 'javascript', 'typescript', 'java', 'c#', 'c++',
    'go', 'rust', 'php', 'ruby', 'swift', 'kotlin', 'r', 'scala',
    'perl', 'assembly'
]


def classify_lifecycle(score: float, trend: float | None = None) -> str:
    """
    Rising:   composite > 60 and trending up
    Dominant: composite > 60 and stable
    Declining: composite trending down > 10% year over year
    Niche:    composite < 30 regardless of trend
    """
    if score < 30:
        return 'Niche'
    if trend is not None and trend < -10:
        return 'Declining'
    if score > 60 and (trend is None or trend >= 0):
        return 'Dominant'
    if score > 60 and trend is not None and trend > 0:
        return 'Rising'
    if score > 40:
        return 'Mature'
    return 'Declining'


def compute_index(weights: dict = None) -> pd.DataFrame:
    if weights is None:
        weights = DEFAULT_WEIGHTS

    total_weight = sum(weights.values())
    if abs(total_weight - 1.0) > 0.01:
        raise ValueError(f'Weights must sum to 1.0, got {total_weight:.3f}')

    if not os.path.exists(NORMALIZED_PATH):
        raise FileNotFoundError(f'Run normalize.py first: {NORMALIZED_PATH}')

    norm = pd.read_csv(NORMALIZED_PATH)
    pivot = norm.pivot(index='language', columns='source', values='normalized_score').fillna(0)
    pivot = pivot.reindex(LANGUAGES, fill_value=0)

    scores = pd.Series(0.0, index=LANGUAGES)
    breakdown = {}

    for source, weight in weights.items():
        if source in pivot.columns:
            col = pivot[source]
            scores += col * weight
            breakdown[source] = (col * weight).round(2)
        else:
            print(f'  WARNING: source "{source}" not in normalized data — skipping')

    result = pd.DataFrame({
        'language':        LANGUAGES,
        'composite_score': scores.values.round(2),
        'lifecycle':       [classify_lifecycle(s) for s in scores.values],
        'date':            str(date.today()),
    })

    for source in DEFAULT_WEIGHTS:
        result[f'score_{source}'] = breakdown.get(source, pd.Series(0.0, index=range(len(LANGUAGES)))).values

    result = result.sort_values('composite_score', ascending=False).reset_index(drop=True)
    result['rank'] = result.index + 1

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    result.to_csv(OUT_PATH, index=False)
    return result


def run(weights: dict = None):
    print('Computing Language Market Index...')
    result = compute_index(weights)
    print(f'\nSaved → {OUT_PATH}\n')
    print(result[['rank', 'language', 'composite_score', 'lifecycle']].to_string(index=False))
    return result


if __name__ == '__main__':
    run()
