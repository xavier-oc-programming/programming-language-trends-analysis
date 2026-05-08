import os
import sys
import json
import pandas as pd
from flask import Flask, render_template, jsonify, request
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

from processing.score import compute_index, DEFAULT_WEIGHTS

app = Flask(__name__)

INDEX_PATH      = os.path.join(os.path.dirname(__file__), '..', 'data', 'processed', 'index.csv')
NORMALIZED_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'processed', 'normalized.csv')

LIFECYCLE_COLORS = {
    'Dominant':  '#5bc0f8',
    'Rising':    '#4ecb71',
    'Mature':    '#f0c040',
    'Declining': '#f07070',
    'Niche':     '#aaaaaa',
}

SOURCE_LABELS = {
    'adzuna_total':    'Job Postings',
    'github_repos':    'GitHub Repos',
    'so_survey_usage': 'Developer Survey',
    'tiobe_rating':    'TIOBE Index',
}


def load_index():
    if not os.path.exists(INDEX_PATH):
        return None
    return pd.read_csv(INDEX_PATH)


def load_normalized():
    if not os.path.exists(NORMALIZED_PATH):
        return None
    return pd.read_csv(NORMALIZED_PATH)


@app.route('/')
def index():
    df = load_index()
    if df is None:
        return render_template('index.html', no_data=True,
                               weights=DEFAULT_WEIGHTS,
                               source_labels=SOURCE_LABELS)

    table = df[['rank', 'language', 'composite_score', 'lifecycle']].to_dict(orient='records')
    for row in table:
        row['composite_score'] = float(row['composite_score'])
        row['color'] = LIFECYCLE_COLORS.get(row['lifecycle'], '#fff')

    return render_template('index.html',
                           table=table,
                           weights=DEFAULT_WEIGHTS,
                           source_labels=SOURCE_LABELS,
                           no_data=False)


@app.route('/api/language/<lang>')
def language_detail(lang):
    df  = load_index()
    norm = load_normalized()

    if df is None:
        return jsonify({'error': 'No index data — run the pipeline first.'}), 404

    row = df[df['language'] == lang.lower()]
    if row.empty:
        return jsonify({'error': f'Language "{lang}" not found'}), 404

    row = row.iloc[0]

    breakdown = {}
    if norm is not None:
        lang_norm = norm[norm['language'] == lang.lower()]
        for _, r in lang_norm.iterrows():
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
    """Recalculate the index with custom weights sent from the dashboard sliders."""
    data = request.get_json()
    weights = {
        'adzuna_total':    float(data.get('adzuna_total',    0.35)),
        'github_repos':    float(data.get('github_repos',    0.30)),
        'so_survey_usage': float(data.get('so_survey_usage', 0.25)),
        'tiobe_rating':    float(data.get('tiobe_rating',    0.10)),
    }

    total = sum(weights.values())
    if abs(total - 1.0) > 0.05:
        return jsonify({'error': f'Weights must sum to 1.0 (got {total:.2f})'}), 400

    try:
        result = compute_index(weights)
        table = result[['rank', 'language', 'composite_score', 'lifecycle']].to_dict(orient='records')
        for row in table:
            row['composite_score'] = float(row['composite_score'])
            row['color'] = LIFECYCLE_COLORS.get(row['lifecycle'], '#fff')
        return jsonify({'table': table})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/index')
def full_index():
    df = load_index()
    if df is None:
        return jsonify([])
    records = df[['rank', 'language', 'composite_score', 'lifecycle']].to_dict(orient='records')
    for r in records:
        r['composite_score'] = float(r['composite_score'])
        r['color'] = LIFECYCLE_COLORS.get(r['lifecycle'], '#fff')
    return jsonify(records)


if __name__ == '__main__':
    app.run(debug=True, port=5001)
