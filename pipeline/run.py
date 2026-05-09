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
    # Skip all fetching and just re-run the scoring on whatever is already on disk
    if not only_score:
        if not skip_github:
            print('\n── GitHub ─────────────────────────────')
            github_fetch.run()        # downloads Octoverse CSV from GitHub

        if not skip_adzuna:
            print('\n── Adzuna ─────────────────────────────')
            adzuna_fetch.run()        # hits the Adzuna REST API for job counts

        if not skip_so:
            print('\n── Stack Overflow Survey ───────────────')
            so_survey_parse.run()     # reads locally-saved survey CSVs

        if not skip_tiobe:
            print('\n── TIOBE ───────────────────────────────')
            tiobe_scrape.run()        # scrapes tiobe.com, falls back to hardcoded if blocked

    print('\n── Normalise ───────────────────────────')
    normalize.run()   # min-max scales each source to 0–100 so they can be weighted together

    print('\n── Score ───────────────────────────────')
    result = score.run()   # applies weights, sums to composite, assigns lifecycle labels

    print('\n── Done ────────────────────────────────')
    print(f'Index computed for {len(result)} languages.')
    return result


if __name__ == '__main__':
    # Parse flags from the command line, e.g. python run.py --skip-tiobe --only-score
    args = sys.argv[1:]
    run(
        skip_github=('--skip-github' in args),
        skip_adzuna=('--skip-adzuna' in args),
        skip_tiobe= ('--skip-tiobe'  in args),
        skip_so=    ('--skip-so'     in args),
        only_score= ('--only-score'  in args),
    )
