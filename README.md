# Programming Language Workforce Strategy

**Business question:** Which programming languages should a technology consultancy be hiring and training for right now?

This project uses Stack Overflow developer activity (2008–present) as a measure of developer interest and cross-references it with live job-posting volume (Adzuna API) to produce quantified hiring and training recommendations.

---

## What this produces

| Output | Description |
|--------|-------------|
| Momentum score | % change in avg monthly posts: last 24 months vs prior 24 months |
| Lifecycle classification | Rising / Dominant / Mature / Declining / Niche |
| Job market correlation | Stack Overflow momentum vs live Adzuna job postings |
| Strategic recommendation | One-paragraph consultant-style hiring conclusion |
| Interactive dashboard | Flask app — select any language and see all signals in one view |

---

## Repo structure

```
├── analysis/
│   ├── language_strategy.ipynb   # Main analysis: workforce strategy
│   └── so_decline_analysis.ipynb # Extra: is Stack Overflow dying?
├── dashboard/
│   ├── app.py                    # Flask app
│   ├── data_processor.py         # Shared data logic
│   └── templates/index.html      # Dashboard UI
├── data/
│   └── QueryResults.csv          # Stack Overflow monthly post counts
├── .env.example                  # Adzuna credentials template
└── requirements.txt
```

---

## Quick start

### Notebook

```bash
pip install -r requirements.txt
cp .env.example .env         # fill in Adzuna credentials (optional)
jupyter notebook analysis/language_strategy.ipynb
```

### Dashboard

```bash
pip install -r requirements.txt
cp .env.example .env         # fill in Adzuna credentials (optional)
cd dashboard
python app.py
# open http://localhost:5000
```

---

## Adzuna API (optional)

Register free at [developer.adzuna.com](https://developer.adzuna.com), then add your credentials to `.env`:

```
ADZUNA_APP_ID=your_app_id
ADZUNA_APP_KEY=your_app_key
ADZUNA_COUNTRY=gb
```

Without credentials the job market section is skipped gracefully — all other analysis runs as normal.

---

## Dataset

Stack Exchange Data Explorer export — monthly post counts per language tag from 2008 onwards.

| Column | Description |
|--------|-------------|
| `DATE` | First day of the month |
| `TAG` | Programming language (e.g. `python`, `javascript`) |
| `POSTS` | Posts published with that tag that month |

Languages: assembly, c, c#, c++, delphi, go, java, javascript, perl, php, python, r, ruby, swift

---

## Dependencies

| Package | Purpose |
|---------|---------|
| `pandas` | Data loading, groupby, pivot, rolling |
| `numpy` | Momentum calculations |
| `matplotlib` | Charts (notebook) |
| `flask` | Dashboard server |
| `requests` | Adzuna API calls |
| `python-dotenv` | `.env` loading |
