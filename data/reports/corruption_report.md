# Corruption and Repair Comparison Report

## Experiment contract

- Baseline, corrupted and repaired states use the same evaluation set and retrieval configuration.
- Corrupted and repaired data are indexed in separate collections; baseline artifacts are not overwritten.
- Repair is rebuilt from the saved raw records and the normal cleaning pipeline, not by editing answers or metrics.

## Evaluation comparison

| Metric | Baseline | Corrupted | Repaired | Corrupted - baseline | Repaired - corrupted |
| --- | ---: | ---: | ---: | ---: | ---: |
| `retrieval_hit_rate` | 1.0000 | 0.0000 | 1.0000 | -1.0000 | 1.0000 |
| `mean_token_f1` | 1.0000 | 0.0386 | 0.3703 | -0.9614 | 0.3317 |
| `judge_accuracy` | 1.0000 | 0.0000 | 0.3000 | -1.0000 | 0.3000 |
| `mean_judge_score` | 5.0000 | 1.0000 | 2.2000 | -4.0000 | 1.2000 |

A negative `Corrupted - baseline` value indicates degradation for these higher-is-better metrics. A positive
`Repaired - corrupted` value indicates recovery. Exact recovery is not guaranteed when ranking contains ties or
when an external judge is non-deterministic; the answer artifacts should be inspected before drawing conclusions.

## Corrupted data quality

```json
{
  "report_name": "corrupted_quality",
  "status": "FAIL",
  "total_rows": 22,
  "metrics": {
    "null_paper_ids": 0,
    "duplicate_paper_ids": 2,
    "null_titles": 0,
    "null_summaries": 3,
    "short_summaries": 3,
    "stale_rows": 4,
    "freshness_threshold_days": 180
  },
  "checks": {
    "row_count_sufficient": true,
    "paper_id_no_nulls": true,
    "paper_id_unique": false,
    "title_no_nulls": true,
    "summary_no_nulls": false,
    "summary_adequate_length": false,
    "freshness_valid": false
  },
  "failed_rules": [
    "paper_id_unique",
    "summary_no_nulls",
    "summary_adequate_length",
    "freshness_valid"
  ]
}
```

## Repaired data quality

```json
{
  "report_name": "repaired_quality",
  "status": "PASS",
  "total_rows": 24,
  "metrics": {
    "null_paper_ids": 0,
    "duplicate_paper_ids": 0,
    "null_titles": 0,
    "null_summaries": 0,
    "short_summaries": 0,
    "stale_rows": 0,
    "freshness_threshold_days": 180
  },
  "checks": {
    "row_count_sufficient": true,
    "paper_id_no_nulls": true,
    "paper_id_unique": true,
    "title_no_nulls": true,
    "summary_no_nulls": true,
    "summary_adequate_length": true,
    "freshness_valid": true
  },
  "failed_rules": []
}
```

## Corrupted freshness

```json
{
  "latest_published": "2026-07-02",
  "oldest_published": "2016-08-08",
  "stale_rows": 4,
  "total_rows": 22,
  "freshness_threshold_days": 180,
  "is_fresh": false
}
```

## Repaired freshness

```json
{
  "latest_published": "2026-08-05",
  "oldest_published": "2026-02-26",
  "stale_rows": 0,
  "total_rows": 24,
  "freshness_threshold_days": 180,
  "is_fresh": true
}
```

## Evidence and interpretation

Use `data/results/corruption_log.json` to trace each injected defect to its paper IDs. Detailed retrieval hits,
answers and judge results are stored separately for corrupted and repaired states under `data/results/`.
Conclusions should only claim an impact when the metric delta or answer-level evidence above supports it.
