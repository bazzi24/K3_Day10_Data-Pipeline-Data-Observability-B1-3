# Phase 1 Baseline Report: Data Pipeline & RAG Evaluation

## 1. Executive Summary & Source Ingestion
- **Source API:** Crossref REST API
- **Search Query:** `agentic retrieval augmented generation large language model`
- **Raw Records Ingested:** 25
- **Clean Records Modeled:** 24

## 2. RAG Baseline Performance Metrics
Evaluation conducted on fixed frozen test set (10 samples):

| Metric | Baseline Score | Target / Ideal | Status |
| :--- | :--- | :--- | :--- |
| **Retrieval Hit Rate** | `100.00%` | >= 80.0% | ✅ PASS |
| **Mean Token F1** | `0.8800` | Higher is better | ✅ OK |
| **LLM Judge Accuracy** | `100.00%` | >= 70.0% | ✅ PASS |
| **Mean Judge Score** | `4.70 / 5.0` | >= 3.50 | ✅ PASS |

## 3. Data Observability & Quality Signals

### Data Quality Checks: **PASS**
- **Row Count Check:** PASS
- **Paper ID Integrity (No Nulls / Unique):** PASS
- **Title & Summary Completeness:** PASS
- **Summary Length Threshold (>=100 chars):** PASS

### Data Freshness Monitoring
- **Freshness Status:** ✅ FRESH
- **Latest Published Date:** `2026-08-05`
- **Oldest Published Date:** `2026-02-26`
- **Stale Records Count:** `0`

---
*Report generated automatically by Data Observability Pipeline.*
