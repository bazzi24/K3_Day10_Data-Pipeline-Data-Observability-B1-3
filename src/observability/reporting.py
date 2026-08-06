from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from core.utils import write_text


def generate_phase1_report(
    report_path: str | Path,
    source_summary: dict[str, Any],
    metrics: dict[str, Any],
    quality: dict[str, Any],
    freshness: dict[str, Any],
) -> None:
    """Viết markdown report cho baseline phase."""
    total_raw = source_summary.get("total_raw_records", source_summary.get("raw_records", source_summary.get("total_records", "N/A")))
    total_clean = source_summary.get("total_clean_records", source_summary.get("clean_rows", quality.get("total_rows", "N/A")))

    hit_rate = metrics.get("retrieval_hit_rate", 0.0)
    token_f1 = metrics.get("mean_token_f1", 0.0)
    judge_acc = metrics.get("judge_accuracy", 0.0)
    judge_score = metrics.get("mean_judge_score", 0.0)
    samples = metrics.get("samples", 0)

    q_status = quality.get("status", "UNKNOWN")
    q_checks = quality.get("checks", {})

    is_fresh = freshness.get("is_fresh", False)
    latest_pub = freshness.get("latest_published", "N/A")
    oldest_pub = freshness.get("oldest_published", "N/A")
    stale_rows = freshness.get("stale_rows", 0)

    md = f"""# Phase 1 Baseline Report: Data Pipeline & RAG Evaluation

## 1. Executive Summary & Source Ingestion
- **Source API:** {source_summary.get("source_api", "Crossref REST API")}
- **Search Query:** `{source_summary.get("query", source_summary.get("source_query", "N/A"))}`
- **Raw Records Ingested:** {total_raw}
- **Clean Records Modeled:** {total_clean}

## 2. RAG Baseline Performance Metrics
Evaluation conducted on fixed frozen test set ({samples} samples):

| Metric | Baseline Score | Target / Ideal | Status |
| :--- | :--- | :--- | :--- |
| **Retrieval Hit Rate** | `{hit_rate:.2%}` | >= 80.0% | {"PASS" if hit_rate >= 0.8 else "ATTENTION"} |
| **Mean Token F1** | `{token_f1:.4f}` | Higher is better | OK |
| **LLM Judge Accuracy** | `{judge_acc:.2%}` | >= 70.0% | {"PASS" if judge_acc >= 0.7 else "ATTENTION"} |
| **Mean Judge Score** | `{judge_score:.2f} / 5.0` | >= 3.50 | {"PASS" if judge_score >= 3.5 else "ATTENTION"} |

## 3. Data Observability & Quality Signals

### Data Quality Checks: **{q_status}**
- **Row Count Check:** {"PASS" if q_checks.get("row_count_sufficient") else "FAIL"}
- **Paper ID Integrity (No Nulls / Unique):** {"PASS" if q_checks.get("paper_id_no_nulls") and q_checks.get("paper_id_unique") else "FAIL"}
- **Title & Summary Completeness:** {"PASS" if q_checks.get("title_no_nulls") and q_checks.get("summary_no_nulls") else "FAIL"}
- **Summary Length Threshold (>=100 chars):** {"PASS" if q_checks.get("summary_adequate_length") else "FAIL"}

### Data Freshness Monitoring
- **Freshness Status:** {"FRESH" if is_fresh else "STALE DETECTED"}
- **Latest Published Date:** `{latest_pub}`
- **Oldest Published Date:** `{oldest_pub}`
- **Stale Records Count:** `{stale_rows}`

---
*Report generated automatically by Data Observability Pipeline.*
"""
    write_text(Path(report_path), md)


def generate_corruption_report(
    report_path: str | Path,
    baseline_metrics: dict[str, Any],
    corrupted_metrics: dict[str, Any],
    repaired_metrics: dict[str, Any],
    corrupted_quality: dict[str, Any],
    repaired_quality: dict[str, Any],
    corrupted_freshness: dict[str, Any],
    repaired_freshness: dict[str, Any],
) -> None:
    """Write an evidence-based baseline/corrupted/repaired comparison."""
    metric_names = ("retrieval_hit_rate", "mean_token_f1", "judge_accuracy", "mean_judge_score")

    def number(payload: dict[str, Any], key: str) -> float | None:
        value = payload.get(key)
        return float(value) if isinstance(value, (int, float)) else None

    def fmt(value: float | None) -> str:
        return "N/A" if value is None else f"{value:.4f}"

    rows = []
    for name in metric_names:
        baseline = number(baseline_metrics, name)
        corrupted = number(corrupted_metrics, name)
        repaired = number(repaired_metrics, name)
        degradation = None if baseline is None or corrupted is None else corrupted - baseline
        recovery = None if repaired is None or corrupted is None else repaired - corrupted
        rows.append(
            f"| `{name}` | {fmt(baseline)} | {fmt(corrupted)} | {fmt(repaired)} "
            f"| {fmt(degradation)} | {fmt(recovery)} |"
        )

    def json_block(payload: dict[str, Any]) -> str:
        return json.dumps(payload, indent=2, ensure_ascii=False, default=str)

    report = f"""# Corruption and Repair Comparison Report

## Experiment contract

- Baseline, corrupted and repaired states use the same evaluation set and retrieval configuration.
- Corrupted and repaired data are indexed in separate collections; baseline artifacts are not overwritten.
- Repair is rebuilt from the saved raw records and the normal cleaning pipeline, not by editing answers or metrics.

## Evaluation comparison

| Metric | Baseline | Corrupted | Repaired | Corrupted - baseline | Repaired - corrupted |
| --- | ---: | ---: | ---: | ---: | ---: |
{chr(10).join(rows)}

A negative `Corrupted - baseline` value indicates degradation for these higher-is-better metrics. A positive
`Repaired - corrupted` value indicates recovery. Exact recovery is not guaranteed when ranking contains ties or
when an external judge is non-deterministic; the answer artifacts should be inspected before drawing conclusions.

## Corrupted data quality

```json
{json_block(corrupted_quality)}
```

## Repaired data quality

```json
{json_block(repaired_quality)}
```

## Corrupted freshness

```json
{json_block(corrupted_freshness)}
```

## Repaired freshness

```json
{json_block(repaired_freshness)}
```

## Evidence and interpretation

Use `data/results/corruption_log.json` to trace each injected defect to its paper IDs. Detailed retrieval hits,
answers and judge results are stored separately for corrupted and repaired states under `data/results/`.
Conclusions should only claim an impact when the metric delta or answer-level evidence above supports it.
"""
    write_text(Path(report_path), report)
