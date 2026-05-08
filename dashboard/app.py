import os
import sys
import pandas as pd
import numpy as np
from flask import Flask, render_template, jsonify, request
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'pipeline'))
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

from processing.score import compute_index, DEFAULT_WEIGHTS

app = Flask(__name__)

INDEX_PATH      = os.path.join(os.path.dirname(__file__), '..', 'data', 'processed', 'index.csv')
NORMALIZED_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'processed', 'normalized.csv')
SO_CSV_PATH     = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw', 'so', 'QueryResults.csv')

AI_INFLECTION = '2022-11-01'

LIFECYCLE_COLORS = {
    'Dominant':  '#5bc0f8',
    'Rising':    '#4ecb71',
    'Mature':    '#f0c040',
    'Declining': '#f07070',
    'Niche':     '#aaaaaa',
}

SOURCE_LABELS = {
    'adzuna_total':     'Job Postings',
    'github_octoverse': 'GitHub Octoverse',
    'so_survey_usage':  'Developer Survey',
    'tiobe_rating':     'TIOBE Index',
}


def load_index():
    if not os.path.exists(INDEX_PATH):
        return None
    return pd.read_csv(INDEX_PATH)


def load_normalized():
    if not os.path.exists(NORMALIZED_PATH):
        return None
    return pd.read_csv(NORMALIZED_PATH)


def load_so_pivot():
    df = pd.read_csv(SO_CSV_PATH)
    df.columns = ['DATE', 'TAG', 'POSTS']
    df['DATE'] = pd.to_datetime(df['DATE'])
    return df.pivot(index='DATE', columns='TAG', values='POSTS').fillna(0)


# ── Main page ────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    df = load_index()
    no_data = df is None

    table = []
    if not no_data:
        table = df[['rank', 'language', 'composite_score', 'lifecycle']].to_dict(orient='records')
        for row in table:
            row['composite_score'] = float(row['composite_score'])
            row['color'] = LIFECYCLE_COLORS.get(row['lifecycle'], '#fff')

    return render_template('index.html',
                           table=table,
                           weights=DEFAULT_WEIGHTS,
                           source_labels=SOURCE_LABELS,
                           no_data=no_data)


# ── LMI API ──────────────────────────────────────────────────────────────────

@app.route('/api/lmi/scores')
def lmi_scores():
    df = load_index()
    if df is None:
        return jsonify([])
    score_cols = [c for c in df.columns if c.startswith('score_')]
    result = []
    for _, row in df.iterrows():
        item = {
            'language':        row['language'],
            'composite_score': round(float(row['composite_score']), 2),
            'lifecycle':       row['lifecycle'],
            'color':           LIFECYCLE_COLORS.get(row['lifecycle'], '#fff'),
        }
        for col in score_cols:
            item[col] = round(float(row[col]), 2)
        result.append(item)
    return jsonify(result)


@app.route('/api/language/<lang>')
def language_detail(lang):
    df   = load_index()
    norm = load_normalized()

    if df is None:
        return jsonify({'error': 'No index data — run the pipeline first.'}), 404

    row = df[df['language'] == lang.lower()]
    if row.empty:
        return jsonify({'error': f'Language "{lang}" not found'}), 404

    row = row.iloc[0]
    breakdown = {}
    if norm is not None:
        for _, r in norm[norm['language'] == lang.lower()].iterrows():
            breakdown[r['source']] = {
                'raw':        round(float(r['raw_value']), 2),
                'normalized': round(float(r['normalized_score']), 2),
                'label':      SOURCE_LABELS.get(r['source'], r['source']),
            }

    return jsonify({
        'language':        lang.lower(),
        'rank':            int(row['rank']),
        'composite_score': round(float(row['composite_score']), 2),
        'lifecycle':       row['lifecycle'],
        'color':           LIFECYCLE_COLORS.get(row['lifecycle'], '#fff'),
        'breakdown':       breakdown,
    })


@app.route('/api/recalculate', methods=['POST'])
def recalculate():
    data = request.get_json()
    weights = {
        'adzuna_total':     float(data.get('adzuna_total',     0.35)),
        'github_octoverse': float(data.get('github_octoverse', 0.30)),
        'so_survey_usage':  float(data.get('so_survey_usage',  0.25)),
        'tiobe_rating':     float(data.get('tiobe_rating',     0.10)),
    }
    if abs(sum(weights.values()) - 1.0) > 0.05:
        return jsonify({'error': f'Weights must sum to 1.0'}), 400
    try:
        result = compute_index(weights)
        table = result[['rank', 'language', 'composite_score', 'lifecycle']].to_dict(orient='records')
        for row in table:
            row['composite_score'] = float(row['composite_score'])
            row['color'] = LIFECYCLE_COLORS.get(row['lifecycle'], '#fff')
        return jsonify({'table': table})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── SO Decline API ────────────────────────────────────────────────────────────

@app.route('/api/so/overview')
def so_overview():
    pivot = load_so_pivot()
    total = pivot.sum(axis=1)
    smoothed = total.rolling(window=6).mean().dropna()
    peak_date = smoothed.idxmax()
    return jsonify({
        'dates':          smoothed.index.strftime('%Y-%m-%d').tolist(),
        'values':         [round(float(v)) for v in smoothed],
        'ai_inflection':  AI_INFLECTION,
        'peak_date':      peak_date.strftime('%Y-%m-%d'),
        'peak_value':     round(float(smoothed.max())),
    })


@app.route('/api/so/impact')
def so_impact():
    pivot = load_so_pivot()
    ai = pd.Timestamp(AI_INFLECTION)
    pre  = pivot[pivot.index <  ai].iloc[-24:].mean()
    post = pivot[pivot.index >= ai].iloc[:24].mean()
    drop = ((post - pre) / pre * 100).round(1).sort_values()
    avg  = round(float(drop.mean()), 1)
    return jsonify({
        'languages': drop.index.tolist(),
        'values':    [float(v) for v in drop],
        'average':   avg,
        'ai_inflection': AI_INFLECTION,
    })


@app.route('/api/so/share')
def so_share():
    pivot = load_so_pivot()
    row_totals = pivot.sum(axis=1).replace(0, float('nan'))
    share = pivot.div(row_totals, axis=0) * 100
    smoothed = share.rolling(window=6).mean().dropna()
    top_langs = share.mean().sort_values(ascending=False).head(8).index.tolist()

    # share change pre vs post AI for annotation
    ai = pd.Timestamp(AI_INFLECTION)
    pre_share  = share[share.index <  ai].iloc[-24:].mean()
    post_share = share[share.index >= ai].iloc[:24].mean()
    share_change = ((post_share - pre_share) / pre_share * 100).round(1)

    return jsonify({
        'dates':         smoothed.index.strftime('%Y-%m-%d').tolist(),
        'ai_inflection': AI_INFLECTION,
        'languages': {
            lang: [round(float(v), 2) for v in smoothed[lang]]
            for lang in top_langs
        },
        'share_change': {lang: float(share_change[lang]) for lang in top_langs if lang in share_change},
    })


@app.route('/api/so/velocity')
def so_velocity():
    pivot = load_so_pivot()
    total    = pivot.sum(axis=1)
    velocity = total.pct_change() * 100
    smoothed = velocity.rolling(window=6).mean().dropna()
    # Trim the early explosive-growth era (2008-2012) — those spikes (>500%/mo)
    # dwarf the post-2019 signal we care about and make the chart unreadable.
    smoothed = smoothed[smoothed.index >= pd.Timestamp('2013-01-01')]
    ai          = pd.Timestamp(AI_INFLECTION)
    recent_pre  = pd.Timestamp('2019-11-01')
    pre_avg  = float(smoothed[(smoothed.index >= recent_pre) & (smoothed.index < ai)].mean())
    post_avg = float(smoothed[smoothed.index >= ai].mean())
    return jsonify({
        'dates':         smoothed.index.strftime('%Y-%m-%d').tolist(),
        'values':        [round(float(v), 2) for v in smoothed],
        'ai_inflection': AI_INFLECTION,
        'pre_ai_avg':    round(pre_avg, 2),
        'post_ai_avg':   round(post_avg, 2),
    })


if __name__ == '__main__':
    app.run(debug=True, port=5001)
