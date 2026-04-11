# Programming Language Trends Analysis

Analyses Stack Overflow post counts to track the popularity of programming languages over time from 2008 onwards.

This project investigates how the popularity of major programming languages has shifted across more than a decade of Stack Overflow activity. Using monthly post-count data tagged by language, the analysis answers questions such as which language dominated in 2010 versus 2020, how Python's rise compares to Java's decline, and how newer languages like Go and Swift entered the scene relative to established ones like C and Perl.

The dataset is a CSV export from the Stack Exchange Data Explorer, containing one row per language per month. Each row records a date, a programming language tag, and the number of Stack Overflow posts published that month with that tag. The data is loaded into pandas, cleaned to parse datetime strings, reshaped from long to wide format via a pivot, and then visualised as multi-line time-series charts — one line per language.

No external APIs or credentials are required. All data was exported in advance as `QueryResults.csv` and is committed directly to the repository.

---

## Table of Contents

1. [Quick start](#1-quick-start)
2. [Analysis flow](#2-analysis-flow)
3. [Features](#3-features)
4. [Dataset schema](#4-dataset-schema)
5. [Architecture](#5-architecture)
6. [Notebook reference](#6-notebook-reference)
7. [Configuration reference](#7-configuration-reference)
8. [Course context](#8-course-context)
9. [Dependencies](#9-dependencies)

---

## 1. Quick start

```bash
git clone https://github.com/xavier-oc-programming/programming-language-trends-analysis.git
cd programming-language-trends-analysis
pip install -r requirements.txt
jupyter notebook
```

Open `practice/A_01_Programming_Languages_Analysis.ipynb` first to follow the full analysis from raw CSV to final chart. For lesson notes and annotated explanations, start with `theory/00__Overview.ipynb`.

---

## 2. Analysis flow

```
data/QueryResults.csv
        │
        ▼
pd.read_csv()  →  DataFrame (2901 rows × 3 cols)
        │
        ├── df.columns = ['DATE', 'TAG', 'POSTS']
        ├── pd.to_datetime(df.DATE)      →  datetime index
        ├── groupby('TAG')['POSTS'].sum() →  all-time totals per language
        ├── groupby('TAG')['DATE'].count() →  months of data per language
        │
        ▼
df.pivot(index='DATE', columns='TAG', values='POSTS')
        │
        ├── fillna(0)                    →  wide_df (210 rows × 14 cols)
        │
        ├── plt.plot() per column        →  raw multi-line chart
        │
        └── rolling(window=6).mean()     →  smoothed multi-line chart
```

---

## 3. Features

- Identifies **JavaScript** as the all-time most-posted language (2.5 M posts)
- Ranks all 14 languages by total post count across the full dataset period
- Shows which languages have fewer months of data because they launched later (Go, Swift)
- Produces a **raw multi-line chart** of all language trends from 2008 onwards
- Produces a **smoothed multi-line chart** using a 6-month rolling average to reveal long-term growth and decline patterns
- Demonstrates how Python overtook Java and C# in the mid-2010s and continued growing

---

## 4. Dataset schema

### `data/QueryResults.csv`

| Column | Type | Description |
|--------|------|-------------|
| `DATE` | string → datetime | First day of the month the posts were published (e.g. `2008-07-01`) |
| `TAG` | string | Stack Overflow tag representing the programming language |
| `POSTS` | integer | Number of posts published with that tag in that month |

**Computed columns** (added at runtime in the notebook):

| Column | Description |
|--------|-------------|
| `POSTS` sum per TAG | All-time post total per language via `groupby().sum()` |
| Pivoted wide columns | One column per language after `df.pivot()` |
| Rolling mean columns | 6-month smoothed values via `rolling(6).mean()` |

---

## 5. Architecture

```
programming-language-trends-analysis/
│
├── theory/                          # Lesson notes and annotated explanations
│   ├── 00__Overview.ipynb           # Day 73 goals and what the analysis covers
│   ├── 01__Download_and_Open_Starter_Notebook.ipynb  # Dataset source and setup
│   ├── 02__Preliminary_Data_Exploration.ipynb        # Loading and inspecting the CSV
│   ├── 03__Analysis_by_Programming_Language.ipynb    # Grouping and ranking languages
│   ├── 04__Data_Cleaning_Working_with_Timestamps.ipynb  # Parsing datetime strings
│   ├── 05__Data_Manipulation_Pivoting_DataFrames.ipynb  # Pivot to wide format
│   ├── 06__Data_Visualisation_with_Matplotlib.ipynb     # Single and dual line charts
│   ├── 07__Multi_Line_Charts_with_Matplotlib.ipynb      # Plotting all languages
│   ├── 08__Smoothing_out_Time_Series_Data.ipynb         # Rolling average smoothing
│   ├── 09__Quiz_18_Programming_Language_Data_Analysis.ipynb  # Course quiz
│   └── 10__Learning_Points_and_Summary.ipynb            # Summary of all techniques
│
├── practice/
│   └── A_01_Programming_Languages_Analysis.ipynb  # Student solution: full pipeline
│
├── data/
│   └── QueryResults.csv             # Stack Overflow monthly post counts by language tag
│
├── docs/
│   └── COURSE_NOTES.md              # Original exercise brief and key concepts
│
├── requirements.txt                 # pip packages with minimum versions
├── .gitignore
└── README.md
```

---

## 6. Notebook reference

### theory/

| Notebook | Key methods covered | Question answered |
|----------|--------------------|--------------------|
| `00__Overview.ipynb` | — | What does this day's analysis investigate? |
| `01__Download_and_Open_Starter_Notebook.ipynb` | `pd.read_csv()`, `df.head()` | Where does the data come from and how is it loaded? |
| `02__Preliminary_Data_Exploration.ipynb` | `df.shape`, `df.count()`, `df.info()` | How large is the dataset and is it complete? |
| `03__Analysis_by_Programming_Language.ipynb` | `groupby().sum()`, `sort_values()`, `idxmax()` | Which language has the most all-time posts? |
| `04__Data_Cleaning_Working_with_Timestamps.ipynb` | `pd.to_datetime()` | How do we convert date strings to datetime objects? |
| `05__Data_Manipulation_Pivoting_DataFrames.ipynb` | `pivot()`, `fillna()`, `isna().values.any()` | How do we reshape long data to wide for plotting? |
| `06__Data_Visualisation_with_Matplotlib.ipynb` | `plt.plot()`, `plt.figure()`, `plt.xlabel()`, `plt.ylim()` | How do we build and style a basic line chart? |
| `07__Multi_Line_Charts_with_Matplotlib.ipynb` | `for` loop over columns, `plt.legend()` | How do we plot all languages on a single chart? |
| `08__Smoothing_out_Time_Series_Data.ipynb` | `rolling(window=6).mean()` | How do we reduce noise to reveal long-term trends? |
| `09__Quiz_18_Programming_Language_Data_Analysis.ipynb` | — | Course quiz on all techniques above |
| `10__Learning_Points_and_Summary.ipynb` | — | What were the key techniques practised today? |

### practice/

| Notebook | Key methods covered | Question answered |
|----------|--------------------|--------------------|
| `A_01_Programming_Languages_Analysis.ipynb` | Full pipeline: `read_csv`, `groupby`, `to_datetime`, `pivot`, `fillna`, `plt.plot`, `rolling` | All of the above — end-to-end student solution |

---

## 7. Configuration reference

| Value | Location | Description |
|-------|----------|-------------|
| `"../data/QueryResults.csv"` | `practice/A_01_Programming_Languages_Analysis.ipynb` | Relative path to the CSV from the practice notebook |
| `figsize=(16, 10)` | practice notebook, cells 43–55 | Chart dimensions in inches |
| `fontsize=14` | practice notebook, tick and label calls | Axis label and tick font size |
| `plt.ylim(0, 35000)` | practice notebook | Y-axis ceiling for post count |
| `window=6` | practice notebook, `rolling()` call | Number of months averaged in the rolling mean |

---

## 8. Course context

100 Days of Code: The Complete Python Pro Bootcamp — Day 73 — topics: Pandas groupby/pivot, datetime parsing, Matplotlib multi-line charts, rolling averages.

See [docs/COURSE_NOTES.md](docs/COURSE_NOTES.md) for the original exercise brief and key concepts.

---

## 9. Dependencies

| Module | Used in | Purpose |
|--------|---------|---------|
| `pandas` | practice/, theory/ | Data loading, cleaning, groupby, pivot, rolling |
| `numpy` | practice/ (implicit via pandas) | Underlying numeric operations |
| `matplotlib` | practice/ | Line chart visualisation |
| `notebook` | all | Jupyter notebook runtime |
