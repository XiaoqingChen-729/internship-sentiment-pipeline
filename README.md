# Sentiment Analysis Pipeline — Internship Project
 
This repository documents the development of a sentiment analysis data pipeline, built as part of an internship project. The goal is to identify, evaluate, and ingest user-generated review data from public platforms to support downstream sentiment modeling and product insight generation.
 
The project is organized into two modules, each contained in its own folder.
 
---
 
## internship-sentiment-pipeline
 
**Module 1 — Data Source Feasibility Assessment**
 
This module evaluates potential data sources for the pipeline and tests their practical ingestion feasibility. Two candidate sources were assessed in depth: Google Play Store and Amazon.
 
Key findings:
- Google Play Store reviews are fully accessible via `google-play-scraper` with no authentication required, stable pagination, and 100% completeness on core fields
- Amazon reviews are blocked by JavaScript dynamic rendering and session-bound API parameters, making recurring automated collection infeasible
- Google Play Store was selected as the primary data source based on technical accessibility, data quality, and commercial relevance
---
 
## googlemap
 
**Module 2 — Data Collection & Exploratory Data Analysis**
 
This module collects a 20,000-review sample from 20 top-ranked Google Play Store apps across 16 industry categories, and conducts a detailed EDA to assess data quality and pipeline readiness.
 
Key findings:
- Core fields (review text, rating, timestamp) are 100% complete across all 20 apps and 16 categories
- Rating distribution is heavily polarized — 55.9% five-star and 27.8% one-star — indicating significant bias that will need to be addressed during model training
- 41.8% of reviews are low-signal (under 20 characters), with notable variation across app categories; service and e-commerce apps produce the most detailed reviews
See [`googlemap/eda_result.md`](googlemap/eda_result.md) for the full EDA report.