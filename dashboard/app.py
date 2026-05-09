import os
import sys
import pandas as pd
import numpy as np
from flask import Flask, render_template, jsonify, request
from dotenv import load_dotenv
from scipy import stats
from matplotlib import cm as mpl_cm
from matplotlib.colors import Normalize as MplNorm

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


def _rgba_to_hex(rgba):
    return '#{:02x}{:02x}{:02x}'.format(
        int(rgba[0] * 255), int(rgba[1] * 255), int(rgba[2] * 255))


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


def _classify_so(v, m, vol_q1, vol_q3, mom_med):
    if v >= vol_q3:                  return 'Dominant'
    if v >= vol_q1 and m >= mom_med: return 'Mature'
    if m >= mom_med:                 return 'Rising'
    if v >= vol_q1:                  return 'Declining'
    return 'Niche'


def compute_chart_data():
    pivot = load_so_pivot()
    df    = load_index()
    norm  = load_normalized()
    ai    = pd.Timestamp(AI_INFLECTION)

    # ── SO Decline 1 ─────────────────────────────────────────────────────────

    # Overview
    total    = pivot.sum(axis=1)
    smoothed = total.rolling(6).mean().dropna()
    peak_date = smoothed.idxmax()

    # Impact (pre/post ChatGPT)
    pre_ai  = pivot[pivot.index <  ai].iloc[-24:].mean()
    post_ai = pivot[pivot.index >= ai].iloc[:24].mean()
    drop    = ((post_ai - pre_ai) / pre_ai * 100).round(1).sort_values()

    # Velocity
    velocity    = total.pct_change() * 100
    smoothed_vel = velocity.rolling(6).mean().dropna()
    smoothed_vel = smoothed_vel[smoothed_vel.index >= pd.Timestamp('2013-01-01')]
    recent_pre  = pd.Timestamp('2019-11-01')
    pre_avg  = float(smoothed_vel[(smoothed_vel.index >= recent_pre) & (smoothed_vel.index < ai)].mean())
    post_avg = float(smoothed_vel[smoothed_vel.index >= ai].mean())

    # Share
    row_totals   = pivot.sum(axis=1).replace(0, float('nan'))
    share        = pivot.div(row_totals, axis=0) * 100
    smoothed_shr = share.rolling(6).mean().dropna()
    top8         = share.mean().sort_values(ascending=False).head(8).index.tolist()
    pre_shr      = share[share.index <  ai].iloc[-24:].mean()
    post_shr     = share[share.index >= ai].iloc[:24].mean()
    shr_change   = ((post_shr - pre_shr) / pre_shr * 100).round(1)

    so1 = {
        'overview': {
            'dates':      smoothed.index.strftime('%Y-%m-%d').tolist(),
            'values':     [round(float(v)) for v in smoothed],
            'peak_date':  peak_date.strftime('%Y-%m-%d'),
            'peak_value': round(float(smoothed.max())),
        },
        'impact': {
            'languages': drop.index.tolist(),
            'values':    [float(v) for v in drop],
            'average':   round(float(drop.mean()), 1),
        },
        'velocity': {
            'dates':       smoothed_vel.index.strftime('%Y-%m-%d').tolist(),
            'values':      [round(float(v), 2) for v in smoothed_vel],
            'pre_ai_avg':  round(pre_avg, 2),
            'post_ai_avg': round(post_avg, 2),
        },
        'share': {
            'dates': smoothed_shr.index.strftime('%Y-%m-%d').tolist(),
            'languages': {
                lang: [round(float(v), 2) for v in smoothed_shr[lang]]
                for lang in top8
            },
            'share_change': {
                lang: float(shr_change[lang])
                for lang in top8 if lang in shr_change
            },
        },
    }

    # ── SO Decline 2 ─────────────────────────────────────────────────────────

    # Monthly posts per language (all 14, tab20 colormap)
    smoothed_pvt = pivot.rolling(6).mean().dropna()
    tab20 = [_rgba_to_hex(mpl_cm.tab20(i)) for i in range(len(pivot.columns))]

    # Momentum: recent 24m vs prior 24m from end of data (matches notebook exactly)
    recent_24 = pivot.iloc[-24:].mean()
    prior_24  = pivot.iloc[-48:-24].mean()
    momentum  = ((recent_24 - prior_24) / prior_24 * 100).round(1).sort_values()

    # RdYlGn gradient colors for momentum bars
    _norm      = MplNorm(vmin=float(momentum.min()), vmax=float(momentum.max()))
    mom_colors = [_rgba_to_hex(mpl_cm.RdYlGn(_norm(v))) for v in momentum.values]

    # Lifecycle matrix
    total_posts = pivot.sum()
    vol_q3  = float(np.percentile(total_posts.to_numpy(), 75))
    vol_q1  = float(np.percentile(total_posts.to_numpy(), 25))
    mom_med = float(np.percentile(momentum.to_numpy(), 50))

    matrix = [
        {
            'language':  lang,
            'volume':    round(float(total_posts[lang])),
            'momentum':  round(float(momentum[lang]), 1),
            'lifecycle': _classify_so(total_posts[lang], momentum[lang], vol_q1, vol_q3, mom_med),
        }
        for lang in total_posts.index
    ]

    # Thresholds for reference lines
    thresholds = {
        'mom_med': round(mom_med, 1),
        'vol_q1':  round(float(vol_q1)),
        'vol_q3':  round(float(vol_q3)),
    }

    # Correlation: SO momentum vs Adzuna raw job counts (matches notebook)
    corr_data = []
    pearson_r = None
    if norm is not None:
        adzuna = norm[norm['source'] == 'adzuna_total'].set_index('language')['raw_value']
        for lang in momentum.index:
            key = lang.lower()
            if key in adzuna.index:
                corr_data.append({
                    'language':  lang,
                    'momentum':  round(float(momentum[lang]), 1),
                    'job_score': round(float(adzuna[key])),
                })
        if len(corr_data) > 1:
            xs = [d['momentum'] for d in corr_data]
            ys = [d['job_score'] for d in corr_data]
            slope, intercept, r, _, _ = stats.linregress(xs, ys)
            pearson_r = round(float(r), 2)
            x_min, x_max = min(xs), max(xs)
            corr_regression = {
                'x': [round(x_min, 1), round(x_max, 1)],
                'y': [round(slope * x_min + intercept), round(slope * x_max + intercept)],
            }
        else:
            corr_regression = None
    else:
        corr_regression = None

    so2 = {
        'per_language': {
            'dates':  smoothed_pvt.index.strftime('%Y-%m-%d').tolist(),
            'langs':  list(pivot.columns),
            'colors': tab20,
            'languages': {
                lang: [round(float(v), 1) for v in smoothed_pvt[lang]]
                for lang in pivot.columns
            },
        },
        'momentum': {
            'languages': momentum.index.tolist(),
            'values':    [float(v) for v in momentum],
            'colors':    mom_colors,
            'average':   round(float(momentum.mean()), 1),
        },
        'matrix':      matrix,
        'thresholds':  thresholds,
        'correlation': corr_data,
        'regression':  corr_regression,
        'pearson_r':   pearson_r,
    }

    # ── LMI ──────────────────────────────────────────────────────────────────

    lmi = []
    if df is not None:
        score_cols = [c for c in df.columns if c.startswith('score_')]
        for _, row in df.iterrows():
            item = {
                'language':        row['language'],
                'composite_score': round(float(row['composite_score']), 2),
                'lifecycle':       row['lifecycle'],
                'color':           LIFECYCLE_COLORS.get(row['lifecycle'], '#fff'),
            }
            for col in score_cols:
                item[col] = round(float(row[col]), 2)
            lmi.append(item)

    return {
        'so1':           so1,
        'so2':           so2,
        'lmi':           lmi,
        'ai_inflection': AI_INFLECTION,
    }


# ── Main page ─────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    df      = load_index()
    no_data = df is None

    table = []
    if not no_data:
        table = df[['rank', 'language', 'composite_score', 'lifecycle']].to_dict(orient='records')
        for row in table:
            row['composite_score'] = float(row['composite_score'])
            row['color'] = LIFECYCLE_COLORS.get(row['lifecycle'], '#fff')

    chart_data = compute_chart_data()

    return render_template('index.html',
                           table=table,
                           weights=DEFAULT_WEIGHTS,
                           source_labels=SOURCE_LABELS,
                           no_data=no_data,
                           chart_data=chart_data)


# ── Dynamic APIs (recalculate + language detail) ──────────────────────────────

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
        return jsonify({'error': 'Weights must sum to 1.0'}), 400
    try:
        result     = compute_index(weights)
        score_cols = [c for c in result.columns if c.startswith('score_')]

        table = result[['rank', 'language', 'composite_score', 'lifecycle']].to_dict(orient='records')
        for row in table:
            row['composite_score'] = float(row['composite_score'])
            row['color'] = LIFECYCLE_COLORS.get(row['lifecycle'], '#fff')

        scores = []
        for _, row in result.iterrows():
            item = {
                'language':        row['language'],
                'composite_score': round(float(row['composite_score']), 2),
                'lifecycle':       row['lifecycle'],
                'color':           LIFECYCLE_COLORS.get(row['lifecycle'], '#fff'),
            }
            for col in score_cols:
                item[col] = round(float(row[col]), 2)
            scores.append(item)

        return jsonify({'table': table, 'scores': scores})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5001)
