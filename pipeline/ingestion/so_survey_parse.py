"""
Stack Overflow Developer Survey ingestion.
Download CSVs from https://survey.stackoverflow.co and place in:
  lmi/data/raw/so_survey/survey_YYYY.csv

Supported years: 2019–2024.
Column names changed across years — this script handles the differences.
"""

import os
import re
import pandas as pd

from pathlib import Path

SURVEY_DIR  = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'raw', 'so_survey')
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'raw', 'so_survey', 'so_survey_parsed.csv')

LANGUAGES = [
    'python', 'javascript', 'typescript', 'java', 'c#', 'c++',
    'go', 'rust', 'php', 'ruby', 'swift', 'kotlin', 'r', 'scala',
    'perl', 'assembly'
]

# Column name variations across survey years
HAVE_WORKED_COLS = [
    'LanguageHaveWorkedWith',   # 2021–2024
    'LanguageWorkedWith',       # 2019–2020
]
WANT_TO_WORK_COLS = [
    'LanguageWantToWorkWith',   # 2021–2024
    'LanguageDesireNextYear',   # 2019–2020
]


def find_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for col in candidates:
        if col in df.columns:
            return col
    return None


def language_pct(series: pd.Series, language: str) -> float:
    """% of respondents who listed this language (semicolon-separated values).
    Uses exact token matching to avoid 'r' matching inside 'JavaScript' etc."""
    total = series.dropna().shape[0]
    if total == 0:
        return 0.0
    lang_lower = language.lower()
    # Split each respondent's answer on ';' and check for an exact match
    # (prevents short names like 'r' or 'c' matching inside longer language names)
    def row_matches(x):
        tokens = [t.strip().lower() for t in str(x).split(';')]
        return lang_lower in tokens
    count = series.dropna().apply(row_matches).sum()
    return round(count / total * 100, 2)


def parse_survey(filepath: str, year: int) -> pd.DataFrame:
    print(f'  Parsing {year}...')
    df = pd.read_csv(filepath, low_memory=False)

    # Column names changed between survey years — try each known variant
    have_col = find_col(df, HAVE_WORKED_COLS)
    want_col = find_col(df, WANT_TO_WORK_COLS)

    if not have_col:
        print(f'    WARNING: no "have worked" column found for {year} — skipping')
        return pd.DataFrame()

    rows = []
    for lang in LANGUAGES:
        have_pct = language_pct(df[have_col], lang)
        want_pct = language_pct(df[want_col], lang) if want_col else None

        # 'usage' = languages respondents worked with this year (what we score on)
        rows.append({
            'language':     lang,
            'metric_value': have_pct,
            'source':       'so_survey_usage',
            'date':         f'{year}-01-01',
        })
        # 'desired' = languages they want to use next year (stored but not used in composite)
        if want_pct is not None:
            rows.append({
                'language':     lang,
                'metric_value': want_pct,
                'source':       'so_survey_desired',
                'date':         f'{year}-01-01',
            })

    return pd.DataFrame(rows)


def run():
    survey_dir = Path(SURVEY_DIR)
    csv_files  = sorted(survey_dir.glob('survey_*.csv'))

    if not csv_files:
        print(f'No survey CSVs found in {SURVEY_DIR}')
        print('Download from https://survey.stackoverflow.co and save as survey_YYYY.csv')
        return

    frames = []
    for path in csv_files:
        year_match = re.search(r'(\d{4})', path.name)
        if not year_match:
            continue
        year = int(year_match.group(1))
        frames.append(parse_survey(str(path), year))

    if not frames:
        print('No data parsed.')
        return

    result = pd.concat(frames, ignore_index=True)
    result.to_csv(OUTPUT_PATH, index=False)
    print(f'\nSaved {len(result)} rows → {OUTPUT_PATH}')
    print(result[result['source'] == 'so_survey_usage']
          .sort_values(['date', 'metric_value'], ascending=[True, False])
          .to_string(index=False))


if __name__ == '__main__':
    run()
