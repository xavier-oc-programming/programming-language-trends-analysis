"""
TIOBE Index ingestion — scrapes the top-50 table from tiobe.com.
No authentication required. Run monthly; results are cached by date.

Note: tiobe.com frequently blocks automated requests (SSL/TLS termination at their WAF).
When scraping fails, falls back to FALLBACK_RATINGS (sourced manually, May 2026).
"""

import os
import re
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import date

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'raw', 'tiobe', 'tiobe_ratings.csv')

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

# Manually sourced from tiobe.com — May 2026
# Used as fallback when the live scrape is blocked by the site's WAF/SSL termination
FALLBACK_RATINGS = {
    'python':     23.84,
    'c':          12.34,
    'java':        9.02,
    'c++':         8.03,
    'c#':          5.98,
    'javascript':  3.49,
    'go':          2.52,
    'rust':        1.47,
    'typescript':  1.42,
    'php':         1.38,
    'swift':       1.05,
    'kotlin':      0.93,
    'assembly':    0.89,
    'ruby':        0.72,
    'r':           0.54,
    'scala':       0.41,
    'perl':        0.38,
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

    # Try to find the ratings table by header text first, then fall back to largest table
    table = None
    for t in soup.find_all('table'):
        headers = [th.get_text(strip=True).lower() for th in t.find_all('th')]
        if any('rating' in h for h in headers):
            table = t
            break

    if not table:
        # Secondary heuristic: the main table has many rows (one per language)
        for t in soup.find_all('table'):
            rows = t.find_all('tr')
            if len(rows) > 10:
                table = t
                break

    if not table:
        raise ValueError('Could not locate TIOBE ratings table — site structure may have changed.')

    rows = []
    today = str(date.today())

    for tr in table.find_all('tr')[1:]:  # skip the header row
        cells = [td.get_text(strip=True) for td in tr.find_all('td')]
        if len(cells) < 4:
            continue

        # Walk cells left-to-right: first text-only cell is the language name,
        # first cell containing '%' after that is the rating percentage
        lang_raw = None
        rating_str = None
        for i, cell in enumerate(cells):
            cleaned = re.sub(r'[^0-9.]', '', cell)
            if lang_raw is None and re.search(r'[a-zA-Z]', cell) and '%' not in cell:
                lang_raw = cell
            elif lang_raw is not None and rating_str is None and '%' in cell:
                rating_str = cleaned

        if not lang_raw or not rating_str:
            continue

        # Normalise language names (e.g. "Assembly Language" → "assembly")
        lang = LANGUAGE_MAP.get(lang_raw.lower(), lang_raw.lower())

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


def build_from_fallback() -> pd.DataFrame:
    today = str(date.today())
    rows = [
        {'language': lang, 'metric_value': rating, 'source': 'tiobe_rating', 'date': today}
        for lang, rating in FALLBACK_RATINGS.items()
    ]
    df = pd.DataFrame(rows)
    print('  Using hardcoded fallback ratings (tiobe.com blocked live scrape)')
    print(df.sort_values('metric_value', ascending=False).to_string(index=False))
    return df


def run():
    tracked = None

    try:
        rows = scrape_tiobe()
        df = pd.DataFrame(rows)
        tracked = df[df['language'].isin(LANGUAGES_WE_TRACK)].copy()

        # If any high-profile language is missing, the scrape probably returned garbage — use fallback
        key_languages = {'python', 'java', 'c#', 'c++', 'javascript'}
        missing_key = key_languages - set(tracked['language'])
        if missing_key:
            raise ValueError(f'Key languages missing from scrape: {sorted(missing_key)} — using fallback')

        print(f'\nTracked languages found ({len(tracked)}):')
        print(tracked.sort_values('metric_value', ascending=False).to_string(index=False))

    except Exception as e:
        print(f'Scrape failed: {e}')
        print('Falling back to hardcoded ratings...')
        tracked = build_from_fallback()

    # Languages not in the TIOBE top-50 get a 0 so they still appear in the output
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
