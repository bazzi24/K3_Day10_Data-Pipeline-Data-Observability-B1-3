from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import re
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from core.config import Settings
from core.utils import normalize_whitespace, read_json, write_json


@dataclass(frozen=True)
class PaperRecord:
    paper_id: str
    title: str
    summary: str
    authors: list[str]
    categories: list[str]
    primary_category: str
    published: str
    updated: str
    abs_url: str
    pdf_url: str
    comment: str


def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value)
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("\n", " ")
    return normalize_whitespace(text)


def _extract_date_parts(value: Any) -> str:
    if not value:
        return ""
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return ""
        return text[:10]
    if isinstance(value, dict):
        date_parts = value.get("date-parts") or []
        if date_parts:
            first = date_parts[0]
            if first:
                year = first[0] if len(first) > 0 and first[0] is not None else None
                month = first[1] if len(first) > 1 and first[1] is not None else 1
                day = first[2] if len(first) > 2 and first[2] is not None else 1
                if year is not None:
                    return f"{year:04d}-{month:02d}-{day:02d}"
        date_time = value.get("date-time")
        if isinstance(date_time, str) and date_time:
            return date_time[:10]
    return ""


def _extract_authors(item: dict[str, Any]) -> list[str]:
    authors: list[str] = []
    for author in item.get("author") or []:
        if not isinstance(author, dict):
            continue
        family = _clean_text(author.get("family"))
        given = _clean_text(author.get("given"))
        name = _clean_text(author.get("name"))
        if name:
            authors.append(name)
        elif family or given:
            authors.append(f"{given} {family}".strip())
    return authors


def _extract_categories(item: dict[str, Any]) -> list[str]:
    subjects = item.get("subject") or []
    categories: list[str] = []
    if isinstance(subjects, list):
        for subject in subjects:
            if isinstance(subject, str):
                text = _clean_text(subject)
                if text:
                    categories.append(text)
    return categories


def _extract_url(item: dict[str, Any], preferred_type: str) -> str:
    for link in item.get("link") or []:
        if not isinstance(link, dict):
            continue
        link_type = _clean_text(link.get("content-type")).lower()
        if preferred_type == "pdf" and "pdf" in link_type:
            return _clean_text(link.get("URL"))
        if preferred_type == "abstract" and "text" in link_type:
            return _clean_text(link.get("URL"))
    return ""


def parse_crossref_payload(payload: dict) -> list[PaperRecord]:
    """Parse Crossref payload thanh list PaperRecord."""
    message = payload.get("message") or {}
    items = message.get("items") or []
    records: list[PaperRecord] = []

    for item in items:
        if not isinstance(item, dict):
            continue

        title = _clean_text(item.get("title") or "")
        if not title:
            continue

        paper_id = _clean_text(item.get("DOI") or item.get("URL") or "")
        if not paper_id:
            continue

        summary = _clean_text(item.get("abstract") or item.get("summary") or "")
        authors = _extract_authors(item)
        categories = _extract_categories(item)
        primary_category = categories[0] if categories else ""

        published = (
            _extract_date_parts(item.get("published-online"))
            or _extract_date_parts(item.get("published"))
            or _extract_date_parts(item.get("issued"))
            or _extract_date_parts(item.get("published-print"))
        )
        updated = (
            _extract_date_parts(item.get("updated"))
            or _extract_date_parts(item.get("indexed"))
            or _extract_date_parts(item.get("deposited"))
            or _extract_date_parts(item.get("created"))
            or published
        )
        if not published:
            published = _extract_date_parts(item.get("created")) or _extract_date_parts(item.get("issued")) or ""
        if not updated:
            updated = published

        abs_url = _clean_text(item.get("URL") or _extract_url(item, "abstract"))
        pdf_url = _clean_text(_extract_url(item, "pdf"))
        comment = ""

        records.append(
            PaperRecord(
                paper_id=paper_id,
                title=title,
                summary=summary,
                authors=authors,
                categories=categories,
                primary_category=primary_category,
                published=published,
                updated=updated,
                abs_url=abs_url,
                pdf_url=pdf_url,
                comment=comment,
            )
        )

    return records


def fetch_source_records(settings: Settings) -> list[PaperRecord]:
    """Goi source API, luu raw response, parse thanh records."""
    source_url = settings.source_api if settings.source_api.startswith("http") else "https://api.crossref.org/works"
    params = {
        "query.title": settings.source_query,
        "filter": settings.source_filter,
        "rows": settings.max_results,
    }
    query_string = urlencode(params, doseq=True)
    url = f"{source_url}?{query_string}" if query_string else source_url
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})

    payload: dict[str, Any] | None = None
    for attempt in range(3):
        try:
            with urlopen(request, timeout=30) as response:
                payload = json.loads(response.read().decode("utf-8"))
            break
        except (HTTPError, URLError, TimeoutError) as exc:
            if attempt == 2:
                payload = None
                break
            time.sleep(2**attempt)

    if payload is None:
        payload = read_json(settings.paths.raw_api_response) if settings.paths.raw_api_response.exists() else {"message": {"items": []}}

    write_json(settings.paths.raw_api_response, payload)
    records = parse_crossref_payload(payload)
    write_json(settings.paths.raw_records_json, [asdict(record) for record in records])
    return records


def load_raw_records(path: Path) -> list[PaperRecord]:
    """Doc JSON snapshot va map thanh `PaperRecord`."""
    if not path.exists():
        return []

    payload = read_json(path)
    if isinstance(payload, list):
        return [PaperRecord(**record) for record in payload if isinstance(record, dict)]
    if isinstance(payload, dict):
        items = payload.get("records") or payload.get("items") or (payload.get("message") or {}).get("items") or []
        return [PaperRecord(**record) for record in items if isinstance(record, dict)]
    return []
