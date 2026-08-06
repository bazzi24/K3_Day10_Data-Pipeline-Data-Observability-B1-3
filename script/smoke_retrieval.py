from __future__ import annotations

import json
import os
from dataclasses import replace
from pathlib import Path

import pandas as pd

from core.config import load_settings
from ingestion.cleaning import build_clean_dataframe
from ingestion.crossref import load_raw_records
from retrieval.index import LocalEmbeddingIndex


def _pick_settings():
    settings = load_settings()
    if settings.llm_provider == "gemini" and not settings.google_api_key and settings.openai_api_key:
        model_name = os.getenv("SMOKE_LLM_MODEL", "gpt-4o-mini")
        settings = replace(settings, llm_provider="openai", model_name=model_name)
    return settings


def _load_clean_df(settings) -> pd.DataFrame:
    raw_records = load_raw_records(settings.paths.raw_records_json)
    if not raw_records:
        raise RuntimeError(f"No raw records found at {settings.paths.raw_records_json}")
    return build_clean_dataframe(raw_records, run_date=pd.Timestamp.now(tz="UTC").to_pydatetime())


def _normalize_exact_value(value: str) -> str:
    return value.strip().strip("[]").strip("'").strip()


def main() -> None:
    settings = _pick_settings()
    clean_df = _load_clean_df(settings)

    config = LocalEmbeddingIndex.prepare_config(
        settings,
        clean_path=settings.paths.clean_json,
        embeddings_output_path=settings.paths.embeddings_json,
    )
    print(json.dumps(
        {
            "collection_name": config.collection_name,
            "persist_path": str(config.persist_path),
            "embeddings_output_path": str(config.embeddings_output_path),
            "input_path": str(config.input_path) if config.input_path else None,
            "row_count": len(clean_df),
            "required_columns_present": all(
                column in clean_df.columns
                for column in [
                    "paper_id",
                    "title",
                    "text_for_embedding",
                    "published",
                    "authors_joined",
                    "categories_joined",
                    "summary",
                    "abs_url",
                    "pdf_url",
                ]
            ),
        },
        indent=2,
    ))

    preview = clean_df.loc[:, ["paper_id", "title", "summary", "text_for_embedding"]].head(3)
    print("\nSAMPLE TEXT_FOR_EMBEDDING")
    for idx, row in preview.iterrows():
        print(f"\n[{idx}] paper_id={row['paper_id']}")
        print(f"title={row['title']}")
        print(f"summary={row['summary'][:220]}")
        print(f"text_for_embedding={row['text_for_embedding'][:400]}")

    index = LocalEmbeddingIndex.build(clean_df, settings, embeddings_output_path=settings.paths.embeddings_json)
    print("\nINDEX BUILT")
    print(json.dumps(
        {
            "backend": index.embedding_backend,
            "collection_name": index.collection_name,
            "persist_path": str(index.persist_path),
        },
        indent=2,
    ))

    sample_title = _normalize_exact_value(str(clean_df.iloc[0]["title"]))
    sample_paper_id = str(clean_df.iloc[0]["paper_id"])

    print("\nLOOKUP BY TITLE")
    print(json.dumps(index.lookup(sample_title), indent=2, ensure_ascii=True)[:2000])

    print("\nLOOKUP BY PAPER_ID")
    print(json.dumps(index.lookup(sample_paper_id), indent=2, ensure_ascii=True)[:2000])

    query = "large language model retrieval augmented generation"
    print("\nSEMANTIC SEARCH")
    for result in index.search(query, top_k=3):
        print(
            json.dumps(
                {
                    "paper_id": result.paper_id,
                    "title": result.title,
                    "score": result.score,
                    "content_preview": result.content[:220],
                },
                ensure_ascii=True,
            )
        )

    try:
        from retrieval.agent import build_agent, run_agent_question

        agent = build_agent(settings, index)
        question = f"What is the publication date of '{sample_title}'?"
        answer = run_agent_question(agent, question)
        print("\nAGENT ANSWER")
        print(answer)
    except Exception as exc:
        print("\nAGENT SKIPPED")
        print(f"{type(exc).__name__}: {exc}")


if __name__ == "__main__":
    main()
