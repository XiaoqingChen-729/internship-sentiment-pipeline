# Monitoring Layer — Google Play Sentiment Pipeline

## Health Classification

Each pipeline run is classified as HEALTHY, WARNING, or FAILING.
FAILING takes priority over WARNING when both conditions are present.

| Status | Condition |
|--------|-----------|
| FAILING | Any app fetch fails, raw_review != cleaned_review, or orphan reviews exist |
| WARNING | Duplicate rate > 30%, low-signal rate > 60%, or any app missing finished_at |
| HEALTHY | All checks pass with no issues or warnings |

---

## Checks and Thresholds

| Check | Threshold | Classification |
|-------|-----------|----------------|
| App fetch failure | Any app returns failed status | FAILING |
| Table mismatch | raw_review count != cleaned_review count | FAILING |
| Orphan reviews | Any review with no ingestion_run record | FAILING |
| High duplicate rate | > 30% of reviews flagged as duplicate | WARNING |
| High low-signal rate | > 60% of reviews flagged as low_signal | WARNING |
| Missing finished_at | Any app run missing a completion timestamp | WARNING |

---

## Test Cases

| Test | Simulated Condition | Expected | Actual | Report File |
|------|---------------------|----------|--------|-------------|
| 1 | Normal run — all 20 apps healthy | HEALTHY | HEALTHY | run_summary_20260724_182558.md |
| 2 | One app fetch failed (invalid app ID) | FAILING | FAILING | run_summary_20260724_201943.md |
| 3 | Table mismatch (one cleaned_review deleted) | FAILING | FAILING | run_summary_20260724_202148.md |
| 4 | High duplicate rate (forced to 35%) | WARNING | WARNING | run_summary_20260724_204834.md |
| 5 | High low-signal rate (forced to 65%) | WARNING | WARNING | run_summary_20260724_204930.md |
| 6 | Missing finished_at (one app set to NULL) | WARNING | WARNING | run_summary_20260724_212111.md |

All six test cases passed as expected.

---

## Known Limitations

- **batch_id is time-based:** If two pipeline runs start within the same second, batch_id collision could occur. In practice this is unlikely but worth noting.
- **Duplicate rate threshold is run-level:** The duplicate check uses flags from the current batch only, not the full database history. A low-insertion run (mostly skipped records) will always show a low duplicate rate even if the underlying data has high repetition.
- **Non-English rate not currently thresholded:** non_english flags are reported but do not trigger WARNING. If the pipeline expands to non-English markets this should be added.
- **finished_at precision is rounded to seconds:** Per-app runtime is stored as integer seconds, so very fast runs (under 1 second) appear as 0 or 1 second.