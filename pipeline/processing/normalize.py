"""
Normalisation — min-max scales each source to 0–100 per language.
Reads raw CSVs from data/raw/, outputs data/processed/normalized.csv
"""

import os
import pandas as pd
import numpy as np

RAW_DIR   = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'raw')
OUT_PATH  = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'processed', 'normalized.csv')

SOURCES = {
    'github_octoverse': os.path.join(RAW_DIR, 'github',   'github_octoverse.csv'),
    'adzuna_total':     os.path.join(RAW_DIR, 'adzuna',   'adzuna_jobs.csv'),
    'so_survey_usage':  os.path.join(RAW_DIR, 'so_survey','so_survey_parsed.csv'),
    'tiobe_rating':     os.path.join(RAW_DIR, 'tiobe',    'tiobe_ratings.csv'),
}

LANGUAGES = [
    'python', 'javascript', 'typescript', 'java', 'c#', 'c++',
    'go', 'rust', 'php', 'ruby', 'swift', 'kotlin', 'r', 'scala',
    'perl', 'assembly'
]


def min_max_scale(series: pd.Series) -> pd.Series:
    lo, hi = series.min(), series.max()
    # If every value is identical there is no spread to scale, so return 50 for all
    if hi == lo:
        return pd.Series(50.0, index=series.index)
    # Stretch the range so the lowest language scores 0 and the highest scores 100
    return (series - lo) / (hi - lo) * 100


def load_source(source_key: str, filepath: str) -> pd.Series | None:
    if not os.path.exists(filepath):
        print(f'  MISSING: {filepath}')
        return None

    df = pd.read_csv(filepath)
    subset = df[df['source'] == source_key].copy()

    if subset.empty:
        # SO survey CSV contains both 'so_survey_usage' and 'so_survey_desired' rows —
        # fall back to the most recent year if a direct key match returns nothing
        if 'so_survey' in source_key:
            df['date'] = pd.to_datetime(df['date'])
            latest = df['date'].max()
            subset = df[(df['date'] == latest) & (df['source'] == 'so_survey_usage')]

    if subset.empty:
        print(f'  No rows for source={source_key}')
        return None

    # When a source has multiple snapshots (e.g. quarterly GitHub data), only keep the latest
    if 'date' in subset.columns:
        subset['date'] = pd.to_datetime(subset['date'])
        latest = subset['date'].max()
        subset = subset[subset['date'] == latest]

    # Average across any duplicate language rows, then fill missing languages with 0
    series = (
        subset.groupby('language')['metric_value']
              .mean()
              .reindex(LANGUAGES, fill_value=0)
    )
    return series


def run():
    rows = []
    for source_key, filepath in SOURCES.items():
        print(f'Loading {source_key}...')
        raw = load_source(source_key, filepath)
        if raw is None:
            continue

        # Scale raw values to 0–100 so different units (job counts vs % usage) are comparable
        scaled = min_max_scale(raw)
        for lang in LANGUAGES:
            rows.append({
                'language':         lang,
                'source':           source_key,
                'raw_value':        round(float(raw.get(lang, 0)), 4),
                'normalized_score': round(float(scaled.get(lang, 0)), 2),
            })

    df = pd.DataFrame(rows)
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    df.to_csv(OUT_PATH, index=False)
    print(f'\nSaved {len(df)} rows → {OUT_PATH}')
    return df


if __name__ == '__main__':
    run()
