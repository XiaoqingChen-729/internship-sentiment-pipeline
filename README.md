# Sentiment Analysis Pipeline — Internship Project

This repository documents the end-to-end development of a sentiment analysis
data pipeline, built as part of an internship project. The goal is to identify,
evaluate, and ingest user-generated review data from public platforms, and to
prepare that data for downstream sentiment modeling and product insight generation.

The project progressed through five stages: data source assessment, data
collection and EDA, pipeline and database implementation, monitoring, and
feature engineering with a baseline model evaluation.

---

## Repository Structure

```
/
├── internship-sentiment-pipeline/   # Stage 1: Data source feasibility assessment
│   ├── test_amazon/
│   │   ├── amazon_static.py
│   │   ├── amazon_improvedheader.py
│   │   └── amazon_internalapi.py
│   ├── test_googleplay/
│   │   └── googleplay.py
│   └── README.md
│
└── googlemap/                       # Stages 2-5: Pipeline, EDA, monitoring, modeling
    ├── schema/
    │   └── schema.sql
    ├── monitoring/
    │   ├── README.md
    │   └── run_summary_*.md
    ├── data/                        # excluded from version control
    ├── eda_output/
    ├── pipeline.py
    ├── monitor.py
    ├── collect_review.py
    ├── eda.py
    ├── feature_engineering.py
    ├── baseline_analysis.py
    ├── eda_result.md
    ├── feature_engineering.md
    ├── baseline_results.md
    └── features_sample.csv
```

---

## Stage 1 — Data Source Feasibility Assessment

**Folder:** `internship-sentiment-pipeline/`

Evaluated potential data sources for the pipeline and tested their practical
ingestion feasibility. Two candidate sources were assessed in depth.

**Google Play Store:**
- Fully accessible via `google-play-scraper` with no authentication required
- Stable pagination with no rate-limiting observed
- Core fields (review text, rating, timestamp) 100% complete across all tested apps
- Selected as the primary data source

**Amazon:**
- Reviews are dynamically rendered via JavaScript and not accessible through
  standard HTTP requests
- Internal API identified via browser DevTools requires session-bound parameters
  that expire immediately, making recurring collection infeasible
- Explicit Terms of Service restrictions prohibit scraping and ML use of content

---

## Stage 2 — Data Collection and EDA

**Folder:** `googlemap/` | **Scripts:** `collect_review.py`, `eda.py`
**Full report:** [`googlemap/eda_result.md`](googlemap/eda_result.md)

Collected 20,000 reviews from 20 top-ranked Google Play Store apps across
16 industry categories and conducted a detailed EDA to assess data quality.

Key findings:
- Core fields are 100% complete across all 20 apps
- Rating distribution is heavily polarized — 55.9% five-star, 27.8% one-star
- 41.8% of reviews are low-signal (under 20 characters)
- 19.5% of review content is duplicated
- 94.1% of reviews are in English
- All reviews fall within a single month, limiting temporal depth

---

## Stage 3 — Pipeline and Database Implementation

**Folder:** `googlemap/` | **Scripts:** `pipeline.py`, `schema/schema.sql`

Designed a six-table PostgreSQL schema and built a recurring ingestion pipeline
that collects, cleans, flags, and stores reviews in a structured database.

**Schema tables:**

| Table | Description |
|-------|-------------|
| category | App industry classifications |
| app | Target apps and metadata |
| ingestion_run | Records each pipeline execution per app |
| raw_review | Original reviews as collected |
| quality_flag | Data quality signals per review |
| cleaned_review | Processed fields for downstream analysis |

**Pipeline capabilities:**
- Collects 1,000 reviews per app across 20 apps per run
- Deduplicates by review ID to prevent duplicate records
- Applies quality flags for low-signal, duplicate, and non-English content
- Records batch ID and runtime per ingestion run for traceability
- Validated across two repeated runs: 19,957 existing records correctly
  skipped, 43 new reviews captured in the second run

---

## Stage 4 — Monitoring Layer

**Folder:** `googlemap/monitoring/` | **Script:** `monitor.py`
**Documentation:** [`googlemap/monitoring/README.md`](googlemap/monitoring/README.md)

Built a standalone monitoring script that queries the database after each
pipeline run and generates a timestamped markdown report.

**Health classification:**

| Status | Condition |
|--------|-----------|
| HEALTHY | All checks pass with no issues or warnings |
| WARNING | Duplicate rate > 30%, low-signal rate > 60%, or missing finished_at |
| FAILING | Any app fetch fails, table mismatch, or orphan reviews exist |

Validated against six controlled test cases covering all three health states.

---

## Stage 5 — Feature Engineering and Baseline Analysis

**Folder:** `googlemap/` | **Scripts:** `feature_engineering.py`, `baseline_analysis.py`
**Documentation:** [`googlemap/feature_engineering.md`](googlemap/feature_engineering.md),
[`googlemap/baseline_results.md`](googlemap/baseline_results.md)

Generated an analysis-ready feature dataset and evaluated whether the current
features provide useful signal for sentiment classification.

**Features generated (19 total):**
- Structural: review length, rating group, date, weekday, month, developer reply
- Quality: low-signal, duplicate, language indicators
- Topic signals: service, login, price, refund, update
- Sentiment signals: positive keywords, negative keywords

**Baseline model results:**

| Model | Macro F1 |
|-------|----------|
| Majority Class Baseline | 0.263 |
| Logistic Regression | 0.491 |

The Logistic Regression model achieves 1.87x the Macro F1 of the majority
class baseline, suggesting that the engineered features carry meaningful signal.
Performance is strongest on positive reviews (F1=0.777) and weakest on neutral
reviews (F1=0.111), which represent only 4.4% of the dataset.

---

## Key Limitations

- **Temporal coverage:** All data falls within a single collection period.
  Recurring ingestion over time is needed to build historical depth.
- **Label quality:** Star ratings are used as weak sentiment labels.
  3-star reviews do not represent a reliable neutral sentiment class.
- **Keyword coverage:** 95.5% of model prediction errors occur on reviews
  with no keyword signals present, highlighting the core limitation of
  the current feature approach.
- **Generalization:** The baseline model was evaluated on a stratified split
  within the same app collection and should not be assumed to generalize
  to new apps or domains.

---

## Recommended Future Work

- Replace or supplement keyword signals with TF-IDF or text embeddings
  to improve coverage for reviews without keyword signals
- Revisit the neutral class definition or remove it if reliable neutral
  labels cannot be obtained from star ratings alone
- Implement negation-aware feature extraction to reduce misclassification
  from phrases like "not great" or "can't login"
- Run controlled feature ablation experiments to validate which signals
  genuinely improve predictive performance
- Evaluate on held-out apps to measure cross-app generalization
