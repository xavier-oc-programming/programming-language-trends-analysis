# Course Notes — Day 73: Data Visualisation with Matplotlib (Programming Languages)

## Course Context

**Course**: 100 Days of Code: The Complete Python Pro Bootcamp  
**Day**: 73  
**Topics**: Pandas data manipulation, datetime handling, pivoting DataFrames, Matplotlib visualisation, rolling averages

---

## Exercise Brief

Analyse the popularity of programming languages over time using Stack Overflow post data.

The dataset is a monthly count of Stack Overflow posts tagged with each programming language, from July 2008 onwards. The SQL query used to generate it on Stack Exchange Data Explorer:

```sql
select dateadd(month, datediff(month, 0, q.CreationDate), 0) m, TagName, count(*)
from PostTags pt
join Posts q on q.Id=pt.PostId
join Tags t on t.Id=pt.TagId
where TagName in (
  'java','c','c++','python','c#','javascript','assembly','php',
  'perl','ruby','visual basic','swift','r','object-c','scratch',
  'go','swift','delphi'
)
and q.CreationDate < dateadd(month, datediff(month, 0, getdate()), 0)
group by dateadd(month, datediff(month, 0, q.CreationDate), 0), TagName
order by dateadd(month, datediff(month, 0, q.CreationDate), 0)
```

Source: https://data.stackexchange.com/stackoverflow/query/675441/popular-programming-languages-per-over-time-eversql-com

---

## Key Concepts Covered

### 1. Preliminary Data Exploration
- `pd.read_csv()` with explicit column names using `names=` and `header=0`
- `df.head()`, `df.tail()`, `df.shape`, `df.count()`, `df.info()`

### 2. Grouped Aggregation
- `groupby("TAG")["POSTS"].sum()` — total posts per language
- `groupby("TAG")["DATE"].count()` — months of data per language
- `sort_values(ascending=False)` — ranking by popularity

### 3. Working with Timestamps
- `pd.to_datetime(df.DATE)` — convert string dates to datetime objects
- Enables time-series plotting on an ordered x-axis

### 4. Pivoting DataFrames
- `df.pivot(index='DATE', columns='TAG', values='POSTS')` — wide-format reshape
- Each programming language becomes its own column
- `fillna(0)` — replace NaN (missing months) with zero
- `isna().values.any()` — verify no missing values remain

### 5. Data Visualisation with Matplotlib
- `plt.figure(figsize=(16, 10))` — set chart size
- `plt.plot(x, y)` — basic line chart
- `plt.xticks(fontsize=...)`, `plt.yticks(fontsize=...)` — axis tick styling
- `plt.xlabel(...)`, `plt.ylabel(...)` — axis labels
- `plt.ylim(0, 35000)` — axis limits
- Iterating with a `for` loop to plot all languages at once
- `label=column.name` + `plt.legend(fontsize=16)` — auto-legend

### 6. Smoothing Time-Series Data
- `df.rolling(window=6).mean()` — 6-month rolling average
- Reduces noise and reveals long-term trends
- Window size controls the degree of smoothing

---

## Analysis Questions Answered

- Which programming language has the highest all-time Stack Overflow post count?
  - **JavaScript** (2,526,031 posts)
- How many months of data exist per language? Which language has the fewest?
  - **Go** had the fewest entries (194 months), as it was introduced later
- How has each language's popularity changed from 2008 to the present?
  - Python shows the steepest growth trajectory; JavaScript peaked mid-period
- How does smoothing change our interpretation of the trends?
  - Rolling averages reveal that Python overtook Java and JavaScript in recent years
