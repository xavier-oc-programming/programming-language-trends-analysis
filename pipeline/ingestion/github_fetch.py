"""
GitHub Octoverse ingestion — developer activity per language, quarterly from 2020.
Source: github.com/github/innovationgraph (public, no auth required)
Metric: num_pushers — number of developers who pushed code in that language globally.
"""

import os
import io
import pandas as pd
import requests

OCTOVERSE_URL = 'https://raw.githubusercontent.com/github/innovationgraph/main/data/languages.csv'
OUTPUT_PATH   = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'raw', 'github', 'github_octoverse.csv')

LANGUAGES = {
    'python', 'javascript', 'typescript', 'java', 'c#', 'c++',
    'go', 'rust', 'php', 'ruby', 'swift', 'kotlin', 'r', 'scala',
    'perl', 'assembly'
}

# Octoverse uses title-case names; map to our lowercase keys
OCTOVERSE_NAME_MAP = {
    'Python':     'python',
    'JavaScript': 'javascript',
    'TypeScript': 'typescript',
    'Java':       'java',
    'C#':         'c#',
    'C++':        'c++',
    'Go':         'go',
    'Rust':       'rust',
    'PHP':        'php',
    'Ruby':       'ruby',
    'Swift':      'swift',
    'Kotlin':     'kotlin',
    'R':          'r',
    'Scala':      'scala',
    'Perl':       'perl',
    'Assembly':   'assembly',
}


def run():
    print(f'Downloading Octoverse language data from GitHub...')
    r = requests.get(OCTOVERSE_URL, timeout=30)
    r.raise_for_status()

    df = pd.read_csv(io.StringIO(r.text))

    # Map Octoverse's title-case names to our lowercase keys, then drop non-tracked languages
    df['language_lower'] = df['language'].map(OCTOVERSE_NAME_MAP)
    df = df[
        (df['language_type'] == 'programming') &
        (df['language_lower'].isin(LANGUAGES))
    ].copy()

    # Octoverse breaks counts down by country — sum globally so one row per language per quarter
    global_df = (
        df.groupby(['language_lower', 'year', 'quarter'], as_index=False)['num_pushers']
          .sum()
    )

    # Convert year + quarter number to a first-of-month date string (Q1=Jan, Q2=Apr, Q3=Jul, Q4=Oct)
    global_df['date'] = global_df.apply(
        lambda r: f"{int(r['year'])}-{int(r['quarter']) * 3 - 2:02d}-01", axis=1
    )

    output = global_df.rename(columns={
        'language_lower': 'language',
        'num_pushers':    'metric_value',
    })[['language', 'metric_value', 'date']].copy()
    output['source'] = 'github_octoverse'

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    output.to_csv(OUTPUT_PATH, index=False)

    # Print a quick sanity-check snapshot of the most recent quarter
    latest = output.sort_values('date').groupby('language').last().reset_index()
    latest = latest.sort_values('metric_value', ascending=False)

    print(f'\nLatest quarter snapshot ({latest["date"].iloc[0]}):')
    print(latest[['language', 'metric_value']].to_string(index=False))
    print(f'\nSaved {len(output)} rows ({output["date"].nunique()} quarters) → {OUTPUT_PATH}')


if __name__ == '__main__':
    run()
