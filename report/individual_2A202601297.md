# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
| :--- | :--- |
| **Họ và tên** | Trương Đình Khoa |
| **MSSV** | 2A202601297 |
| **Khóa/Lớp** | K3 |
| **Tên nhóm** | B1-3 — Data Pipeline Lab |
| **Vai trò chính** | **Role 2: Data Ingestion, Cleaning & Recovery Owner** |
| **Repository** | `K3_Day10_Data-Pipeline-Data-Observability-B1-3` |
| **Ngày hoàn thành** | 2026-08-06 |

---

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| :--- | :--- | :--- | :--- | :--- |
| **Crossref Raw Ingestion** | `src/ingestion/crossref.py` - `fetch_source_records`, `parse_crossref_payload`, `load_raw_records` | Crossref REST API / raw snapshot | `data/raw/crossref_response.json`, `data/raw/crossref_records.json` | Hoàn thành |
| **Cleaning & Data Modeling** | `src/ingestion/cleaning.py` - `build_clean_dataframe` | Raw `PaperRecord` list | `data/clean/papers_clean.csv`, `data/clean/papers_clean.json` | Hoàn thành |
| **Corruption Data Generator** | `src/ingestion/corruption.py` - `corrupt_clean_dataframe` | Cleaned baseline DataFrame | `data/clean/papers_clean_corrupted.*`, `data/results/corruption_log.json` | Hoàn thành |
| **Recovery from Raw Snapshot** | `src/ingestion/cleaning.py` phối hợp `src/pipelines/corruption_flow.py` | `data/raw/crossref_records.json` | `data/clean/papers_clean_repaired.*` | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả và bằng chứng |
| :--- | :--- | :--- |
| Thống nhất data contract cho downstream modules | Role 3 (RAG/index), Role 4 (Evaluation/Observability) | `paper_id`, `text_for_embedding`, `published`, `summary_chars`, `age_days` được giữ ổn định giữa clean data, ChromaDB và evaluation set. |
| Hỗ trợ kiểm chứng repair | Role 1 (Pipeline integration), Role 4 (Quality report) | Repaired data được rebuild từ `data/raw/crossref_records.json`, không sửa tay metrics hay answers. |

---

## 3. Kết quả theo vai trò

### 3.1. Raw ingestion từ Crossref

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| :--- | :--- | :--- | :--- |
| Gọi Crossref API và lưu snapshot | `src/ingestion/crossref.py` - `fetch_source_records` | `data/raw/crossref_response.json` | File raw response tồn tại trong `data/raw/`. |
| Parse raw payload thành record chuẩn | `src/ingestion/crossref.py` - `parse_crossref_payload` | `data/raw/crossref_records.json` với 24 records | `jq 'length' data/raw/crossref_records.json` trả `24`. |
| Xử lý lỗi API có fallback | `fetch_source_records` | Retry 3 lần, nếu lỗi thì đọc snapshot cũ nếu có | Code có retry/backoff và fallback sang `raw_api_response`. |

Ingestion giữ lại các trường quan trọng cho pipeline sau: `paper_id`, `title`, `summary`, `authors`, `categories`, `primary_category`, `published`, `updated`, `abs_url`, `pdf_url`.

### 3.2. Cleaning và data model

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| :--- | :--- | :--- | :--- |
| Normalize text và loại HTML/whitespace | `src/ingestion/cleaning.py` - `_normalize_text` | Text sạch hơn cho title/summary/authors/categories | Clean JSON không còn HTML tag thô trong các trường chính. |
| Parse/fallback ngày xuất bản | `src/ingestion/cleaning.py` - `_parse_date`, `build_clean_dataframe` | `published`, `updated`, `age_days` | `data/quality/freshness_report.json` dùng được freshness signal. |
| Tạo text cho embedding | `build_clean_dataframe` | Cột `text_for_embedding` | Role 3 dùng clean data để build `data/embeddings/papers_embeddings.json`. |
| Deduplicate theo document ID | `build_clean_dataframe` | `data/clean/papers_clean.json` với 24 records | Baseline quality có `duplicate_paper_ids = 0`. |

Cleaned dataset là contract chính cho retrieval và evaluation. Nếu `paper_id` hoặc `text_for_embedding` lệch format, downstream metric sẽ sai ngay cả khi dữ liệu nguồn đúng.

### 3.3. Corruption và recovery

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| :--- | :--- | :--- | :--- |
| Sinh dữ liệu corrupted có chủ đích | `src/ingestion/corruption.py` - `corrupt_clean_dataframe` | `data/clean/papers_clean_corrupted.json` | Corruption log ghi 6 loại corruption, `input_rows = 24`, `output_rows = 22`. |
| Ghi log corruption có thể audit | `data/results/corruption_log.json` | Log gồm seed, loại lỗi, số record, `paper_ids` | Kiểm tra `seed = 42` và từng event trong log. |
| Repair bằng rebuild từ raw snapshot | `build_clean_dataframe` trong corruption flow | `data/clean/papers_clean_repaired.json` | Repaired quality `PASS`, total rows quay về `24`. |

---

## 4. Số liệu và bằng chứng chính

### Baseline data

- `data/raw/crossref_records.json`
  - Số raw records: `24`
- `data/clean/papers_clean.json`
  - Số clean records: `24`
- `data/quality/baseline_quality.json`
  - `status`: `PASS`
  - `total_rows`: `24`
  - `duplicate_paper_ids`: `0`
  - `null_summaries`: `0`
  - `stale_rows`: `0`

### Corrupted data

- `data/results/corruption_log.json`
  - `seed`: `42`
  - `input_rows`: `24`
  - `output_rows`: `22`
  - `net_row_delta`: `-2`
  - `drop_latest_records`: `4`
  - `blank_summary`: `3`
  - `summary_noise`: `3`
  - `truncate_title`: `3`
  - `stale_publication_date`: `3`
  - `duplicate_rows`: `2`
- `data/quality/corrupted_quality.json`
  - `status`: `FAIL`
  - `total_rows`: `22`
  - `duplicate_paper_ids`: `2`
  - `null_summaries`: `3`
  - `short_summaries`: `3`
  - `stale_rows`: `4`
  - Failed rules: `paper_id_unique`, `summary_no_nulls`, `summary_adequate_length`, `freshness_valid`

### Repaired data

- `data/clean/papers_clean_repaired.json`
  - Số repaired records: `24`
- `data/quality/repaired_quality.json`
  - `status`: `PASS`
  - `total_rows`: `24`
  - `duplicate_paper_ids`: `0`
  - `null_summaries`: `0`
  - `short_summaries`: `0`
  - `stale_rows`: `0`

---

## 5. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Role 2 phải bảo đảm dữ liệu đi vào pipeline có schema ổn định và có thể khôi phục sau khi bị corruption. Nếu raw snapshot, clean schema hoặc document ID không ổn định, các phần embedding, retrieval, evaluation và observability sẽ không thể so sánh baseline/corrupted/repaired một cách công bằng.

### Cách triển khai

1. **Ingestion:** `fetch_source_records` gọi Crossref với query/filter trong settings, lưu raw response và parse thành `PaperRecord`.
2. **Parsing:** `parse_crossref_payload` lấy DOI/URL làm `paper_id`, chuẩn hóa title, abstract, authors, categories và ngày xuất bản.
3. **Cleaning:** `build_clean_dataframe` normalize text, fallback summary rỗng thành `No summary available.`, parse date và tính `age_days`.
4. **Data contract:** clean data tạo các trường downstream cần: `authors_joined`, `categories_joined`, `summary_chars`, `age_days`, `text_for_embedding`.
5. **Corruption:** `corrupt_clean_dataframe` tạo lỗi có kiểm soát gồm drop latest, blank summary, noise, truncate title, stale date và duplicate rows.
6. **Recovery:** repaired dataset được build lại từ `data/raw/crossref_records.json`, không copy ngược từ baseline metrics và không sửa answer thủ công.

---

## 6. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Cần một document identity dùng chung cho clean data, vector index và evaluation set.
- **Phương án đã chọn:** Dùng DOI/URL đã normalize làm `paper_id`, giữ nguyên từ raw parse đến clean JSON và ChromaDB metadata.
- **Lý do:** Evaluation dùng `ground_truth_doc_ids`, nên nếu document ID thay đổi giữa các bước thì retrieval hit rate có thể sai dù model retrieve đúng paper.
- **Kết quả:** Baseline và repaired đều đạt `retrieval_hit_rate = 1.0`; corrupted tụt về `0.0` do dữ liệu bị phá có chủ đích, không phải do lệch schema.

---

## 7. Một ví dụ corruption/repair tiêu biểu để demo

### Corruption rõ ràng

- `data/results/corruption_log.json`
- Loại lỗi: `drop_latest_records`
- Số record bị xóa: `4`
- Tác động: clean corrupted còn `22` rows và retrieval coverage giảm mạnh trong `data/results/corrupted_metrics.json`.

### Repair rõ ràng

- `data/clean/papers_clean_repaired.json`
- Cách repair: đọc lại `data/raw/crossref_records.json` và chạy lại `build_clean_dataframe`
- Kết quả: repaired quality `PASS`, `total_rows = 24`, `duplicate_paper_ids = 0`, `null_summaries = 0`, `stale_rows = 0`.

---

## 8. Giới hạn và kết luận

- Ingestion phụ thuộc vào Crossref API; khi API lỗi, pipeline dùng snapshot đã lưu để vẫn tái hiện được kết quả.
- Cleaning hiện xử lý tốt schema và completeness cơ bản, nhưng chưa có validation nâng cao cho semantic quality của abstract.
- Corruption được tạo deterministic với seed `42`, phù hợp cho demo và so sánh metric lặp lại.
- Repair đã phục hồi dữ liệu từ raw snapshot đáng tin cậy, đưa clean data và quality checks quay về baseline.
- Báo cáo này không chứa `.env`, API key, token hoặc secret.

---

## 9. Cam kết của thành viên

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Trương Đình Khoa  
**Ngày xác nhận:** 2026-08-06
