# Role 4 — Corruption Evaluation & Observability Analysis

> Bản phân tích dựa hoàn toàn trên artifact thật trong `data/`. Không sửa tay answers/metrics; mọi số liệu trích trực tiếp từ file JSON đã sinh bởi `script/run_corruption_flow.py`.
> Phạm vi: `src/evaluation/` và `src/observability/`. Không chỉnh sửa file của Role 1/2/3.

## 0. Kiểm tra tiền đề — Role 1/2/3 đã xong

| Role | Bằng chứng đã kiểm tra | Trạng thái |
| :--- | :--- | :--- |
| **Role 1** (orchestration) | `src/pipelines/corruption_flow.py` chạy đủ chuỗi corrupt → rebuild → evaluate → quality/freshness → repair → compare; `_require_files` chặn khi baseline chưa đủ artifact. | ✅ |
| **Role 2** (data & recovery) | `src/ingestion/corruption.py` sinh đủ 6 loại corruption; `data/results/corruption_log.json` log rõ record ID / type / parameter / before-after count (24 → 22, net −2). Repair rebuild từ `data/raw/crossref_records.json` bằng `build_clean_dataframe`. | ✅ |
| **Role 3** (RAG) | `src/core/config.py` khai báo collection riêng `papers-baseline` / `papers-corrupted` / `papers-repaired` và path embeddings riêng; `papers_embeddings_corrupted.json` tồn tại, baseline không bị ghi đè. | ✅ |

Kết luận: tiền đề đủ để Role 4 đánh giá công bằng (giữ nguyên test set `data/eval/test_set.json`, ground truth, evaluator, top-k giữa 3 trạng thái).

---

## 1. Evaluate corrupted trên test set cũ (Item 1)

Dùng đúng `test_set.json` (10 câu, đã freeze) cho cả 3 trạng thái. Artifact sinh ra:

- `data/results/corrupted_metrics.json`, `data/results/corrupted_answers.json`
- `data/results/repaired_metrics.json`, `data/results/repaired_answers.json`

| Metric | Baseline | Corrupted | Repaired | Δ do corruption | Δ phục hồi |
| :--- | ---: | ---: | ---: | ---: | ---: |
| `retrieval_hit_rate` | 1.00 | **0.00** | 1.00 | −1.00 | +1.00 |
| `mean_token_f1` | 0.370 | 0.039 | 0.370 | −0.332 | +0.332 |
| `judge_accuracy` | 0.30 | **0.00** | 0.30 | −0.30 | +0.30 |
| `mean_judge_score` | 2.20 | 1.00 | 2.20 | −1.20 | +1.20 |

Nguồn: `data/results/baseline_metrics.json`, `corrupted_metrics.json`, `repaired_metrics.json`.

---

## 2. So sánh answer/metric với baseline — case xấu đi có bằng chứng (Item 2)

**Case chọn: `q3` và `q9` — đều là câu hỏi factual về ngày xuất bản.**

Trong `corruption_log.json`, các record này nằm trong nhóm bị làm hỏng theo `drop_latest_records` / `stale_publication_date`. Vì record bị xóa hoặc bị đổi ngày trong corrupted dataset, retrieval và answer extraction đều sai:

| Câu | Baseline retrieved | Baseline kết quả | Corrupted retrieved | Corrupted kết quả |
| :--- | :--- | :--- | :--- | :--- |
| **q3** (SafeRAG date) | `['10.2118/234689-pa', '10.1007/s10278-026-02086-9', '10.1088/2515-7647/ae7491', '10.65521/mjret.v13i1s.3023']` | đúng, f1=1.0, score=5 | `['10.1088/2515-7647/ae7491', '10.1088/2515-7647/ae7491', '10.65521/mjret.v13i1s.3023', '10.55041/ijsrem61473']` | trả lời `2016-08-08` thay vì `2026-08-05`, f1=0.0, score=1 |
| **q9** (JADE-Plus date) | `['10.1007/s10278-026-02086-9', '10.55041/ijsrem61473', '10.63503/j.ijaimd.2026.233', '10.3390/buildings16132637']` | đúng, f1=1.0, score=5 | `['10.3390/buildings16132637', '10.63503/j.ijaimd.2026.233', '10.1038/s41746-026-02944-4', '10.55041/ijsrem61473']` | trả lời `2026-07-02` thay vì `2026-07-13`, f1=0.0, score=1 |

Chuỗi nhân quả có artifact chứng minh:
`drop_latest_records` / `stale_publication_date` (corruption_log) → record bị xóa hoặc bị làm stale trong `papers-corrupted` → retrieval miss hoặc answer sai → `retrieval_hit_rate` và `token_f1` sụt.

Đáng chú ý: q3 và q9 đều trả về một ngày *có định dạng hợp lệ nhưng sai* — đây là kiểu lỗi nguy hiểm nhất vì trông "hợp lý" nhưng bịa từ context không liên quan.

---

## 3. Evaluator không biến fallback thành success giả (Item 3)

Kiểm tra `src/evaluation/metrics.py::_judge_answer`: khi LLM lỗi, nhánh fallback dùng heuristic `token_f1` và **ghi rõ** `reasoning="Fallback heuristic judge used because the LLM evaluator was unavailable."`, đồng thời `correct` chỉ true khi `score>=3` (tức f1≥0.5). Không có đường nào mặc định gán success.

Đối chiếu artifact thực tế: quét toàn bộ `judge.reasoning` trong cả 3 file answers →
**10/10 câu đều ghi fallback heuristic judge**. Nghĩa là judge metric trong artifact này là heuristic judge, không phải một LLM judge ngoài. Corrupted vẫn có `judge_accuracy=0.0` vì heuristic chấm sai theo answer sai, không phải do fallback bị đội lốt thành công. Không có "fake pass".

---

## 4. Quality/Freshness cho corrupted — report riêng (Item 4)

Report lưu tách biệt, không đè baseline: `data/quality/corrupted_quality.json`, `data/quality/corrupted_freshness_report.json`.

| Signal | Baseline | Corrupted |
| :--- | :--- | :--- |
| status | PASS | **FAIL** |
| total_rows | 24 | 22 |
| duplicate_paper_ids | 0 | 2 |
| null_summaries | 0 | 3 |
| short_summaries (<100) | 0 | 3 |
| stale_rows | 0 | 4 |
| latest_published | 2026-08-05 | **2026-07-02** |
| oldest_published | 2026-02-26 | **2016-08-08** |
| is_fresh | true | **false** |

`failed_rules` (corrupted): `paper_id_unique`, `summary_no_nulls`, `summary_adequate_length`, `freshness_valid`.

---

## 5. Nối corruption log ↔ quality signal ↔ metric (Item 5)

| Corruption (log) | Count | Quality/Freshness signal đổi | Bằng chứng |
| :--- | ---: | :--- | :--- |
| `drop_latest_records` | 4 | `total_rows` 24→22; `latest_published` 2026-08-05→2026-07-02 | freshness report; và trực tiếp gây retrieval miss q3/q9 (mục 2) |
| `blank_summary` | 3 | `null_summaries=3` (FAIL `summary_no_nulls`) và `short_summaries=3` (FAIL `summary_adequate_length`) — cùng 3 record blank (len=0) | corrupted_quality.json |
| `stale_publication_date` | 3 | `stale_rows` → FAIL `freshness_valid`; `oldest_published`=2016-08-08 | freshness report |
| `duplicate_rows` | 2 | `duplicate_paper_ids=2` (FAIL `paper_id_unique`) | corrupted_quality.json |

→ Các signal FAIL trên đều có corruption tương ứng trong log; metric RAG sụt (mục 1) khớp với việc data bị hỏng, không phải do đổi câu hỏi.

---

## 6. Signal KHÔNG đổi — tránh kết luận quá mức (Item 6)

Ghi nhận rõ các điểm mù để không "over-claim":

- **`paper_id_no_nulls` vẫn PASS** — không corruption nào set null paper_id.
- **`row_count_sufficient` vẫn PASS** — 22 ≥ 1; check ngưỡng row rất lỏng, không phản ánh mất 4 record mới.
- **`title_no_nulls` vẫn PASS dù `truncate_title` cắt 3 title xuống 12 ký tự** — check null không bắt được title bị cắt cụt. **Điểm mù cần lưu ý.**
- **`summary_noise` (3 record) KHÔNG bị bất kỳ check summary nào bắt** — noise được *nối thêm* vào summary dài (1600–2540 ký tự), nên `summary_no_nulls` và `summary_adequate_length` vẫn xanh cho các record này. Đây là kiểu corruption "im lặng" ở tầng quality nhưng vẫn đầu độc retrieval/answer.

Kết luận thận trọng: quality checks hiện tại bắt tốt **missing/duplicate/stale**, nhưng **không** phát hiện **truncate_title** và **summary_noise**. Không nên tuyên bố "quality checks phát hiện mọi corruption".

---

## 7. Ghi chú về repair (không recover hoàn toàn)

`retrieval_hit_rate` phục hồi 1.00 (bằng baseline), và các metric tổng hợp khác cũng trở về đúng baseline artifact hiện có. Điều này cho thấy repair đã đưa hệ thống trở lại trạng thái baseline của run hiện tại; các điểm yếu còn lại là hạn chế vốn có của baseline chứ không phải do corruption sau repair.

---

## 8. Artifact tham chiếu

- `data/results/{baseline,corrupted,repaired}_metrics.json`, `*_answers.json`
- `data/results/corruption_log.json`
- `data/quality/{baseline_quality,corrupted_quality}.json`, `{freshness_report,corrupted_freshness_report}.json`
- `data/reports/baseline_corrupted_comparison.md`

*Không có API key/`.env` trong báo cáo này.*
