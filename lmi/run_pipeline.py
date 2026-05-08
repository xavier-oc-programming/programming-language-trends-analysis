"""
Pipeline orchestrator — runs all ingestion and processing steps in sequence.

Usage:
    python run_pipeline.py              # run everything
    python run_pipeline.py --skip-tiobe # skip scraping (use cached data)
    python run_pipeline.py --only-score # re-score without re-fetching
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from ingestion import github_fetch, adzuna_fetch, so_survey_parse, tiobe_scrape
from processing import normalize, score


def run(skip_github=False, skip_adzuna=False, skip_tiobe=False,
        skip_so=False, only_score=False):

    if not only_score:
        if not skip_github:
            print('\n── GitHub ─────────────────────────────')
            github_fetch.run()

        if not skip_adzuna:
            print('\n── Adzuna ─────────────────────────────')
            adzuna_fetch.run()

        if not skip_so:
            print('\n── Stack Overflow Survey ───────────────')
            so_survey_parse.run()

        if not skip_tiobe:
            print('\n── TIOBE ───────────────────────────────')
            tiobe_scrape.run()

    print('\n── Normalise ───────────────────────────')
    normalize.run()

    print('\n── Score ───────────────────────────────')
    result = score.run()

    print('\n── Done ────────────────────────────────')
    print(f'Index computed for {len(result)} languages.')
    return result


if __name__ == '__main__':
    args = sys.argv[1:]
    run(
        skip_github=('--skip-github' in args),
        skip_adzuna=('--skip-adzuna' in args),
        skip_tiobe= ('--skip-tiobe'  in args),
        skip_so=    ('--skip-so'     in args),
        only_score= ('--only-score'  in args),
    )
