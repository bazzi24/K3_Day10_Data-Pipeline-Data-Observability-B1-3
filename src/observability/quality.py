from pathlib import Path
from typing import Any

import pandas as pd

from core.config import Settings
from core.utils import write_json


def run_data_quality_checks(df: pd.DataFrame, settings: Settings, report_name: str) -> dict[str, Any]:
    """Tạo bộ data quality checks.

    1. Check row count.
    2. Check `paper_id` not null và unique.
    3. Check `title` not null.
    4. Check độ dài `summary`.
    5. Check freshness bằng `age_days`.
    6. Ghi kết quả vào `data/quality/`.
    """
    total_rows = len(df)
    min_row_threshold = 1

    row_count_check = total_rows >= min_row_threshold

    if "paper_id" in df.columns:
        null_paper_ids = int(df["paper_id"].isnull().sum())
        duplicate_paper_ids = int(df["paper_id"].duplicated().sum())
    else:
        null_paper_ids = total_rows
        duplicate_paper_ids = 0

    if "title" in df.columns:
        null_titles = int(df["title"].isnull().sum() + (df["title"].astype(str).str.strip() == "").sum())
    else:
        null_titles = total_rows

    if "summary" in df.columns:
        null_summaries = int(df["summary"].isnull().sum() + (df["summary"].astype(str).str.strip() == "").sum())
        short_summaries = int((df["summary"].astype(str).str.strip().str.len() < 100).sum())
    else:
        null_summaries = total_rows
        short_summaries = total_rows

    if "age_days" in df.columns:
        stale_rows = int((df["age_days"] > settings.freshness_threshold_days).sum())
    else:
        stale_rows = 0

    checks = {
        "row_count_sufficient": row_count_check,
        "paper_id_no_nulls": null_paper_ids == 0,
        "paper_id_unique": duplicate_paper_ids == 0,
        "title_no_nulls": null_titles == 0,
        "summary_no_nulls": null_summaries == 0,
        "summary_adequate_length": short_summaries == 0,
        "freshness_valid": stale_rows == 0,
    }

    all_passed = all(checks.values())
    status = "PASS" if all_passed else "FAIL"

    failed_rules = [check_name for check_name, passed in checks.items() if not passed]

    report = {
        "report_name": report_name,
        "status": status,
        "total_rows": total_rows,
        "metrics": {
            "null_paper_ids": null_paper_ids,
            "duplicate_paper_ids": duplicate_paper_ids,
            "null_titles": null_titles,
            "null_summaries": null_summaries,
            "short_summaries": short_summaries,
            "stale_rows": stale_rows,
            "freshness_threshold_days": settings.freshness_threshold_days,
        },
        "checks": checks,
        "failed_rules": failed_rules,
    }

    out_path = settings.paths.quality_dir / f"{report_name}.json"
    write_json(out_path, report)
    return report


def build_freshness_report(df: pd.DataFrame, settings: Settings, report_path: str | Path) -> dict[str, Any]:
    """Tổng hợp freshness report.

    1. Tìm latest và oldest published date.
    2. Đếm số dòng stale.
    3. Tạo payload: latest_published, oldest_published, stale_rows, total_rows, is_fresh.
    4. Ghi JSON report.
    """
    total_rows = len(df)

    if total_rows > 0 and "published" in df.columns and not df["published"].isnull().all():
        published_series = df["published"].dropna().astype(str).str.strip()
        latest_published = str(published_series.max()) if not published_series.empty else "N/A"
        oldest_published = str(published_series.min()) if not published_series.empty else "N/A"
    else:
        latest_published = "N/A"
        oldest_published = "N/A"

    if "age_days" in df.columns:
        stale_rows = int((df["age_days"] > settings.freshness_threshold_days).sum())
    else:
        stale_rows = 0

    is_fresh = (stale_rows == 0) and (total_rows > 0)

    report = {
        "latest_published": latest_published,
        "oldest_published": oldest_published,
        "stale_rows": stale_rows,
        "total_rows": total_rows,
        "freshness_threshold_days": settings.freshness_threshold_days,
        "is_fresh": is_fresh,
    }

    out_p = Path(report_path)
    write_json(out_p, report)
    return report

