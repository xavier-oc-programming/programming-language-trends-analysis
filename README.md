![Python](https://img.shields.io/badge/Python-3.11-blue)
![Pandas](https://img.shields.io/badge/Pandas-2.0+-blue)
![NumPy](https://img.shields.io/badge/NumPy-1.24+-blue)
![Matplotlib](https://img.shields.io/badge/Matplotlib-3.7+-orange)
![SciPy](https://img.shields.io/badge/SciPy-1.10+-blue)
![Flask](https://img.shields.io/badge/Flask-3.0+-lightgrey)

# Programming Language Workforce Strategy

Two-project analysis answering a single business question: **which programming languages should a technology consultancy be hiring and training for right now?**

Project 1 investigates Stack Overflow post-volume data to expose what happened after ChatGPT launched — and why that makes raw SO counts an unreliable hiring signal from 2022 onwards. Project 2 builds the replacement: the **Language Market Index (LMI)**, a composite scoring system across four independent data sources normalised and weighted into a single defensible score. Both feed into an interactive Flask dashboard that lets any stakeholder stress-test the methodology live.

**Project 1 → [notebooks/01_so_decline_analysis.ipynb](notebooks/01_so_decline_analysis.ipynb)**
&nbsp;&nbsp;·&nbsp;&nbsp;
**Project 2 → [notebooks/02_language_market_index.ipynb](notebooks/02_language_market_index.ipynb)**
&nbsp;&nbsp;·&nbsp;&nbsp;
**Dashboard → [dashboard/app.py](dashboard/app.py)** *(port 5001)*

---

## Table of Contents

0. [Prerequisites](#0-prerequisites)
1. [Quick Start](#1-quick-start)
2. [Project Structure](#2-project-structure)
3. [Datasets](#3-datasets)
4. [Project 1 — Is Stack Overflow Dying?](#4-project-1--is-stack-overflow-dying)
5. [Project 2 — Language Market Index](#5-project-2--language-market-index)
6. [Dashboard](#6-dashboard)
7. [Key Findings](#7-key-findings)
8. [Visualisations](#8-visualisations)
9. [Operations Reference](#9-operations-reference)
10. [Course Context](#10-course-context)
11. [Dependencies](#11-dependencies)

---

## 0. Prerequisites

- Python 3.11+
- pip
- Adzuna API credentials (free at [developer.adzuna.com](https://developer.adzuna.com)) — only needed to re-fetch job posting data; cached data is committed

---

## 1. Quick Start

```bash
git clone <repo-url>
cd Day_73_Data_Visualisation_with_Matplotlib_Programming_Languages
pip install -r requirements.txt
cp .env.example .env   # add Adzuna credentials
```

### Run the analysis notebooks

```bash
jupyter notebook notebooks/01_so_decline_analysis.ipynb
jupyter notebook notebooks/02_language_market_index.ipynb
```

Select **Restart & Run All** in each. All charts save to `plots/`.

### Re-run the LMI pipeline (re-fetch all sources)

```bash
cd pipeline
python run.py
```

Skip sources or recompute from cached data:

```bash
python run.py --skip-github --skip-so   # re-run Adzuna + TIOBE only
python run.py --only-score              # recompute index from cached data, no fetching
```

### Run the interactive dashboard

```bash
cd dashboard
python app.py
# open http://localhost:5001
```

### Full system flow

```
pipeline/run.py
    │
    │  ── [Ingestion] ──────────────────────────────────────────────────────────
    ├── Stack Overflow Data Explorer    →  data/raw/so/QueryResults.csv
    │   Monthly post counts per language tag, 2008–2025 (14 tags × 200+ months)
    │
    ├── Adzuna Jobs API                 →  data/raw/adzuna/
    │   Live job posting counts per language, fetched via REST API and cached
    │
    ├── GitHub Octoverse                →  data/raw/github/
    │   Repository activity by language (public dataset, static JSON)
    │
    ├── Stack Overflow Developer Survey →  data/raw/so_survey/
    │   % of developers reporting daily use per language (134 MB CSV, not committed)
    │   so_survey_parsed.csv committed — sufficient to re-run the index
    │
    └── TIOBE Index                     →  data/raw/tiobe/
        Industry recognition ratings, scraped with hardcoded fallback
    │
    │  ── [Processing] ─────────────────────────────────────────────────────────
    ├── normalize.py   →  min-max scale each source independently to 0–100
    │                     output: data/processed/normalized.csv
    │
    └── score.py       →  weighted composite sum + percentile lifecycle classification
                          output: data/processed/index.csv
    │
    │  ── [Analysis] ───────────────────────────────────────────────────────────
    │
    ├── notebooks/01_so_decline_analysis.ipynb
    │   ├── Total post volume — 6-month rolling avg, peak detection
    │   ├── Per-language volume — tab20 colormap, all 14 tags
    │   ├── Pre vs post ChatGPT — 24-month window comparison, sorted bar
    │   ├── Velocity — pct_change, rolling mean, pre/post average lines
    │   ├── Language share — row-normalised relative activity over time
    │   ├── Momentum score — recent 24m vs prior 24m, RdYlGn gradient
    │   ├── Lifecycle matrix — percentile classification, volume × momentum scatter
    │   └── SO vs job demand — linregress, Pearson r, anti-correlation test
    │
    └── notebooks/02_language_market_index.ipynb
        ├── LMI ranked scores — weighted bar, lifecycle colour coding
        ├── Score breakdown — stacked bar showing per-source contribution
        └── Sensitivity analysis — 4 weighting scenarios, ranking stability test
    │
    │  ── [Dashboard] ──────────────────────────────────────────────────────────
    ├── app.py        →  compute_chart_data() runs all pandas/scipy at page load
    │                    DATA injected as {{ chart_data | tojson }} — no page-load fetches
    │                    tab20 + RdYlGn colormaps computed server-side in Python
    │
    └── index.html    →  Chart.js v4 + annotation@3 + datalabels@2
                         Three sections: SO Decline · SO Deep Dive · LMI
                         Dynamic: POST /api/recalculate · GET /api/language/<lang>
    │
    │  ── [Output] ─────────────────────────────────────────────────────────────
    ├── plots/so_decline_analysis/    →  8 charts (PNG, 150 dpi)
    ├── plots/language_market_index/  →  2 charts (PNG, 150 dpi)
    └── dashboard/                    →  interactive Flask app (port 5001)
```

---

## 2. Project Structure

```
├── notebooks/
│   ├── 01_so_decline_analysis.ipynb        # Project 1: Is Stack Overflow Dying?
│   └── 02_language_market_index.ipynb      # Project 2: Language Market Index (LMI)
│
├── pipeline/
│   ├── run.py                              # Orchestrator — runs all ingestion + scoring
│   ├── style.py                            # Shared chart constants + helpers (BG, GREEN, style_ax, fmt_k …)
│   ├── ingestion/
│   │   ├── adzuna_fetch.py                 # Adzuna Jobs API (cached)
│   │   ├── github_fetch.py                 # GitHub Octoverse public dataset
│   │   ├── so_survey_parse.py              # Stack Overflow Developer Survey CSV
│   │   └── tiobe_scrape.py                 # TIOBE Index scraper (hardcoded fallback)
│   └── processing/
│       ├── normalize.py                    # Min-max normalisation per source (0–100)
│       └── score.py                        # Weighted composite + lifecycle classification
│
├── dashboard/
│   ├── app.py                              # Flask app — server-side chart data injection
│   └── templates/index.html                # Chart.js dashboard (SO Decline · Deep Dive · LMI)
│
├── data/
│   ├── raw/
│   │   ├── so/QueryResults.csv             # SO monthly post counts (pre-downloaded)
│   │   ├── adzuna/                         # Job posting counts (API cache)
│   │   ├── github/                         # GitHub Octoverse repo activity
│   │   ├── so_survey/
│   │   │   ├── so_survey_parsed.csv        # Committed — sufficient to re-run the index
│   │   │   └── survey_2025.csv             # NOT committed (134 MB) — download from stackoverflow.co/survey
│   │   └── tiobe/                          # TIOBE Index ratings
│   └── processed/
│       ├── index.csv                       # Final LMI composite scores + lifecycle labels
│       └── normalized.csv                  # Per-source normalised scores (0–100)
│
├── plots/
│   ├── so_decline_analysis/                # 8 charts — generated by notebook 1
│   └── language_market_index/              # 2 charts — generated by notebook 2
│
├── .env.example
├── requirements.txt
└── README.md
```

---

## 3. Datasets

### Stack Overflow post counts (Project 1)

**File:** `data/raw/so/QueryResults.csv`  
**Source:** Stack Overflow Data Explorer — custom SQL query returning monthly post counts per language tag  
**Coverage:** 14 programming language tags · July 2008 – December 2025 · 200+ months  
**Size:** ~15,000 rows (tag × month combinations)

| Column | Type | Description |
|--------|------|-------------|
| DATE | datetime | First day of the month (YYYY-MM-01) |
| TAG | str | Programming language tag (`python`, `javascript`, `java`, etc.) |
| POSTS | int | Total posts with that tag published in that month |

**Pivot structure:** The raw long-format table is immediately pivoted to `DATE × TAG` with `POSTS` as values and `fillna(0)` applied — giving a clean matrix where every language has a value for every month, with zero for months of no activity.

**Languages tracked:** `assembly` · `c` · `c#` · `c++` · `delphi` · `go` · `java` · `javascript` · `perl` · `php` · `python` · `r` · `ruby` · `swift`

---

### LMI data sources (Project 2)

> **Note:** `data/raw/so_survey/survey_2025.csv` (134 MB) is not committed. Download it from [stackoverflow.co/survey](https://stackoverflow.co/survey) and place it at that path before running `pipeline/run.py`. The parsed output (`so_survey_parsed.csv`) is committed and sufficient to re-run the index without re-parsing.

| Source | File | What it measures | Weight |
|--------|------|-----------------|--------|
| Adzuna job postings | `data/raw/adzuna/` | Active job openings requiring each language | 35% |
| GitHub Octoverse | `data/raw/github/` | Public repositories actively built in each language | 30% |
| SO Developer Survey | `data/raw/so_survey/` | % of developers reporting daily use | 25% |
| TIOBE Index | `data/raw/tiobe/` | Industry recognition and search-volume proxy | 10% |

**Normalisation:** each source is independently min-max scaled to 0–100 before weighting. This prevents any single source from dominating through raw magnitude — a language with 50,000 job postings and one with 5,000 are scored relative to the range within Adzuna, not on an absolute scale.

**Lifecycle classification** (applied to final composite scores):

| Stage | Rule |
|-------|------|
| Dominant | composite score ≥ 75th percentile of all languages |
| Mature | composite score ≥ 50th percentile |
| Declining | composite score ≥ 25th percentile |
| Niche | composite score < 25th percentile |

---

## 4. Project 1 — Is Stack Overflow Dying?

**Notebook:** [notebooks/01_so_decline_analysis.ipynb](notebooks/01_so_decline_analysis.ipynb)

**Question:** What happened to Stack Overflow after ChatGPT launched — and does that make it an unreliable proxy for developer activity and language relevance?

**Dataset:** 14 language tags × 200+ months of monthly post counts, pivoted to a `DATE × TAG` matrix.

### Analysis sections

| # | Section | Key question | Operations |
|---|---------|--------------|------------|
| 1 | Setup | Load and pivot raw SO data | `read_csv`, `pivot`, `fillna`, `to_datetime` |
| 2 | Platform Decline | When did SO peak — and how far has it fallen? | `sum(axis=1)`, `rolling(6).mean()`, `idxmax`, `fill_between` |
| 3 | Per-Language Volume | Which languages drove the peak, and which are declining fastest? | `rolling(6).mean()`, `tab20` colormap, `plot` per column |
| 4 | Pre vs Post AI | How much did each language drop in the 24 months after ChatGPT? | `iloc[-24:]`, window `mean()`, percentage change, `barh` |
| 5 | Velocity Analysis | Was ChatGPT the cause, or an accelerant of a pre-existing trend? | `pct_change()`, `rolling(6)`, pre/post average lines, `axhline` |
| 6 | Share Over Time | Which languages are gaining or losing ground relative to each other? | `div(row_totals, axis=0)`, `* 100`, `rolling(6)`, `head(8)` |
| 7 | Language Momentum | How does each language's recent trajectory compare to its own history? | `iloc[-24:]`, `iloc[-48:-24]`, momentum `pct_change`, `RdYlGn` gradient |
| 8 | Lifecycle Matrix | Where does each language sit on the volume × momentum plane? | `np.percentile`, custom `classify_so()`, scatter + quadrant lines |
| 9 | SO vs Job Demand | Does SO momentum actually predict what employers are hiring for? | `scipy.stats.linregress`, Pearson r, regression line overlay |
| 10 | Findings | What does this all mean for workforce strategy? | Narrative summary backed by computed values |

---

## 5. Project 2 — Language Market Index

**Notebook:** [notebooks/02_language_market_index.ipynb](notebooks/02_language_market_index.ipynb)

**Question:** Given that SO post volume became unreliable post-November 2022, what composite signal can replace it for language workforce strategy?

**Approach:** Build a composite index from four independent data sources, each measuring a different dimension of market presence, normalised to remove scale differences and weighted by signal quality.

### LMI methodology

```
For each language l and each source s:

    normalized[l][s] = (raw[l][s] - min_s) / (max_s - min_s) × 100
                       ← min-max scaling applied independently per source

    composite[l] = 0.35 × normalized[l][adzuna]
                 + 0.30 × normalized[l][github]
                 + 0.25 × normalized[l][so_survey]
                 + 0.10 × normalized[l][tiobe]

    lifecycle[l] = percentile_classify(composite[l])
                   ← Dominant / Mature / Declining / Niche
                      based on 75th / 50th / 25th percentile thresholds
```

### Analysis sections

| # | Section | Key question | Operations |
|---|---------|--------------|------------|
| 1 | Setup & Pipeline | Load pipeline modules and verify processed data exists | `sys.path.insert`, `import`, `os.path.exists`, `os.makedirs` |
| 2 | Load Index | What are the current LMI rankings and lifecycle labels? | `read_csv`, `to_string`, composite score inspection |
| 3 | Composite Scores | Which languages lead across all four signals combined? | `barh`, lifecycle colour coding, score `text` annotations |
| 4 | Score Breakdown | What does each source contribute, and which signal drives each ranking? | Stacked `barh`, `np.zeros`, `bottom` accumulation |
| 5 | Sensitivity Analysis | Does the ranking hold under different weighting assumptions? | `compute_index(weights)` across 4 scenarios, `pd.DataFrame` comparison |
| 6 | Strategic Recommendation | What should a consultancy actually hire for, and with what confidence? | Cross-scenario validation, tiered hiring recommendation |

### Default weights and rationale

| Source | Weight | Rationale |
|--------|--------|-----------|
| Adzuna job postings | 35% | The most direct and immediately actionable workforce signal — what employers are paying for right now |
| GitHub Octoverse | 30% | Actual developer behaviour: what people build in practice, not what they report using |
| SO Developer Survey | 25% | Broad self-reported usage signal; less affected by the platform-level decline identified in Project 1 |
| TIOBE Index | 10% | Lagging indicator — useful for macro direction and industry recognition, weak for near-term hiring magnitude |

---

## 6. Dashboard

**File:** [dashboard/app.py](dashboard/app.py) · **Port:** 5001

Three sections navigable via sidebar, each lazy-loaded on first visit:

| Section | Charts |
|---------|--------|
| **SO Decline** | Platform total (rolling avg) · Pre/post ChatGPT drop per language · Velocity (MoM change) · Share over time + interactive pie snapshot comparison |
| **SO Deep Dive** | Per-language monthly posts (tab20 colormap) · Momentum scores (RdYlGn gradient, value labels) · SO vs job demand scatter (regression line, Pearson r, language labels) · Lifecycle matrix (volume × momentum, language labels, median threshold) |
| **Language Market Index** | Composite scores · Score breakdown by source · Ranked table · Language detail panel · Weight sliders → live recalculate |

**Architecture:** All chart data is computed server-side at page load. `compute_chart_data()` in Flask runs all pandas operations — rolling averages, momentum windows, scipy linregress, and matplotlib colormaps (tab20, RdYlGn) — and injects the result as a single JSON object into the template. Chart.js reads synchronously from `DATA.*` with no page-load fetch calls. Two endpoints remain dynamic:

- `POST /api/recalculate` — recomputes the full LMI under custom weights from the sidebar sliders
- `GET /api/language/<lang>` — returns per-source breakdown for the clicked table row

---

## 7. Key Findings

### Project 1 — Is Stack Overflow Dying?

**1. Stack Overflow is in structural freefall.**  
Total post volume peaked at **103,077 posts/month in June 2016** and by December 2025 had fallen to **2,338/month — a 97.7% drop from peak**. Averaged across all 14 tracked languages, the 24 months after ChatGPT launched saw a **−53.5%** drop versus the prior 24 months. The platform is not declining gradually — it is collapsing.

**2. ChatGPT was an accelerant, not the cause.**  
SO was already declining at **−0.5%/month** in the three years before ChatGPT (2019–2022). After launch, the rate became **−7.6%/month — 15× steeper**. The structural decline began years earlier as developers shifted to documentation sites, YouTube, and search engines for answers. ChatGPT didn't break a healthy platform; it finished one already losing ground.

**3. The decline is uneven — and the asymmetry is the insight.**  
JavaScript lost the most relative share (−16.2%). Go (+44.2%) and C# (+30.9%) actually *gained* share post-ChatGPT. Languages where AI assistance is weakest — enterprise systems, embedded, and niche ecosystems with complex context-dependent problems — held up best on SO. Languages where AI is strongest (Python, JavaScript) saw the steepest relative declines, precisely because their developers were the earliest adopters of AI-assisted answers.

**4. Python's SO decline is a signal of strength, not weakness.**  
Python's absolute post volume fell −59.9% — above the −53.5% average — and its relative share dropped −4.6% post-ChatGPT. This is counterintuitive until you recognise that Python is the primary language of AI tooling itself. Python developers were among the first to route questions through ChatGPT and Copilot, making a falling SO count a proxy for early AI adoption, not declining relevance.

**5. SO momentum anti-correlates with job market demand (r = −0.26).**  
Languages declining fastest on SO (Python, Java, JavaScript) remain the top hiring targets by Adzuna job posting count. The Pearson correlation between SO momentum and job scores is **negative**. This is not just noise — it is an inversion. Using raw SO counts as a hiring signal would actively mislead: it points toward niche languages with stable SO presence (Assembly, Delphi) and away from the languages employers are actually hiring for.

### Project 2 — Language Market Index

**6. Python is the undisputed #1 — by a wide margin.**  
Composite LMI score of **88.4/100**. The gap to #2 (JavaScript, 68.0) is larger than the gap from #2 to #5. Python ranks first in every weighting scenario tested: jobs-heavy, GitHub-heavy, and equal weights. Its dominance is structural, not an artefact of the default weighting model.

**7. The top four form a stable Dominant tier.**  
Python, JavaScript, Java, and TypeScript (scores 35–88) represent the safe hiring bets for any consultancy. These are the only four languages where all four independent signals — job postings, GitHub activity, developer survey, and TIOBE — simultaneously agree. Confidence is highest here.

**8. TypeScript is the most underrated hire.**  
Ranked #4 at 35.4, with the strongest GitHub presence of any language outside Python and JavaScript — it is the primary language of the modern web toolchain. Often treated as a JavaScript variant in workforce discussions, it registers as a meaningfully separate and growing signal in the data.

**9. The LMI is robust to weighting assumptions.**  
The top-5 composition is unchanged across all four scenarios tested. Python and JavaScript trade the #1–#2 positions depending on whether job postings or GitHub activity are weighted more heavily, but the Dominant tier is stable. This robustness makes the index defensible to stakeholders who might challenge any individual weighting choice.

**10. Rust and Kotlin are false negatives in the current index.**  
Both show strong developer survey interest but weak job market signal — not because they are unimportant, but because Adzuna job postings (the highest-weighted source) reflect current hiring, not leading adoption curves. These are the two languages most worth monitoring as early indicators of where the next hiring wave is forming.

---

## 8. Visualisations

All charts are committed to `plots/` and visible without running the code.

### Total Monthly Posts — Platform Decline
![SO Total Decline](plots/so_decline_analysis/total_monthly_posts_decline.png)

### Monthly Posts by Language
![Per-Language Trend](plots/so_decline_analysis/monthly_posts_per_language.png)

### Pre vs Post ChatGPT — Drop per Language
![Pre/Post Drop](plots/so_decline_analysis/pre_post_chatgpt_drop_per_language.png)

### Velocity — Month-over-Month Change
![Velocity Chart](plots/so_decline_analysis/month_over_month_velocity.png)

### Language Share of Monthly Posts Over Time
![Share Over Time](plots/so_decline_analysis/language_share_over_time.png)

### Language Momentum Score (recent 24m vs prior 24m)
![Momentum Chart](plots/so_decline_analysis/language_momentum_score.png)

### Language Lifecycle Matrix: Volume vs Momentum
![Lifecycle Matrix](plots/so_decline_analysis/lifecycle_matrix_volume_vs_momentum.png)

### Stack Overflow Momentum vs Job Market Demand
![Correlation](plots/so_decline_analysis/so_momentum_vs_job_demand.png)

### LMI Composite Scores
![LMI Scores](plots/language_market_index/composite_scores.png)

### LMI Score Breakdown by Source
![LMI Breakdown](plots/language_market_index/score_breakdown_by_source.png)

---

## 9. Operations Reference

### Data Loading & Pivoting
`pd.read_csv()` · `pd.to_datetime()` · `df.pivot(index, columns, values)` · `fillna(0)` · `df.columns = [...]` · `df.set_index(col)`

### Rolling & Smoothing
`rolling(window=6).mean()` · `.dropna()` · `idxmax()` · `.max()` · `.iloc[-1]` · `smoothed.index[-1]`

### Window Comparisons (pre/post ChatGPT)
`df[df.index < timestamp]` · `df[df.index >= timestamp]` · `df.iloc[-24:]` · `df.iloc[-48:-24]` · `.mean()` per window · percentage difference `(post - pre) / pre * 100`

### Percentage Change & Velocity
`pct_change()` · `* 100` · `rolling(6).mean()` · boolean index slicing for date ranges · `float(series.mean())`

### Normalisation & Relative Measures
`(x - x.min()) / (x.max() - x.min()) * 100` · `div(row_totals, axis=0) * 100` (row normalisation for share) · `replace(0, np.nan)` before division

### Aggregation & Sorting
`sum(axis=1)` · `sum(axis=0)` · `.mean()` · `sort_values(ascending=True/False)` · `.head(n)` · `.round(1)` · `.idxmax()` · `.idxmin()`

### Percentile Classification
`np.percentile(vals, 25)` · `np.percentile(vals, 50)` · `np.percentile(vals, 75)` · custom `classify_so(volume, momentum)` function with percentile thresholds

### Correlation & Regression
`scipy.stats.linregress(x, y)` → `slope, intercept, r, p, se` · `np.linspace(x.min(), x.max(), 100)` · `slope * x_line + intercept` · Pearson r interpretation

### Shared Style Module (`pipeline/style.py`)
To eliminate repetition across notebooks and pipeline scripts, all colour constants and chart helpers live in a single importable module. Both notebooks load it with `from style import *`.

| Export | What it is |
|--------|------------|
| `BG`, `PANEL`, `BORDER` | Dark-theme background hex values |
| `TEXT`, `TEXT_DIM`, `WHITE` | Text colour hierarchy |
| `BLUE`, `GREEN`, `AMBER`, `RED`, `GREY`, `MARK`, `ORANGE`, `PURPLE` | Named accent colours — used in place of hex literals throughout all charts |
| `LIFECYCLE` | `dict` mapping lifecycle label → colour — used by scatter plots, bar charts, and dashboard |
| `style_ax(ax, fig)` | Applies the full 8-line dark-theme boilerplate in one call — background, tick colour, spine colour, label colour |
| `fmt_k(x, _)` | Axis tick formatter: `1500 → '1k'`, `1_500_000 → '1.5M'` |
| `fmt_pct(x, _)` | Axis tick formatter: `-7.6 → '-7.6%'` |

### Colormaps & Colour Gradients
`plt.cm.tab20(range(n))` · `matplotlib.cm.RdYlGn(norm_value)` · `matplotlib.colors.Normalize(vmin, vmax)` · `#{:02x}{:02x}{:02x}` hex conversion · `mpatches.Patch(color, label)` custom legend

### Matplotlib Charting
`fig, ax = plt.subplots(figsize=…)` · `ax.plot()` · `ax.fill_between()` · `ax.bar()` · `ax.barh()` · `ax.scatter()` · `ax.axvline()` · `ax.axhline()` · `ax.annotate()` · `ax.text()` · `ax.legend()` · `mticker.FuncFormatter(lambda x, _: …)` · `style_ax(ax, fig)` (shared helper) · `plt.tight_layout()` · `plt.savefig(dpi=150, facecolor=…)`

### Flask Dashboard
`Flask(__name__)` · `render_template()` · `jsonify()` · `request.get_json()` · `{{ data | tojson }}` (Jinja2 server-side injection) · `@app.route(methods=['POST'])` · `scipy.stats.linregress` at page load · colormap hex conversion in Python before template render

### Chart.js (JavaScript)
`new Chart(canvas, {type, data, options})` · `maintainAspectRatio: false` · `chartjs-plugin-annotation@3` (line annotations, label annotations) · `chartjs-plugin-datalabels@2` (bar value labels, scatter dot labels) · lazy section initialisation on first navigate · `chart.update()` for live recalculation · `fetch('/api/recalculate', {method: 'POST', body: JSON.stringify(weights)})`

---

## 10. Course Context

**100 Days of Code: The Complete Python Pro Bootcamp** — Day 73.  
Topics introduced by the course: pandas DataFrames, matplotlib basics, data visualisation.

The course provided the foundation. This project extends it significantly in scope and rigour: a four-source data ingestion pipeline, independent min-max normalisation, percentile-based lifecycle classification, a weighted composite index with sensitivity analysis, scipy correlation and OLS regression, 10 publication-quality charts, a three-section interactive Flask dashboard with Chart.js, server-side JSON data injection, and a full analytical narrative across two linked notebooks that run from raw data exploration to a structured strategic recommendation.

---

## 11. Dependencies

| Package | Purpose |
|---------|---------|
| `pandas` | Data loading, pivoting, rolling averages, window comparisons, normalisation |
| `numpy` | Percentile computation, linspace, colormap normalisation, array operations |
| `matplotlib` | All 10 charts — line, bar, barh, scatter, fill_between, annotations, colormaps |
| `scipy` | Pearson correlation and OLS regression (`stats.linregress`) |
| `flask` | Interactive dashboard — routing, template rendering, JSON APIs |
| `requests` | Adzuna Jobs API + GitHub Octoverse data fetch |
| `beautifulsoup4` | TIOBE Index HTML scraping |
| `python-dotenv` | `.env` credential loading for Adzuna API keys |
| `jupyter` | Notebook server for `.ipynb` files |

```bash
pip install -r requirements.txt
```
