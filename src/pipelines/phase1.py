from __future__ import annotations

from core.config import load_settings, require_llm_credentials
from core.utils import now_utc, read_json, write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from evaluation.testset import build_test_set
from ingestion.cleaning import build_clean_dataframe
from ingestion.crossref import fetch_source_records, load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_phase1_report
from retrieval.index import LocalEmbeddingIndex
from retrieval.qa import answer_question


def main() -> None:
    """Baseline pipeline end-to-end."""
    settings = load_settings()
    try:
        require_llm_credentials(settings)
    except RuntimeError as exc:
        # Extractive QA still works; judge falls back to token-F1 heuristics.
        print(f"Warning: {exc} Continuing with heuristic judge fallback.")
    run_date = now_utc()

    # 1-2. Load or fetch raw records.
    if settings.paths.raw_records_json.exists() and not settings.refresh_source:
        records = load_raw_records(settings.paths.raw_records_json)
    else:
        records = fetch_source_records(settings)

    # 3-4. Clean and save.
    clean_df = build_clean_dataframe(records, run_date=run_date)
    if clean_df.empty:
        raise RuntimeError("Cleaning produced an empty dataframe. Check source fetch/parse.")

    write_csv(clean_df, settings.paths.clean_csv)
    write_json(settings.paths.clean_json, clean_df.to_dict(orient="records"))

    # 5. Build embedding index.
    index = LocalEmbeddingIndex.build(
        clean_df,
        settings=settings,
        embeddings_output_path=settings.paths.embeddings_json,
    )

    # 6. Create or load evaluation set.
    if settings.paths.eval_testset.exists() and not settings.refresh_test_set:
        test_set = read_json(settings.paths.eval_testset)
    else:
        test_set = build_test_set(clean_df, settings.paths.eval_testset)

    # 7. Evaluate.
    evaluation = evaluate_pipeline(
        settings=settings,
        index=index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.baseline_metrics,
        answers_output_path=settings.paths.baseline_answers,
    )

    # 8. Quality + freshness.
    quality = run_data_quality_checks(clean_df, settings=settings, report_name="baseline_quality")
    freshness = build_freshness_report(
        clean_df,
        settings=settings,
        report_path=settings.paths.freshness_report,
    )

    # 9. Markdown report.
    source_summary = {
        "source_api": settings.source_api,
        "source_query": settings.source_query,
        "source_filter": settings.source_filter,
        "raw_records": len(records),
        "clean_rows": int(len(clean_df)),
        "embedding_model": settings.embedding_model,
        "collection_name": settings.baseline_collection_name,
        "test_set_size": len(test_set),
    }
    generate_phase1_report(
        report_path=settings.paths.baseline_report,
        source_summary=source_summary,
        metrics=evaluation.summary,
        quality=quality,
        freshness=freshness,
    )

    # 10. Optional demo answers on a few sample questions.
    demo_questions = [item["question"] for item in test_set[:3]]
    demo_answers = []
    for question in demo_questions:
        result = answer_question(question, settings=settings, index=index)
        demo_answers.append(
            {
                "question": result.question,
                "answer": result.answer,
                "retrieved_doc_ids": result.retrieved_doc_ids,
                "retrieved_titles": result.retrieved_titles,
            }
        )
    write_json(settings.paths.demo_answers, demo_answers)

    print("Phase 1 baseline completed.")
    print(f"Clean rows: {len(clean_df)}")
    print(f"Metrics: {settings.paths.baseline_metrics}")
    print(f"Report: {settings.paths.baseline_report}")
