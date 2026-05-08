"""
GitHub ingestion — repository counts per language via GitHub Search API.
Requires GITHUB_TOKEN in .env (classic PAT, no special scopes needed).
Generate at: https://github.com/settings/tokens
"""

import os
import time
import json
import pandas as pd
import requests
from datetime import date
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
OUTPUT_PATH  = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw', 'github', 'github_repos.csv')

LANGUAGES = [
    'Python', 'JavaScript', 'TypeScript', 'Java', 'C#', 'C++',
    'Go', 'Rust', 'PHP', 'Ruby', 'Swift', 'Kotlin', 'R', 'Scala',
    'Perl', 'Assembly'
]

# GitHub search API uses specific language names for some
LANGUAGE_ALIASES = {
    'C#':       'C%23',
    'C++':      'C%2B%2B',
    'Assembly': 'Assembly',
}


def fetch_repo_count(language: str) -> dict:
    encoded = LANGUAGE_ALIASES.get(language, language.replace(' ', '+'))
    url = f'https://api.github.com/search/repositories?q=language:{encoded}&per_page=1'

    headers = {'Accept': 'application/vnd.github+json'}
    if GITHUB_TOKEN:
        headers['Authorization'] = f'Bearer {GITHUB_TOKEN}'

    r = requests.get(url, headers=headers, timeout=15)

    if r.status_code == 403:
        reset = int(r.headers.get('X-RateLimit-Reset', 0))
        wait  = max(reset - int(time.time()), 0) + 2
        print(f'  Rate limited — waiting {wait}s')
        time.sleep(wait)
        return fetch_repo_count(language)

    r.raise_for_status()
    data = r.json()
    return {
        'language':     language.lower(),
        'metric_value': data.get('total_count', 0),
        'source':       'github_repos',
        'date':         str(date.today()),
    }


def run():
    if not GITHUB_TOKEN:
        print('WARNING: No GITHUB_TOKEN found — requests are rate-limited to 10/min.')
        print('Generate a PAT at https://github.com/settings/tokens and add it to .env')

    rows = []
    for lang in LANGUAGES:
        print(f'  Fetching GitHub repo count: {lang}')
        try:
            rows.append(fetch_repo_count(lang))
        except Exception as e:
            print(f'  Error for {lang}: {e}')
        time.sleep(1.2)  # stay well under rate limit

    df = pd.DataFrame(rows)
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)
    print(f'\nSaved {len(df)} rows → {OUTPUT_PATH}')
    print(df.sort_values('metric_value', ascending=False).to_string(index=False))


if __name__ == '__main__':
    run()
