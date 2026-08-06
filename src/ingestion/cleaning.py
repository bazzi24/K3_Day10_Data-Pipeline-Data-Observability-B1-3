from __future__ import annotations

from datetime import datetime
import re

import pandas as pd

from core.utils import normalize_whitespace
from ingestion.crossref import PaperRecord


def _parse_date(value: str) -> datetime | None:
    if not value:
        return None
    text = value.strip()
    if not text:
        return None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y-%m", "%Y"):
        try:
            return datetime.strptime(text[:10], fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None


def _normalize_text(value: str | None) -> str:
    if value is None:
        return ""
    cleaned = re.sub(r"<[^>]+>", " ", str(value))
    cleaned = cleaned.replace("\n", " ")
    cleaned = normalize_whitespace(cleaned)
    if cleaned.startswith("['") and cleaned.endswith("']"):
        cleaned = cleaned[2:-2]
    return normalize_whitespace(cleaned)


def build_clean_dataframe(records: list[PaperRecord], run_date: datetime) -> pd.DataFrame:
    """Clean raw records thanh dataframe san sang de embed."""
    rows: list[dict[str, object]] = []
    for record in records:
        title = _normalize_text(record.title)
        summary = _normalize_text(record.summary) or "No summary available."
        authors = [a for a in (_normalize_text(author) for author in record.authors) if a]
        categories = [c for c in (_normalize_text(category) for category in record.categories) if c]
        primary_category = _normalize_text(record.primary_category) or (categories[0] if categories else "")
        published = _normalize_text(record.published)
        updated = _normalize_text(record.updated) or published

        published_dt = _parse_date(published)
        if published_dt is None:
            published_dt = _parse_date(updated)
        if published_dt is None:
            published_dt = run_date

        age_days = int((run_date.date() - published_dt.date()).days)
        authors_joined = "; ".join(authors)
        categories_joined = "; ".join(categories)
        summary_chars = len(summary)
        text_for_embedding = " | ".join(
            part for part in [title, summary, authors_joined, categories_joined, primary_category] if part
        )

        rows.append(
            {
                "paper_id": _normalize_text(record.paper_id),
                "title": title,
                "summary": summary,
                "authors": authors,
                "categories": categories,
                "primary_category": primary_category,
                "authors_joined": authors_joined,
                "categories_joined": categories_joined,
                "published": published,
                "updated": updated,
                "abs_url": _normalize_text(record.abs_url),
                "pdf_url": _normalize_text(record.pdf_url),
                "comment": _normalize_text(record.comment),
                "summary_chars": summary_chars,
                "age_days": age_days,
                "text_for_embedding": text_for_embedding,
            }
        )

    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame(
            columns=[
                "paper_id",
                "title",
                "summary",
                "authors",
                "categories",
                "primary_category",
                "authors_joined",
                "categories_joined",
                "published",
                "updated",
                "abs_url",
                "pdf_url",
                "comment",
                "summary_chars",
                "age_days",
                "text_for_embedding",
            ]
        )

    df = df.dropna(subset=["paper_id", "title"]).copy()
    df = df.drop_duplicates(subset=["paper_id"], keep="first")
    df["summary_chars"] = df["summary_chars"].astype(int)
    df["age_days"] = df["age_days"].astype(int)
    df = df.sort_values(["published", "title"], ascending=[False, True], kind="mergesort").reset_index(drop=True)
    return df
