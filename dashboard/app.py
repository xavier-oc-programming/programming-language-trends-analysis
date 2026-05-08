import os
from flask import Flask, render_template, jsonify, request
from dotenv import load_dotenv
from data_processor import load_pivot, build_strategy_table, fetch_job_count

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

app = Flask(__name__)

ADZUNA_APP_ID  = os.getenv('ADZUNA_APP_ID')
ADZUNA_APP_KEY = os.getenv('ADZUNA_APP_KEY')
ADZUNA_COUNTRY = os.getenv('ADZUNA_COUNTRY', 'gb')
ADZUNA_AVAILABLE = bool(ADZUNA_APP_ID and ADZUNA_APP_KEY)

pivot    = load_pivot()
smoothed = pivot.rolling(window=6).mean()
strategy = build_strategy_table(pivot)


@app.route('/')
def index():
    languages = sorted(pivot.columns.tolist())
    table_data = strategy.reset_index().to_dict(orient='records')
    return render_template(
        'index.html',
        languages=languages,
        table_data=table_data,
        adzuna_available=ADZUNA_AVAILABLE,
    )


@app.route('/api/language/<lang>')
def language_data(lang):
    if lang not in pivot.columns:
        return jsonify({'error': 'Language not found'}), 404

    series = smoothed[lang].dropna()
    row    = strategy.loc[lang]

    job_count = None
    if ADZUNA_AVAILABLE:
        job_count = fetch_job_count(lang, ADZUNA_APP_ID, ADZUNA_APP_KEY, ADZUNA_COUNTRY)

    return jsonify({
        'language':    lang,
        'momentum':    float(row['momentum']),
        'lifecycle':   row['lifecycle'],
        'total_posts': int(row['total_posts']),
        'job_count':   int(job_count) if job_count is not None else None,
        'chart': {
            'dates':  [d.strftime('%Y-%m') for d in series.index],
            'values': [round(float(v), 1) for v in series.values],
        }
    })


@app.route('/api/matrix')
def matrix_data():
    records = []
    for lang, row in strategy.iterrows():
        records.append({
            'language':    lang,
            'momentum':    float(row['momentum']),
            'total_posts': int(row['total_posts']),
            'lifecycle':   row['lifecycle'],
        })
    return jsonify(records)


if __name__ == '__main__':
    app.run(debug=True, port=5000)
