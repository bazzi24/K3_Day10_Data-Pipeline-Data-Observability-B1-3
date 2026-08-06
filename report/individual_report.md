# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
| :--- | :--- |
| **Họ và tên** | Thành viên 4 (Role 4) |
| **MSSV** | [Điền MSSV của bạn] |
| **Khóa/Lớp** | K3 / K4 |
| **Tên nhóm** | Nhóm 4 người — Data Pipeline Lab |
| **Vai trò chính** | **Role 4: Evaluation & Observability Owner** |
| **Repository** | `K3_Day10_Data-Pipeline-Data-Observability` |
| **Ngày hoàn thành** | 2026-08-06 |

---

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| :--- | :--- | :--- | :--- | :--- |
| **Frozen Test Set Generator** | [testset.py]`build_test_set` | Cleaned DataFrame `data/clean/papers_clean.json` | `data/eval/test_set.json` | Hoàn thành |
| **Data Quality & Freshness Checks** | [quality.py]`run_data_quality_checks`, `build_freshness_report` | Cleaned / Corrupted DataFrame, `Settings` | `data/quality/*.json`, `freshness_report.json` | Hoàn thành |
| **Observability Reporting** | [reporting.py]`generate_phase1_report`, `generate_corruption_report` | Metrics JSON, Quality reports, Freshness reports | `data/reports/phase1_report.md`, `data/reports/corruption_report.md` | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả và bằng chứng |
| :--- | :--- | :--- |
| Thống nhất Data Contract với đồng đội | Role 1 (Integrator), Role 2 (Data Ingestion), Role 3 (RAG Owner) | Sử dụng đúng các DOI thực tế (`10.2118/234689-pa`, `10.1145/3818621`...) làm `ground_truth_doc_ids` đồng nhất giữa `testset.py` và vector store ChromaDB. |

---

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| :--- | :--- | :--- | :--- |
| Đóng băng bộ câu hỏi đánh giá | `src/evaluation/testset.py` | `data/eval/test_set.json` (gồm 10 câu hỏi đa dạng loại hình) | Inspect file `test_set.json` kiểm tra các trường `id`, `question_type`, `question`, `ground_truth`, `ground_truth_doc_ids`. |
| Cấu hình bộ kiểm tra chất lượng dữ liệu | `src/observability/quality.py` | Reports trong `data/quality/` (Row count, uniqueness, nulls, freshness) | Đã test trả về status `PASS` khi data sạch và `FAIL` khi data bị corrupt. |
| Sinh báo cáo tổng hợp Markdown | `src/observability/reporting.py` | `phase1_report.md` & `corruption_report.md` | Xuất bảng so sánh 3 cột (Baseline vs Corrupted vs Repaired) cùng delta phục hồi. |

---

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết
Hệ thống RAG nếu không có cơ chế giám sát chất lượng dữ liệu (Data Observability) sẽ dễ bị làm sai lệch kết quả bởi data bị hỏng (null summary, stale date, duplicate paper_id). Role 4 xây dựng thước đo (Frozen Eval Set) và chốt chặn giám sát (Quality & Freshness Checks) để phát hiện sự cố trước khi người dùng nhận thấy và đo lường sự phục hồi sau repair.

### Cách triển khai
1. **`build_test_set`:** Trích xuất các bài báo tiêu biểu từ `papers_clean.json`, sinh ra bộ 10 câu hỏi đa dạng loại hình (`authors`, `summary`, `date`, `categories`) kèm `ground_truth_doc_ids` chính xác từ DOI thực tế (`10.2118/234689-pa`, `10.1145/3818621`...). Bộ test này được lưu cố định (freeze) và tái sử dụng qua cả 3 pha.
2. **`run_data_quality_checks`:** Kiểm tra 7 tiêu chí bắt buộc (row count >= 1, `paper_id` non-null & unique, `title` non-null, `summary` length >= 100 chars, `age_days` <= threshold). Nếu có bất kỳ vi phạm nào, trả về `status: "FAIL"` và liệt kê `failed_rules`.
3. **`build_freshness_report`:** Xác định ngày xuất bản mới nhất (`latest_published`), cũ nhất (`oldest_published`), số dòng bị quá hạn (`stale_rows`) và cờ `is_fresh`.
4. **`generate_corruption_report`:** Render báo cáo Markdown dạng bảng đối chiếu 3 trạng thái **Baseline**, **Corrupted**, **Repaired** kèm cột **Recovery Delta**, phục vụ việc bảo vệ luận điểm thí nghiệm.

---

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Cần chọn phương án tạo bộ câu hỏi đánh giá (Evaluation Set) sao cho kết quả đo lường giữa các pha (Baseline vs Corrupted vs Repaired) phản ánh chính xác tác động của dữ liệu.
- **Các phương án đã cân nhắc:**
  1. *Phương án A:* Sinh động (dynamically generate) bộ câu hỏi mới mỗi lần chạy pipeline.
  2. *Phương án B (Đã chọn):* Đóng băng (Freeze) bộ câu hỏi `test_set.json` duy nhất sau khi làm sạch Phase 1 và tái sử dụng 100% bộ câu hỏi này cho các pha sau.
- **Lý do chọn:** Phương án B bảo đảm nguyên tắc khoa học về đối chứng: giữ nguyên các biến số đánh giá (Evaluation Set, Ground Truth, Evaluator prompt/metric, Top-k) và chỉ thay đổi duy nhất biến số dữ liệu (Dataset status).
- **Bằng chứng:** Điểm sụt giảm và phục hồi của `retrieval_hit_rate` và `token_f1` hoàn toàn là do chất lượng dữ liệu thay đổi, không bị nhiễu do câu hỏi thay đổi.

---

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi:** Trong quá trình test ban đầu, `retrieval_hit_rate` luôn bằng 0.0%.
- **Nguyên nhân gốc:** Trường `ground_truth_doc_ids` trong `test_set.json` bị lệch định dạng ID so với trường `paper_id` (DOI) được index trong ChromaDB.
- **Cách xử lý:** Chuẩn hóa ép kiểu `str(row["paper_id"]).strip()` đồng nhất ở cả `testset.py`, `cleaning.py` và `index.py`.
- **Cách xác minh sau khi sửa:** Chạy thử smoke test evaluation, `retrieval_hit_rate` trên data sạch đạt điểm tuyệt đối 100%.

---

## 7. Hiểu biết về luồng end-to-end

1. **Dữ liệu đi từ Crossref đến vector index:** Crossref API -> `crossref_response.json` (raw API) -> `crossref_records.json` (parsed flat) -> `cleaning.py` (loại bỏ rác, parse date, tính `age_days`, ghép `text_for_embedding`) -> `papers_clean.csv/json` -> `index.py` (MiniLM embedding model 384 dim + ChromaDB vector collection).
2. **Evaluation set & Ground-truth document IDs:** Bộ câu hỏi gồm `question`, `ground_truth` và `ground_truth_doc_ids`. Khi agent trả lời, evaluator đối chiếu xem danh sách `retrieved_doc_ids` từ vector store có chứa `ground_truth_doc_ids` hay không để tính `retrieval_hit_rate`.
3. **Quality checks vs Freshness monitoring:** Quality checks kiểm tra độ toàn vẹn cấu trúc (Row count, Nulls, Duplicates, Schema validation). Freshness monitoring kiểm tra yếu tố thời gian (độ tuổi `age_days`, phát hiện tài liệu quá hạn/outdated so với `freshness_threshold_days`).
4. **Vì sao dùng chung test set:** Để đảm bảo tính công bằng và so sánh lặp lại được (fair & reproducible comparison). Nếu test set thay đổi ở pha corrupted, ta không thể phân biệt được score giảm do data hỏng hay do câu hỏi khó hơn.
5. **Repair được xem là thành công khi:** Data Quality status chuyển từ `FAIL` về `PASS`, số dòng stale/corrupted về `0`, và các chỉ số RAG (`retrieval_hit_rate`, `mean_token_f1`, LLM judge score) phục hồi tiệm cận hoặc bằng mức Baseline.

---

## 8. Cam kết của thành viên

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Thành viên 4 (Role 4)  
**Ngày xác nhận:** 2026-08-06  
