from __future__ import annotations

from datetime import datetime

import pandas as pd

from core.utils import write_json


def _rebuild_text_for_embedding(row: pd.Series) -> str:
    parts = [str(row.get("title", "")), str(row.get("summary", "")), str(row.get("authors_joined", "")), str(row.get("categories_joined", ""))]
    return " | ".join(part for part in parts if part)


def corrupt_clean_dataframe(df: pd.DataFrame, output_log_path) -> pd.DataFrame:
    """Simulate nhieu dang data corruption va ghi log."""
    corrupted = df.copy()
    if corrupted.empty:
        write_json(output_log_path, {"actions": [], "row_count": 0})
        return corrupted

    actions: list[dict[str, object]] = []
    row_count = len(corrupted)

    drop_count = max(1, min(3, row_count // 6))
    if drop_count > 0:
        corrupted = corrupted.iloc[:-drop_count].copy()
        actions.append({"action": "drop_latest_rows", "count": drop_count})

    if len(corrupted) > 0:
        blank_count = max(1, min(3, len(corrupted) // 4))
        blank_indices = corrupted.index[:blank_count]
        corrupted.loc[blank_indices, "summary"] = ""
        actions.append({"action": "blank_summary", "count": len(blank_indices)})

    if len(corrupted) > 0:
        noise_count = max(1, min(3, len(corrupted) // 4))
        noise_indices = corrupted.index[:noise_count]
        corrupted.loc[noise_indices, "title"] = corrupted.loc[noise_indices, "title"].astype(str) + " [corrupted-noise]"
        corrupted.loc[noise_indices, "summary"] = corrupted.loc[noise_indices, "summary"].astype(str) + " noise-token inserted for corruption test."
        actions.append({"action": "inject_noise", "count": len(noise_indices)})

    if len(corrupted) > 0:
        truncate_count = max(1, min(3, len(corrupted) // 4))
        truncate_indices = corrupted.index[:truncate_count]
        corrupted.loc[truncate_indices, "title"] = corrupted.loc[truncate_indices, "title"].astype(str).str[:20]
        actions.append({"action": "truncate_title", "count": len(truncate_indices)})

    if len(corrupted) > 0:
        stale_count = max(1, min(3, len(corrupted) // 4))
        stale_indices = corrupted.index[:stale_count]
        corrupted.loc[stale_indices, "published"] = "2000-01-01"
        corrupted.loc[stale_indices, "updated"] = "2000-01-01"
        corrupted.loc[stale_indices, "age_days"] = (datetime.now().date() - datetime(2000, 1, 1).date()).days
        actions.append({"action": "stale_published_date", "count": len(stale_indices)})

    if len(corrupted) > 0:
        duplicate_count = max(1, min(2, len(corrupted) // 4))
        duplicated_rows = corrupted.head(duplicate_count).copy()
        corrupted = pd.concat([corrupted, duplicated_rows], ignore_index=True)
        actions.append({"action": "add_duplicate_rows", "count": len(duplicated_rows)})

    if "summary_chars" in corrupted.columns:
        corrupted["summary_chars"] = corrupted["summary"].fillna("").astype(str).str.len()
    if "text_for_embedding" in corrupted.columns:
        corrupted["text_for_embedding"] = corrupted.apply(_rebuild_text_for_embedding, axis=1)

    write_json(output_log_path, {"actions": actions, "row_count": int(len(corrupted))})
    return corrupted.reset_index(drop=True)
