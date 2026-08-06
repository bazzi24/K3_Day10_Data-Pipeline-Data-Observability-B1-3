# Group Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin bài nộp

| Thông tin | Nội dung |
| --- | --- |
| Khóa/Lớp | K3 |
| Tên nhóm | B1-3 |
| Repository | `K3_Day10_Data-Pipeline-Data-Observability-B1-3` |
| Ngày hoàn thành | 2026-08-06 |

### Thành viên và phân công

| STT | Họ và tên | MSSV | Vai trò chính | Deliverable sở hữu |
| --: | --- | --- | --- | --- |
| 1 | Phùng Văn Đạt | 2A202602012 | Role 1: Điều phối pipeline | `src/core/`, `src/pipelines/`, baseline orchestration, release/demo |
| 2 | Trương Đình Khoa | 2A202601297 | Role 2: Nền tảng dữ liệu & recovery | `src/ingestion/`, `data/raw/`, `data/clean/` |
| 3 | Vũ Quang Tùng | 2A202601545 | Role 3: RAG & agent | `src/retrieval/`, `data/embeddings/` |
| 4 | Nguyễn Trọng Dũng | 2A202601965 | Role 4: Evaluation & observability | `src/evaluation/`, `src/observability/`, `data/eval/`, `data/quality/`, `data/reports/` |

## 2. Tóm tắt kết quả

Nhóm đã hoàn thành pipeline end-to-end cho ba trạng thái baseline, corrupted và repaired. Artifact hiện có cho thấy:

- `data/raw/crossref_records.json`: 24 raw records.
- `data/clean/papers_clean.json`: 24 clean records.
- `data/eval/test_set.json`: 10 câu hỏi frozen evaluation set.
- `data/results/baseline_metrics.json`: `retrieval_hit_rate=1.0`, `mean_token_f1=0.37030291298583984`, `judge_accuracy=0.3`, `mean_judge_score=2.2`.
- `data/results/corrupted_metrics.json`: `retrieval_hit_rate=0.0`, `mean_token_f1=0.0385757070123647`, `judge_accuracy=0.0`, `mean_judge_score=1.0`.
- `data/results/repaired_metrics.json`: quay lại đúng baseline của artifact hiện có.

Khi corruption được kích hoạt sau baseline, dữ liệu bị làm hỏng có chủ đích theo nhiều kịch bản: xóa record mới nhất, blank summary, chèn noise, truncate title, làm stale ngày xuất bản và tạo duplicate rows. Quality/freshness chuyển từ `PASS/FRESH` sang `FAIL/false`, và retrieval/answer metrics giảm mạnh. Sau repair, pipeline chạy lại từ raw snapshot đáng tin cậy, quality/freshness phục hồi về `PASS/true`, và metrics tổng hợp quay lại đúng baseline của run hiện tại.

## 3. Kiến trúc và luồng dữ liệu

### Luồng end-to-end

```text
Crossref API
    -> raw response / raw records
    -> cleaning và data modeling
    -> embedding + ChromaDB index
    -> frozen evaluation set
    -> baseline evaluation
    -> quality / freshness reports
    -> corruption
    -> evaluate corrupted
    -> repair từ raw snapshot
    -> evaluate repaired
    -> comparison report
```

### Trách nhiệm của từng khối

| Khối | Input | Xử lý chính | Output/artifact | Owner |
| --- | --- | --- | --- | --- |
| Ingestion | Crossref REST API | Fetch, retry, parse | `data/raw/crossref_response.json`, `data/raw/crossref_records.json` | Role 2 |
| Cleaning | Raw records | Normalize text, dedup, derive `age_days`, build `text_for_embedding` | `data/clean/papers_clean.csv`, `data/clean/papers_clean.json` | Role 2 |
| Embedding/index | Cleaned data | MiniLM embedding + ChromaDB collections | `data/embeddings/*.json`, `data/chroma/` | Role 3 |
| Evaluation | Frozen test set | Same test set for all states, metrics + answers | `data/eval/test_set.json`, `data/results/*.json` | Role 4 |
| Observability | Clean/corrupted/repaired data | Quality + freshness checks | `data/quality/*.json` | Role 4 |
| Corruption/repair | Clean baseline + raw snapshot | Inject corruption, then rebuild from raw | `data/clean/papers_clean_corrupted.json`, `data/clean/papers_clean_repaired.json` | Role 2 + Role 1 |
| Reporting | All artifacts | Generate markdown reports | `data/reports/phase1_report.md`, `data/reports/corruption_report.md` | Role 4 |

## 4. Cách tái hiện kết quả

### Cấu hình và nguyên tắc

| Biến/cấu hình | Giá trị sử dụng |
| --- | --- |
| Embedding model | `text-embedding-3-small` |
| Retrieval `top_k` | `4` |
| Freshness threshold | `180` days |
| Random seed | `42` cho corruption flow |
| Secret / API key | Không commit trong repo |

### Lệnh chạy

```bash
python script/run_phase1.py
python script/run_corruption_flow.py
```

### Kết quả tái hiện

| Lệnh | Trạng thái | Bằng chứng |
| --- | --- | --- |
| Baseline pipeline | Thành công | `data/results/baseline_metrics.json`, `data/reports/phase1_report.md` |
| Corruption flow | Thành công | `data/results/corruption_log.json`, `data/results/corrupted_metrics.json`, `data/results/repaired_metrics.json`, `data/reports/corruption_report.md` |

## 5. Ingestion, cleaning và data contract

### Nguồn dữ liệu

| Thuộc tính | Giá trị |
| --- | --- |
| Source | Crossref REST API |
| Query/filter | `query.title=agentic retrieval augmented generation large language model`, `filter=from-pub-date:2026-02-07,has-abstract:true`, `rows=24` |
| Số record nhận được | 24 raw records |
| Retry/backoff | 3 lần retry với backoff lũy thừa (2s, 4s) trong `src/ingestion/crossref.py` |

### Raw và clean schema

| Trường | Kiểu dữ liệu | Bắt buộc? | Ý nghĩa | Xử lý khi thiếu/sai |
| --- | --- | --- | --- | --- |
| `paper_id` | string | Có | DOI hoặc URL định danh paper | Bỏ record nếu thiếu |
| `title` | string | Có | Tiêu đề paper | Bỏ record nếu thiếu |
| `summary` | string | Có | Abstract/summary đã chuẩn hóa | Bỏ record nếu quá ngắn / rỗng ở cleaning |
| `authors` | list[string] | Không | Danh sách tác giả | Chuẩn hóa thành chuỗi `authors_joined` |
| `categories` | list[string] | Không | Chủ đề/subject | Chuẩn hóa thành `categories_joined` |
| `published` | string | Có | Ngày xuất bản | Parse lại, fallback khi cần |
| `updated` | string | Không | Ngày cập nhật/indexed | Dùng làm fallback cho published |
| `text_for_embedding` | string | Có | Text đầu vào cho embedding | Tạo từ title, summary, authors, categories, primary_category |

### Quy tắc cleaning

| Quy tắc | Quality dimension | Số record bị tác động | Cách xác minh |
| --- | --- | ---: | --- |
| Loại record không có `paper_id` hoặc `title` | Validity / completeness | 0 record bị loại ở baseline pipeline | `data/clean/papers_clean.json`, `data/reports/phase1_report.md` |
| Chuẩn hóa whitespace, HTML tags và date string | Consistency | Tất cả record hợp lệ | `src/ingestion/cleaning.py`, `data/clean/papers_clean.json` |
| Tạo `text_for_embedding`, `summary_chars`, `age_days` | Consistency / freshness | Tất cả record hợp lệ | `data/clean/papers_clean.json` |

## 6. Evaluation setup

| Thành phần | Cấu hình thực tế |
| --- | --- |
| Số câu hỏi | 10 |
| `question_type` | `authors`, `summary`, `date`, `categories` |
| Ground-truth document ID | DOI thật từ cleaned dataset, lưu trong `ground_truth_doc_ids` |
| Test set dùng chung | `data/eval/test_set.json` |
| Collection tách biệt | `papers-baseline`, `papers-corrupted`, `papers-repaired` |
| LLM judge | Heuristic fallback trong artifact hiện tại |

## 7. Kết quả baseline

### Artifact checklist

| Artifact | Đường dẫn thực tế | Trạng thái |
| --- | --- | --- |
| Raw response/records | `data/raw/` | Có |
| Cleaned dataset | `data/clean/` | Có |
| Embedding manifest/index | `data/embeddings/` | Có |
| Evaluation set | `data/eval/` | Có |
| Baseline metrics | `data/results/baseline_metrics.json` | Có |
| Quality/freshness | `data/quality/` | Có |
| Baseline report | `data/reports/phase1_report.md` | Có |

### Baseline metrics

| Metric | Giá trị | Diễn giải |
| --- | ---: | --- |
| `retrieval_hit_rate` | 1.0 | 100% câu hỏi có document đúng trong top-k |
| `mean_token_f1` | 0.37030291298583984 | Mean token F1 của baseline artifact |
| `judge_accuracy` | 0.3 | Heuristic judge đúng 3/10 samples |
| `mean_judge_score` | 2.2 | Điểm trung bình của artifact hiện có |

## 8. Data quality và freshness

### Quality checks

| Check | Kết quả baseline | Bằng chứng |
| --- | --- | --- |
| Row count sufficient | PASS, 24 rows | `data/quality/baseline_quality.json` |
| Paper ID no nulls / unique | PASS | `data/quality/baseline_quality.json` |
| Title & summary completeness | PASS | `data/quality/baseline_quality.json` |
| Summary length threshold | PASS | `data/quality/baseline_quality.json` |

### Freshness

| Thuộc tính | Giá trị |
| --- | --- |
| Timestamp mới nhất | `2026-08-05` |
| Ngưỡng freshness | `180` days |
| Trạng thái baseline | Fresh |
| Lý do | `stale_rows=0`, `is_fresh=true` |

## 9. Corruption scenarios và repair

| Corruption | Cách tạo | Record bị tác động | Tác động thực tế | Cách repair |
| --- | --- | ---: | --- | --- |
| Drop latest records | Xóa record có ngày xuất bản mới nhất | 4 | Retrieval miss, metric giảm | Rebuild từ raw snapshot |
| Blank summary | Đặt summary rỗng | 3 | `summary_no_nulls` fail | Re-run cleaning từ raw |
| Summary noise | Chèn boilerplate noise | 3 | Đầu độc retrieval/answer | Rebuild từ raw source |
| Truncate title | Cắt title còn 12 ký tự | 3 | Giảm retrievability | Rebuild từ raw source |
| Stale publication date | Đẩy published date về 2016-08-08 | 3 | `freshness_valid` fail | Re-run cleaning từ raw snapshot |
| Duplicate rows | Nhân bản row giữ nguyên `paper_id` | 2 | `paper_id_unique` fail | Rebuild clean dataset từ raw |

### Corruption log

- `data/results/corruption_log.json`
- `input_rows = 24`, `output_rows = 22`, `net_row_delta = -2`
- Seed: `42`

### Repair contract

- Repair không chỉnh answers hoặc metrics bằng tay.
- Repair đọc lại `data/raw/crossref_records.json`.
- Repair chạy lại cleaning để tạo `papers_clean_repaired.json`.
- Repair build lại embeddings, index và evaluate trên cùng frozen test set.

## 10. So sánh baseline, corrupted và repaired

| Metric/signal | Baseline | Corrupted | Repaired |
| --- | ---: | ---: | ---: |
| `retrieval_hit_rate` | 1.0 | 0.0 | 1.0 |
| `mean_token_f1` | 0.37030291298583984 | 0.0385757070123647 | 0.37030291298583984 |
| `judge_accuracy` | 0.3 | 0.0 | 0.3 |
| `mean_judge_score` | 2.2 | 1.0 | 2.2 |
| Quality checks | PASS | FAIL | PASS |
| Freshness status | Fresh | Stale | Fresh |

### Kết luận có bằng chứng

1. `drop_latest_records`, `blank_summary`, `stale_publication_date` và `duplicate_rows` làm quality/freshness xấu đi rõ rệt, kéo metrics RAG xuống trong `data/results/corrupted_metrics.json`.
2. Repair từ raw snapshot đưa quality/freshness và metrics tổng hợp quay lại đúng baseline artifact hiện có.

## 11. Vấn đề tích hợp quan trọng

- `ground_truth_doc_ids` trong test set phải khớp với `paper_id` trong ChromaDB.
- Khi contract này lệch, retrieval hit rate sẽ giảm dù raw data vẫn đúng.
- Việc chuẩn hóa ID và giữ test set frozen giúp baseline/corrupted/repaired so sánh được trên cùng một mặt bằng.

## 12. Giới hạn và hướng cải thiện

| Giới hạn hiện tại | Ảnh hưởng | Hướng cải thiện |
| --- | --- | --- |
| Quality checks chưa bắt được mọi dạng corruption | Có corruption vẫn không hiện ra qua null/length checks | Bổ sung signal cho truncate/noise |
| Reproducibility phụ thuộc vào môi trường chạy | Cần cùng dependency set để tái hiện | Ghi lockfile và pin môi trường |
| Chưa có đủ metadata nhân sự trong snapshot cũ | Cần đối chiếu với báo cáo cá nhân | Dùng 4 individual reports đã có |

## 13. Checklist trước khi nộp

- [x] Thông tin nhóm và repository chính xác.
- [x] Phân công khớp với module, artifact và kết quả thực tế.
- [x] Baseline, corrupted và repaired dùng cùng evaluation set.
- [x] Bảng metrics khớp với các file trong `data/results/`.
- [x] Quality/freshness conclusions khớp với `data/quality/`.
- [x] Các đường dẫn báo cáo và artifact truy cập được.
- [x] Mỗi thành viên đã hoàn thành báo cáo vai trò riêng.
- [x] Không có `.env`, API key, token hoặc secret trong source, report, log hay ảnh.
