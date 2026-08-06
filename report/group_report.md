# Group Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin bài nộp

| Thông tin | Nội dung |
| --- | --- |
| Khóa/Lớp | K3 |
| Tên nhóm | B1-3 |
| Repository | `K3_Day10_Data-Pipeline-Data-Observability-B1-3` |
| Ngày hoàn thành | 2026-08-06 |

### Thành viên và phân công

| STT | Họ và tên | MSSV | Vai trò chính | Module/deliverable sở hữu |
| --: | --- | --- | --- | --- |
| 1 | Phùng Văn Đạt | 2A202602012 | Role 1: Điều phối pipeline | `src/core/`, `src/pipelines/`, baseline orchestration, demo/release |
| 2 | Chưa cung cấp trong repo | Chưa cung cấp | Role 2: Nền tảng dữ liệu & recovery | `src/ingestion/`, `data/raw/`, `data/clean/` |
| 3 | Chưa cung cấp trong repo | Chưa cung cấp | Role 3: RAG & agent | `src/retrieval/`, `data/embeddings/` |
| 4 | Nguyễn Trọng Dũng | 2A202601965 | Role 4: Evaluation & observability | `src/evaluation/`, `src/observability/`, `data/eval/`, `data/quality/`, `data/reports/` |

## 2. Tóm tắt kết quả

Nhóm đã hoàn thành pipeline end-to-end cho ba trạng thái baseline, corrupted và repaired. Baseline ingest được 24 raw records từ Crossref, clean còn 24 records, build embedding + ChromaDB, tạo frozen test set 10 câu hỏi và đo được baseline metrics: `retrieval_hit_rate=1.0`, `mean_token_f1=0.37030291298583984`, `judge_accuracy=0.3`, `mean_judge_score=2.2`. Khi corruption được kích hoạt sau baseline, dữ liệu bị làm hỏng theo nhiều kiểu có chủ đích: xóa bản ghi mới nhất, blank summary, chèn noise, truncate title, làm stale ngày xuất bản và duplicate rows. Tín hiệu observability phản ánh đúng hư hỏng: quality `FAIL`, freshness `false`, stale rows tăng và retrieval/answer metrics tụt mạnh. Sau repair, pipeline chạy lại từ raw snapshot đáng tin cậy, quality/freshness quay về `PASS` và `true`, retrieval hit rate phục hồi về 1.0, và các metric tổng hợp quay về đúng baseline của artifact hiện có. Giới hạn còn lại là baseline ban đầu không phải mọi câu hỏi đều đạt điểm cao tuyệt đối, nên cần đọc metric cùng với answer-level evidence. Repo hiện tại chỉ có report cá nhân của role 4 trong thư mục `report/`.

## 3. Kiến trúc và luồng dữ liệu

### Luồng end-to-end

```text
Crossref API
    -> raw response/raw records
    -> cleaning và data modeling
    -> embedding + ChromaDB index
    -> evaluation baseline
    -> quality/freshness reports
    -> corruption
    -> re-index và re-evaluate
    -> repair từ dữ liệu nguồn
    -> comparison report
```

### Trách nhiệm của từng khối

| Khối | Input | Xử lý chính | Output/artifact | Owner |
| --- | --- | --- | --- | --- |
| Ingestion | Crossref REST API | Fetch, retry, parse | `data/raw/crossref_response.json`, `data/raw/crossref_records.json` | Role 2 |
| Cleaning | Raw records | Normalize text, dedup, derive `age_days`, build `text_for_embedding` | `data/clean/papers_clean.csv`, `data/clean/papers_clean.json` | Role 2 |
| Embedding/index | Cleaned data | MiniLM embedding + ChromaDB collections | `data/embeddings/*.json`, `data/chroma/` | Role 3 |
| Evaluation | Frozen test set | Same test set for three states, metrics + answers | `data/eval/test_set.json`, `data/results/*.json` | Role 4 |
| Observability | Clean/corrupted/repaired data | Quality + freshness checks | `data/quality/*.json` | Role 4 |
| Corruption/repair | Clean baseline + raw snapshot | Inject corruption, then rebuild from raw | `data/clean/papers_clean_corrupted.json`, `data/clean/papers_clean_repaired.json` | Role 2 + Role 1 |
| Orchestration | All artifacts | Run flows and generate markdown reports | `data/reports/phase1_report.md`, `data/reports/corruption_report.md` | Role 1 + Role 4 |

## 4. Cách tái hiện kết quả

### Cấu hình không chứa secret

| Biến/cấu hình | Giá trị sử dụng |
| --- | --- |
| `LLM_PROVIDER` | Runtime-configured; secret-bearing `.env` values are not committed |
| `LLM_MODEL` | Runtime-configured; see the execution environment used to generate the artifacts |
| Embedding model | `text-embedding-3-small` |
| Số lượng Crossref records | `24` requested, `25` raw records ingested, `24` clean records modeled |
| Retrieval `top_k` | `4` |
| Freshness threshold | `180` days |
| Random seed, nếu có | `42` for corruption flow |

### Lệnh cài đặt

```bash
uv sync
```

### Lệnh chạy

Baseline:

```bash
uv run python script/run_phase1.py
```

Corruption flow:

```bash
uv run python script/run_corruption_flow.py
```

### Kết quả tái hiện

| Lệnh | Trạng thái | Thời điểm chạy gần nhất | Bằng chứng |
| --- | --- | --- | --- |
| Baseline pipeline | Thành công | 2026-08-06 | `data/results/baseline_metrics.json`, `data/reports/phase1_report.md` |
| Corruption flow | Thành công | 2026-08-06 | `data/results/corruption_log.json`, `data/results/corrupted_metrics.json`, `data/results/repaired_metrics.json`, `data/reports/corruption_report.md` |

## 5. Ingestion, cleaning và data contract

### Nguồn dữ liệu

| Thuộc tính | Giá trị |
| --- | --- |
| Source | Crossref REST API |
| Query/filter | `query.title=agentic retrieval augmented generation large language model`, `filter=from-pub-date:2026-02-07,has-abstract:true`, `rows=24` |
| Thời điểm lấy dữ liệu | 2026-08-06 |
| Số record nhận được | 24 raw records |
| Cơ chế retry/backoff | 3 lần retry với backoff lũy thừa (2s, 4s) trong `src/ingestion/crossref.py` |

### Raw và clean schema

| Trường | Kiểu dữ liệu | Bắt buộc? | Ý nghĩa | Xử lý khi thiếu/sai |
| --- | --- | --- | --- | --- |
| `paper_id` | string | Có | DOI hoặc URL định danh paper | Bỏ record nếu thiếu |
| `title` | string | Có | Tiêu đề paper | Bỏ record nếu thiếu |
| `summary` | string | Có | Abstract/summary đã chuẩn hóa | Để rỗng thì thay bằng `No summary available.` ở clean stage, corruption stage có thể làm rỗng |
| `authors` | list[string] | Không | Danh sách tác giả | Chuẩn hóa thành chuỗi `authors_joined` |
| `categories` | list[string] | Không | Chủ đề/subject | Chuẩn hóa thành `categories_joined` |
| `published` | string | Có | Ngày xuất bản | Parse lại, fallback sang `updated`/`run_date` khi cần |
| `updated` | string | Không | Ngày cập nhật/indexed | Dùng làm fallback cho published |
| `text_for_embedding` | string | Có | Text đầu vào cho embedding | Tạo từ title, summary, authors, categories, primary_category |

### Quy tắc cleaning

| Quy tắc | Quality dimension liên quan | Số record bị tác động | Cách xác minh |
| --- | --- | ---: | --- |
| Loại record không có `paper_id` hoặc `title` | Validity / completeness | 0 record bị loại ở baseline pipeline (24 raw -> 24 clean) | `data/clean/papers_clean.json`, `data/reports/phase1_report.md` |
| Chuẩn hóa whitespace, HTML tags và date string | Consistency | Tất cả record hợp lệ | `src/ingestion/cleaning.py`, `papers_clean.csv/json` |
| Tạo `text_for_embedding`, `summary_chars`, `age_days` | Consistency / freshness | Tất cả record hợp lệ | `data/clean/papers_clean.json` |

Giải thích cách nhóm tạo `text_for_embedding`, document ID và `age_days`:

- `text_for_embedding` được ghép từ `title | summary | authors_joined | categories_joined | primary_category`.
- `paper_id` là DOI/URL chuẩn hóa và được giữ nhất quán giữa raw, clean, test set và ChromaDB.
- `age_days` = chênh lệch ngày giữa `run_date` và `published_dt`, dùng để phát hiện stale data.

## 6. Evaluation setup

| Thành phần | Cấu hình thực tế |
| --- | --- |
| Số câu hỏi | 10 |
| Các `question_type` | `authors`, `summary`, `date`, `categories` |
| Ground-truth document ID | DOI thật từ cleaned dataset, lưu trong `ground_truth_doc_ids` |
| Embedding model | `text-embedding-3-small` |
| Vector store/collection | `papers-baseline`, `papers-corrupted`, `papers-repaired` trong `data/chroma/` |
| Retrieval `top_k` | 4 |
| LLM provider/model | Runtime-configured; artifacts only preserve the generated outputs |
| Test set dùng chung cho ba trạng thái | `data/eval/test_set.json` |

Giải thích vì sao test set được giữ nguyên khi đánh giá baseline, corrupted và repaired:

- Nếu test set đổi, delta metric sẽ không còn phản ánh riêng tác động của corruption/repair.
- Frozen test set giúp so sánh nhân quả trên cùng câu hỏi, cùng evaluator và cùng `top_k`.

## 7. Kết quả baseline

### Artifact checklist

| Artifact | Đường dẫn thực tế | Trạng thái | Ghi chú |
| --- | --- | --- | --- |
| Raw response/records | `data/raw/` | Có | `crossref_response.json`, `crossref_records.json` |
| Cleaned dataset | `data/clean/` | Có | `papers_clean.csv`, `papers_clean.json` |
| Embedding manifest/index | `data/embeddings/` | Có | `papers_embeddings.json` |
| Evaluation set | `data/eval/` | Có | `test_set.json` |
| Baseline metrics | `data/results/baseline_metrics.json` | Có | Baseline RAG metrics |
| Quality/freshness | `data/quality/` | Có | Baseline quality + freshness JSON |
| Baseline report | `data/reports/phase1_report.md` | Có | Markdown report khớp baseline artifact |

### Baseline metrics

| Metric | Giá trị | Diễn giải |
| --- | ---: | --- |
| `retrieval_hit_rate` | 1.0 | 100% câu hỏi có document đúng trong top-k |
| `mean_token_f1` | 0.37030291298583984 | Mean token F1 của baseline artifact hiện tại |
| `judge_accuracy` | 0.3 | Judge heuristic đúng 3/10 samples |
| `mean_judge_score` | 2.2 | Điểm trung bình theo artifact hiện có |
| Ragas | N/A | Không chạy pass Ragas trong artifact hiện tại |

## 8. Data quality và freshness

### Quality checks

| Check | Quality dimension | Ngưỡng/kỳ vọng | Kết quả baseline | Bằng chứng |
| --- | --- | --- | --- | --- |
| Row count sufficient | Completeness | `>= 1` | PASS, 24 rows | `data/quality/baseline_quality.json` |
| Paper ID no nulls / unique | Validity / uniqueness | `no nulls`, `unique` | PASS, `null_paper_ids=0`, `duplicate_paper_ids=0` | `data/quality/baseline_quality.json` |
| Title & summary completeness | Completeness | `no nulls` | PASS | `data/quality/baseline_quality.json` |
| Summary length threshold | Content quality | `>= 100 chars` | PASS | `data/quality/baseline_quality.json` |

### Freshness

| Thuộc tính | Giá trị |
| --- | --- |
| Freshness được đo tại | `data/quality/freshness_report.json` |
| Timestamp mới nhất | `2026-08-05` |
| Ngưỡng freshness | `180` days |
| Trạng thái baseline | Fresh |
| Lý do | `stale_rows=0`, `is_fresh=true` |

## 9. Corruption scenarios và repair

| Corruption | Cách tạo | Record bị tác động | Quality signal kỳ vọng | Tác động thực tế | Cách repair |
| --- | --- | ---: | --- | --- | --- |
| Drop latest records | Xóa record có ngày xuất bản mới nhất | 4 | Giảm coverage retrieval | `retrieval_hit_rate` tụt về 0.0 ở corrupted metrics | Clean lại từ raw snapshot, không copy sửa tay |
| Blank summary | Đặt summary rỗng | 3 | `summary_no_nulls` fail | `null_summaries=3` | Re-run cleaning từ raw |
| Summary noise | Chèn boilerplate noise | 3 | Giảm token F1 / judge score | `mean_token_f1` giảm mạnh | Rebuild từ raw source |
| Truncate title | Cắt title còn 12 ký tự | 3 | Giảm retrievability | Answer retrieval lệch | Rebuild từ raw source |
| Stale publication date | Đẩy published date về 2016-08-08 | 3 | `freshness_valid` fail | `stale_rows=4` | Re-run cleaning từ raw snapshot |
| Duplicate rows | Nhân bản row giữ nguyên `paper_id` | 2 | `paper_id_unique` fail | `duplicate_paper_ids=2` | Rebuild clean dataset từ raw |

Corruption log:

- Đường dẫn: `data/results/corruption_log.json`
- Trạng thái: Có
- Nhận xét: Log ghi rõ 6 loại corruption, số record bị tác động, `paper_ids` và tham số áp dụng.

Giải thích cách repair đảm bảo dữ liệu được phục hồi từ nguồn đáng tin cậy thay vì chỉ che kết quả lỗi:

- Repair không chỉnh trực tiếp answer hay metrics.
- Repair đọc lại `data/raw/crossref_records.json`, chạy lại `build_clean_dataframe`, sau đó build lại embeddings và evaluate.
- Vì vậy repaired dataset là bản tái sinh từ raw snapshot, không phải vá thủ công từ corrupted baseline.

## 10. So sánh baseline, corrupted và repaired

| Metric/signal | Baseline | Corrupted | Repaired | Thay đổi do corruption | Mức phục hồi | Nhận xét |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `retrieval_hit_rate` | 1.0 | 0.0 | 1.0 | -1.0 | +1.0 | Hồi phục hoàn toàn |
| `mean_token_f1` | 0.37030291298583984 | 0.0385757070123647 | 0.37030291298583984 | -0.33172720597347514 | +0.33172720597347514 | Hồi phục hoàn toàn về baseline |
| `judge_accuracy` | 0.3 | 0.0 | 0.3 | -0.3 | +0.3 | Hồi phục hoàn toàn về baseline |
| `mean_judge_score` | 2.2 | 1.0 | 2.2 | -1.2 | +1.2 | Hồi phục hoàn toàn về baseline |
| Quality checks pass/fail | PASS | FAIL | PASS | Từ PASS sang FAIL | Từ FAIL sang PASS | Data contract được phục hồi |
| Freshness status | Fresh | Stale detected | Fresh | Từ fresh sang stale | Từ stale sang fresh | Recovery rõ ràng ở freshness |

Nêu ít nhất hai kết luận có quan hệ nhân quả được hỗ trợ bởi artifacts:

1. `duplicate_rows` + `blank_summary` + `stale_publication_date` → `quality/freshness FAIL` → `retrieval_hit_rate` và `judge_score` giảm mạnh trong `data/results/corrupted_metrics.json`.
2. `repair from raw snapshot` → `quality PASS` + `freshness fresh` → các metric tổng hợp phục hồi về đúng baseline của artifact hiện có.

## 11. Vấn đề tích hợp quan trọng

Mô tả một vấn đề phát sinh khi ghép các module trong pipeline và cách nhóm xử lý:

- **Triệu chứng:** `retrieval_hit_rate` ban đầu bằng 0.0 trong các test đầu tiên.
- **Nguyên nhân:** `ground_truth_doc_ids` trong test set và `paper_id` trong ChromaDB chưa đồng nhất format.
- **Cách xử lý:** Chuẩn hóa `paper_id` bằng `str(row["paper_id"]).strip()` và giữ contract ổn định giữa `testset.py`, `cleaning.py`, `index.py`.
- **Cách xác minh:** `data/results/baseline_metrics.json` cho thấy hit rate phục hồi lên 1.0, và `data/results/baseline_answers.json` chứa retrieved doc IDs khớp DOI thật.

## 12. Giới hạn và hướng cải thiện

| Giới hạn hiện tại | Ảnh hưởng | Hướng cải thiện có thể kiểm chứng |
| --- | --- | --- |
| Không có đủ thông tin nhân sự role 1-3 trong repo snapshot | Group report chưa thể ghi đầy đủ tên/MSSV cho toàn bộ nhóm | Bổ sung roster chính thức vào report hoặc README |
| Reproducibility phụ thuộc vào môi trường Python/dependencies | Không thể tái chạy flow nếu thiếu package | Ghi rõ lockfile, cài đủ deps và kiểm tra import path |

## 13. Checklist trước khi nộp

- [x] Thông tin nhóm và repository chính xác.
- [x] Phân công khớp với module, artifact và kết quả thực tế.
- [x] Baseline, corrupted và repaired dùng cùng evaluation set.
- [x] Bảng metrics khớp với các file trong `data/results/`.
- [x] Quality/freshness conclusions khớp với `data/quality/`.
- [x] Các đường dẫn báo cáo và artifact truy cập được.
- [ ] Mỗi thành viên đã hoàn thành báo cáo vai trò riêng.  *Repo snapshot hiện chỉ thấy report role 4.*
- [x] Không có `.env`, API key, token hoặc secret trong source, report, log hay ảnh.
