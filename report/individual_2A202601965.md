# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
| :--- | :--- |
| **Họ và tên** | Nguyễn Trọng Dũng |
| **MSSV** | 2A202601965 |
| **Khóa/Lớp** | K3 |
| **Tên nhóm** | Nhóm 4 người — Data Pipeline Lab |
| **Vai trò chính** | **Role 4: Evaluation & Observability Owner** |
| **Repository** | `K3_Day10_Data-Pipeline-Data-Observability-B1-3` |
| **Ngày hoàn thành** | 2026-08-06 |

---

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| :--- | :--- | :--- | :--- | :--- |
| **Frozen Test Set Generator** | `src/evaluation/testset.py` - `build_test_set` | Cleaned DataFrame `data/clean/papers_clean.json` | `data/eval/test_set.json` | Hoàn thành |
| **Data Quality & Freshness Checks** | `src/observability/quality.py` - `run_data_quality_checks`, `build_freshness_report` | Cleaned / Corrupted DataFrame, `Settings` | `data/quality/*.json`, `data/quality/freshness_report.json` | Hoàn thành |
| **Observability Reporting** | `src/observability/reporting.py` - `generate_phase1_report`, `generate_corruption_report` | Metrics JSON, Quality reports, Freshness reports | `data/reports/phase1_report.md`, `data/reports/corruption_report.md` | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả và bằng chứng |
| :--- | :--- | :--- |
| Thống nhất Data Contract với đồng đội | Role 1 (Integrator), Role 2 (Data Ingestion), Role 3 (RAG Owner) | `ground_truth_doc_ids` trong `data/eval/test_set.json` dùng đúng DOI thực tế và khớp với `paper_id` trong ChromaDB. |

---

## 3. Kết quả theo vai trò

### 3.1. Evaluation set đã được đóng băng

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| :--- | :--- | :--- | :--- |
| Tạo frozen evaluation set | `src/evaluation/testset.py` | `data/eval/test_set.json` với 10 câu hỏi | Kiểm tra 4 loại câu hỏi: `authors`, `summary`, `date`, `categories`. Mỗi sample có `question`, `ground_truth`, `ground_truth_doc_ids`. |

Tập test này được giữ nguyên cho baseline, corrupted và repaired để delta metric phản ánh đúng thay đổi của dữ liệu, không bị nhiễu bởi câu hỏi mới.

### 3.2. Data quality và freshness

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| :--- | :--- | :--- | :--- |
| Chạy quality checks | `src/observability/quality.py` | `data/quality/baseline_quality.json`, `data/quality/corrupted_quality.json`, `data/quality/repaired_quality.json` | Baseline `PASS`, corrupted `FAIL`, repaired `PASS`. |
| Chạy freshness checks | `src/observability/quality.py` | `data/quality/freshness_report.json`, `data/quality/corrupted_freshness_report.json`, `data/quality/repaired_freshness_report.json` | Baseline/repaired `is_fresh = true`, corrupted `is_fresh = false`. |

### 3.3. Reporting và comparison

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| :--- | :--- | :--- | :--- |
| Sinh baseline report | `src/observability/reporting.py` - `generate_phase1_report` | `data/reports/phase1_report.md` | Report nêu rõ nguồn Crossref, số raw/clean records, metrics baseline và trạng thái quality/freshness. |
| Sinh comparison report | `src/observability/reporting.py` - `generate_corruption_report` | `data/reports/corruption_report.md` | Report so sánh baseline, corrupted và repaired từ metrics/quality/freshness thật. |

---

## 4. Số liệu và bằng chứng chính

### Baseline

- `data/results/baseline_metrics.json`
  - `retrieval_hit_rate`: `1.0`
  - `mean_token_f1`: `0.37030291298583984`
  - `judge_accuracy`: `0.3`
  - `mean_judge_score`: `2.2`
- `data/quality/baseline_quality.json`
  - `status`: `PASS`
  - `total_rows`: `24`
  - `duplicate_paper_ids`: `0`
  - `null_summaries`: `0`
  - `stale_rows`: `0`
- `data/quality/freshness_report.json`
  - `is_fresh`: `true`
  - `latest_published`: `2026-08-05`
  - `oldest_published`: `2026-02-26`

### Corrupted

- `data/results/corrupted_metrics.json`
  - `retrieval_hit_rate`: `0.0`
  - `mean_token_f1`: `0.0385757070123647`
  - `judge_accuracy`: `0.0`
  - `mean_judge_score`: `1.0`
- `data/quality/corrupted_quality.json`
  - `status`: `FAIL`
  - `total_rows`: `22`
  - `duplicate_paper_ids`: `2`
  - `null_summaries`: `3`
  - `short_summaries`: `3`
  - `stale_rows`: `4`
- `data/quality/corrupted_freshness_report.json`
  - `is_fresh`: `false`
  - `latest_published`: `2026-07-02`
  - `oldest_published`: `2016-08-08`

### Repaired

- `data/results/repaired_metrics.json`
  - `retrieval_hit_rate`: `1.0`
  - `mean_token_f1`: `0.37030291298583984`
  - `judge_accuracy`: `0.3`
  - `mean_judge_score`: `2.2`
- `data/quality/repaired_quality.json`
  - `status`: `PASS`
  - `total_rows`: `24`
  - `duplicate_paper_ids`: `0`
  - `null_summaries`: `0`
  - `short_summaries`: `0`
  - `stale_rows`: `0`
- `data/quality/repaired_freshness_report.json`
  - `is_fresh`: `true`
  - `latest_published`: `2026-08-05`
  - `oldest_published`: `2026-02-26`

---

## 5. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Nếu evaluation set không được freeze, hoặc nếu quality/freshness không được đo trên cùng dataset, thì không thể kết luận corruption có thật sự làm giảm chất lượng retrieval/answer hay không. Role 4 chốt lại biến số đánh giá, rồi đo delta giữa baseline, corrupted và repaired.

### Cách triển khai

1. **Freeze evaluation set:** `build_test_set` chọn 10 sample đầu tiên của cleaned dataset và tạo bộ câu hỏi cố định với `ground_truth_doc_ids` là DOI thật.
2. **Quality checks:** `run_data_quality_checks` kiểm tra row count, null/duplicate `paper_id`, title, summary length và freshness qua `age_days`.
3. **Freshness report:** `build_freshness_report` tổng hợp `latest_published`, `oldest_published`, `stale_rows`, `is_fresh`.
4. **Comparison report:** `generate_corruption_report` render bảng baseline/corrupted/repaired từ metrics, quality và freshness thật.

---

## 6. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Muốn so sánh baseline, corrupted và repaired một cách công bằng.
- **Phương án đã chọn:** Dùng chung một test set frozen, giữ nguyên evaluator và `top_k`, chỉ thay dataset state.
- **Lý do:** Khi test set không đổi, mọi thay đổi của metric mới có ý nghĩa nhân quả với corruption/repair.
- **Kết quả:** Baseline và repaired khớp nhau trên các metric tổng hợp, còn corrupted suy giảm rõ rệt. Điều này cho thấy repair đã đưa hệ thống trở lại baseline của artifact hiện có, dù một số câu hỏi riêng lẻ vẫn có token F1 thấp ngay từ baseline.

---

## 7. Một hit/miss tiêu biểu để demo trung thực

### Hit

- `q3` trong `data/results/baseline_answers.json` và `data/results/repaired_answers.json`
- Câu hỏi: thời điểm xuất bản của paper `SafeRAG`
- Baseline và repaired đều trả đúng `2026-08-05`
- Đây là ví dụ cho recovery thật ở tầng retrieval + answer extraction

### Miss

- `q9` trong `data/results/corrupted_answers.json`
- Câu hỏi: thời điểm xuất bản của paper `JADE-Plus`
- Baseline và repaired đều trả đúng `2026-07-13`, nhưng corrupted trả `2026-07-02`
- Đây là ví dụ rõ của corruption làm hỏng retrieval và kéo answer sai lệch

---

## 8. Giới hạn và kết luận

- Corruption làm quality/freshness xấu đi rõ rệt và kéo metric answer xuống mạnh.
- Repair đã phục hồi data contract, row count, duplicate, null summary và freshness.
- Các metric tổng hợp của repaired quay về đúng baseline artifact hiện có.
- Kết luận hợp lệ là: repair thành công ở tầng dữ liệu và retrieval coverage, đồng thời khớp lại baseline quan sát được trong run hiện tại.
- Báo cáo này không chứa `.env`, API key, token hoặc secret.

---

## 9. Cam kết của thành viên

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Nguyễn Trọng Dũng  
**Ngày xác nhận:** 2026-08-06
