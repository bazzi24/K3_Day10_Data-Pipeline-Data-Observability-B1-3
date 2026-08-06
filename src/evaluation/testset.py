from pathlib import Path
from typing import Any

import pandas as pd

from core.utils import write_json


def build_test_set(df: pd.DataFrame, output_path: str | Path) -> list[dict[str, Any]]:
    """Tạo bộ evaluation set từ cleaned dataframe.

    Yêu cầu:
    1. Kiểm tra số lượng document tối thiểu.
    2. Chọn các paper đại diện từ cleaned dataframe.
    3. Tạo nhiều loại câu hỏi: summary, authors, date, categories.
    4. Mỗi row gồm: id, question_type, question, ground_truth, ground_truth_doc_ids.
    5. Ghi file JSON vào output_path.
    """
    if df.empty:
        raise ValueError("Cannot build test set from an empty DataFrame.")

    sample_df = df.head(10).copy()
    test_set: list[dict[str, Any]] = []
    question_counter = 1

    for _, row in sample_df.iterrows():
        paper_id = str(row["paper_id"]).strip()
        title = str(row.get("title", "")).strip()
        summary = str(row.get("summary", "")).strip()
        authors = str(row.get("authors_joined", "")).strip()
        published = str(row.get("published", "")).strip()
        categories = str(row.get("categories_joined", "")).strip()

        if authors and len(test_set) < 10:
            test_set.append({
                "id": f"q{question_counter}",
                "question_type": "authors",
                "question": f"Who are the authors of the paper titled '{title}'?",
                "ground_truth": authors,
                "ground_truth_doc_ids": [paper_id],
            })
            question_counter += 1

        if summary and len(test_set) < 10:
            test_set.append({
                "id": f"q{question_counter}",
                "question_type": "summary",
                "question": f"What is the main topic and summary of the research paper '{title}'?",
                "ground_truth": summary,
                "ground_truth_doc_ids": [paper_id],
            })
            question_counter += 1

        if published and len(test_set) < 10:
            test_set.append({
                "id": f"q{question_counter}",
                "question_type": "date",
                "question": f"When was the paper '{title}' published?",
                "ground_truth": published,
                "ground_truth_doc_ids": [paper_id],
            })
            question_counter += 1

        if categories and len(test_set) < 10:
            test_set.append({
                "id": f"q{question_counter}",
                "question_type": "categories",
                "question": f"What research categories does the paper '{title}' belong to?",
                "ground_truth": categories,
                "ground_truth_doc_ids": [paper_id],
            })
            question_counter += 1

        if len(test_set) >= 10:
            break

    out_p = Path(output_path)
    write_json(out_p, test_set)
    return test_set
