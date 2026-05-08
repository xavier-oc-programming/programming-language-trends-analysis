"""
Adzuna ingestion — job listing counts per language across multiple countries.
Requires ADZUNA_APP_ID and ADZUNA_APP_KEY in .env.
"""

import os
import time
import pandas as pd
import requests
from datetime import date
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

APP_ID  = os.getenv('ADZUNA_APP_ID')
APP_KEY = os.getenv('ADZUNA_APP_KEY')
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw', 'adzuna', 'adzuna_jobs.csv')

COUNTRIES = ['gb', 'us', 'de', 'fr', 'es']

LANGUAGES = [
    'Python', 'JavaScript', 'TypeScript', 'Java', 'C#', 'C++',
    'Go', 'Rust', 'PHP', 'Ruby', 'Swift', 'Kotlin', 'R', 'Scala',
    'Perl', 'Assembly'
]

SEARCH_TERMS = {
    'python':     'python developer',
    'javascript': 'javascript developer',
    'typescript': 'typescript developer',
    'java':       'java developer',
    'c#':         'c# dotnet developer',
    'c++':        'c++ developer',
    'go':         'golang developer',
    'rust':       'rust developer',
    'php':        'php developer',
    'ruby':       'ruby rails developer',
    'swift':      'swift ios developer',
    'kotlin':     'kotlin android developer',
    'r':          'r statistics data science',
    'scala':      'scala developer',
    'perl':       'perl developer',
    'assembly':   'assembly programmer',
}


def fetch_job_count(language: str, country: str) -> int | None:
    term = SEARCH_TERMS.get(language.lower(), f'{language.lower()} developer')
    url = (
        f'https://api.adzuna.com/v1/api/jobs/{country}/search/1'
        f'?app_id={APP_ID}&app_key={APP_KEY}'
        f'&what={requests.utils.quote(term)}&results_per_page=1'
    )
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.json().get('count', 0)
    except Exception as e:
        print(f'  Error {language}/{country}: {e}')
        return None


def run():
    if not APP_ID or not APP_KEY:
        print('ERROR: ADZUNA_APP_ID and ADZUNA_APP_KEY required in .env')
        return

    rows = []
    today = str(date.today())

    for country in COUNTRIES:
        print(f'\nFetching Adzuna jobs — country: {country}')
        for lang in LANGUAGES:
            count = fetch_job_count(lang, country)
            if count is not None:
                rows.append({
                    'language':     lang.lower(),
                    'metric_value': count,
                    'source':       f'adzuna_{country}',
                    'date':         today,
                })
                print(f'  {lang:<14} {count:>8,} jobs')
            time.sleep(0.5)

    df = pd.DataFrame(rows)

    # Aggregate across countries into a single score per language
    agg = (
        df.groupby('language')['metric_value']
          .sum()
          .reset_index()
          .assign(source='adzuna_total', date=today)
    )

    combined = pd.concat([df, agg], ignore_index=True)
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    combined.to_csv(OUTPUT_PATH, index=False)
    print(f'\nSaved {len(combined)} rows → {OUTPUT_PATH}')


if __name__ == '__main__':
    run()
