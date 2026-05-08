"""
TIOBE Index ingestion — scrapes the top-50 table from tiobe.com.
No authentication required. Run monthly; results are cached by date.
"""

import os
import re
import time
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import date

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw', 'tiobe', 'tiobe_ratings.csv')

TIOBE_URL = 'https://www.tiobe.com/tiobe-index/'

LANGUAGE_MAP = {
    'visual basic': 'visual basic',
    'c++':          'c++',
    'c#':           'c#',
    'assembly language': 'assembly',
    'fortran':      'fortran',
}

LANGUAGES_WE_TRACK = {
    'python', 'javascript', 'typescript', 'java', 'c#', 'c++',
    'go', 'rust', 'php', 'ruby', 'swift', 'kotlin', 'r', 'scala',
    'perl', 'assembly', 'c'
}

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/124.0.0.0 Safari/537.36'
    )
}


def scrape_tiobe() -> list[dict]:
    print(f'Fetching {TIOBE_URL}')
    r = requests.get(TIOBE_URL, headers=HEADERS, timeout=20)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, 'html.parser')
    table = soup.find('table', {'id': 'VLTH'})

    if not table:
        # Fallback: find any table with a Ratings column
        for t in soup.find_all('table'):
            headers = [th.get_text(strip=True).lower() for th in t.find_all('th')]
            if 'ratings' in headers or 'rating' in headers:
                table = t
                break

    if not table:
        raise ValueError('Could not locate TIOBE ratings table — site structure may have changed.')

    rows = []
    today = str(date.today())

    for tr in table.find_all('tr')[1:]:  # skip header
        cells = [td.get_text(strip=True) for td in tr.find_all('td')]
        if len(cells) < 4:
            continue

        lang_raw = cells[4] if len(cells) > 4 else cells[2]
        lang = LANGUAGE_MAP.get(lang_raw.lower(), lang_raw.lower())

        rating_str = cells[5] if len(cells) > 5 else cells[3]
        rating_str = re.sub(r'[^0-9.]', '', rating_str)

        try:
            rating = float(rating_str)
        except ValueError:
            continue

        rows.append({
            'language':     lang,
            'metric_value': rating,
            'source':       'tiobe_rating',
            'date':         today,
        })

    return rows


def run():
    try:
        rows = scrape_tiobe()
    except Exception as e:
        print(f'Scrape failed: {e}')
        return

    df = pd.DataFrame(rows)

    # Keep only languages we track, plus flag unknowns
    tracked = df[df['language'].isin(LANGUAGES_WE_TRACK)].copy()
    untracked = df[~df['language'].isin(LANGUAGES_WE_TRACK)]

    print(f'\nTracked languages found ({len(tracked)}):')
    print(tracked.sort_values('metric_value', ascending=False).to_string(index=False))

    missing = LANGUAGES_WE_TRACK - set(tracked['language'])
    if missing:
        print(f'\nNot in TIOBE top-50 (will score as 0): {sorted(missing)}')
        for lang in missing:
            tracked = pd.concat([tracked, pd.DataFrame([{
                'language':     lang,
                'metric_value': 0.0,
                'source':       'tiobe_rating',
                'date':         str(date.today()),
            }])], ignore_index=True)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    tracked.to_csv(OUTPUT_PATH, index=False)
    print(f'\nSaved {len(tracked)} rows → {OUTPUT_PATH}')


if __name__ == '__main__':
    run()
