# Member Role Report - Day 10: Data Pipeline & Data Observability

## 1. Thong tin ca nhan

| Thong tin | Noi dung |
| :--- | :--- |
| **Ho va ten** | Vũ Quang Tùng |
| **MSSV** | 2A202601545 |
| **Khoa/Lop** | K3 |
| **Ten nhom** | B1-3 - Data Pipeline Lab |
| **Vai tro chinh** | **Role 3: RAG & agent Owner** |
| **Repository** | `K3_Day10_Data-Pipeline-Data-Observability-B1-3` |
| **Ngay hoan thanh** | 2026-08-06 |

---

## 2. Vai tro va pham vi cong viec

### Phan viec so huu

| Module/deliverable | File/ham phu trach | Input nhan vao | Output ban giao | Trang thai |
| :--- | :--- | :--- | :--- | :--- |
| **Frozen Test Set Generator** | `src/evaluation/testset.py` - `build_test_set` | Cleaned DataFrame tu `data/clean/papers_clean.json` | `data/eval/test_set.json` | Hoan thanh |
| **Data Quality & Freshness Checks** | `src/observability/quality.py` - `run_data_quality_checks`, `build_freshness_report` | Cleaned / Corrupted / Repaired DataFrame, `Settings` | `data/quality/*.json`, `data/quality/freshness_report.json` | Hoan thanh |
| **Observability Reporting** | `src/observability/reporting.py` - `generate_phase1_report`, `generate_corruption_report` | Metrics JSON, quality reports, freshness reports | `data/reports/phase1_report.md`, `data/reports/corruption_report.md` | Hoan thanh |

### Viec ho tro ngoai pham vi chinh

| Hoat dong | Thanh vien/module duoc ho tro | Ket qua va bang chung |
| :--- | :--- | :--- |
| Thong nhat data contract voi dong doi | Role 1 (Integrator), Role 2 (Data Ingestion), Role 3 (RAG Owner) | `ground_truth_doc_ids` trong `data/eval/test_set.json` dung DOI/paper_id that va khop voi document ID trong ChromaDB. |

---

## 3. Ket qua theo vai tro

### 3.1. Evaluation set da duoc dong bang

| Nhiem vu da thuc hien | File/ham/artifact lien quan | Ket qua ban giao | Cach xac minh |
| :--- | :--- | :--- | :--- |
| Tao frozen evaluation set | `src/evaluation/testset.py` | `data/eval/test_set.json` voi 10 cau hoi | Kiem tra 4 loai cau hoi: `authors`, `summary`, `date`, `categories`. Moi sample co `question`, `ground_truth`, `ground_truth_doc_ids`. |

Tap test nay duoc giu nguyen cho baseline, corrupted va repaired de delta metric phan anh dung thay doi cua du lieu, khong bi nhieu boi cau hoi moi.

### 3.2. Data quality va freshness

| Nhiem vu da thuc hien | File/ham/artifact lien quan | Ket qua ban giao | Cach xac minh |
| :--- | :--- | :--- | :--- |
| Chay quality checks | `src/observability/quality.py` | `data/quality/baseline_quality.json`, `data/quality/corrupted_quality.json`, `data/quality/repaired_quality.json` | Baseline `PASS`, corrupted `FAIL`, repaired `PASS`. |
| Chay freshness checks | `src/observability/quality.py` | `data/quality/freshness_report.json`, `data/quality/corrupted_freshness_report.json`, `data/quality/repaired_freshness_report.json` | Baseline/repaired `is_fresh = true`, corrupted `is_fresh = false`. |

### 3.3. Reporting va comparison

| Nhiem vu da thuc hien | File/ham/artifact lien quan | Ket qua ban giao | Cach xac minh |
| :--- | :--- | :--- | :--- |
| Sinh baseline report | `src/observability/reporting.py` - `generate_phase1_report` | `data/reports/phase1_report.md` | Report neu ro nguon Crossref, so raw/clean records, metrics baseline va trang thai quality/freshness. |
| Sinh comparison report | `src/observability/reporting.py` - `generate_corruption_report` | `data/reports/corruption_report.md` | Report so sanh baseline, corrupted va repaired tu metrics/quality/freshness that. |

---

## 4. So lieu va bang chung chinh

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

## 5. Giai thich phan ky thuat da thuc hien

### Van de can giai quyet

Neu evaluation set khong duoc freeze, hoac neu quality/freshness khong duoc do tren cung dataset, thi khong the ket luan corruption co that su lam giam chat luong retrieval/answer hay khong. Role 4 chot lai bien so danh gia, roi do delta giua baseline, corrupted va repaired.

### Cach trien khai

1. **Freeze evaluation set:** `build_test_set` chon 10 sample dau tien cua cleaned dataset va tao bo cau hoi co dinh voi `ground_truth_doc_ids` la DOI/paper_id that.
2. **Quality checks:** `run_data_quality_checks` kiem tra row count, null/duplicate `paper_id`, title, summary length va freshness qua `age_days`.
3. **Freshness report:** `build_freshness_report` tong hop `latest_published`, `oldest_published`, `stale_rows`, `is_fresh`.
4. **Comparison report:** `generate_corruption_report` render bang baseline/corrupted/repaired tu metrics, quality va freshness that.

---

## 6. Mot quyet dinh ky thuat quan trong

- **Boi canh:** Muon so sanh baseline, corrupted va repaired mot cach cong bang.
- **Phuong an da chon:** Dung chung mot test set frozen, giu nguyen evaluator va `top_k`, chi thay dataset state.
- **Ly do:** Khi test set khong doi, moi thay doi cua metric moi co y nghia nhan qua voi corruption/repair.
- **Ket qua:** Baseline va repaired khop nhau tren cac metric tong hop, con corrupted suy giam ro ret. Dieu nay cho thay repair da dua he thong quay ve baseline cua artifact hien co.

---

## 7. Mot hit/miss tieu bieu de demo trung thuc

### Hit

- `q3` trong `data/results/baseline_answers.json` va `data/results/repaired_answers.json`
- Cau hoi: thoi diem xuat ban cua paper `SafeRAG`
- Baseline va repaired deu tra dung `2026-08-05`
- Day la vi du cho recovery that o tang retrieval + answer extraction

### Miss

- `q9` trong `data/results/corrupted_answers.json`
- Cau hoi: thoi diem xuat ban cua paper `JADE-Plus`
- Baseline va repaired deu tra dung `2026-07-13`, nhung corrupted tra `2026-07-02`
- Day la vi du ro cua corruption lam hong retrieval va keo answer sai lech

---

## 8. Gioi han va ket luan

- Corruption lam quality/freshness xau di ro ret va keo metric answer xuong manh.
- Repair da phuc hoi data contract, row count, duplicate, null summary va freshness.
- Cac metric tong hop cua repaired quay ve dung baseline artifact hien co.
- Ket luan hop le la: repair thanh cong o tang du lieu va retrieval coverage, dong thoi khop lai baseline quan sat duoc trong run hien tai.
- Bao cao nay khong chua `.env`, API key, token hoac secret.

---

## 9. Cam ket cua thanh vien

- [x] Noi dung bao cao phan anh dung phan viec va muc hieu cua toi.
- [x] Toi co the giai thich luong end-to-end, khong chi module minh phu trach.
- [x] Moi ket luan ve ket qua deu co artifact hoac metric de doi chieu.
- [x] Toi khong ghi "da chay thanh cong" cho phan chua duoc kiem chung.
- [x] Bao cao khong chua `.env`, API key, token hoac secret.
- [x] Bao cao nay khong phai ban sao nguyen van cua bao cao nhom hoac bao cao thanh vien khac.

**Ho va ten:** Chua cung cap trong repo  
**Ngay xac nhan:** 2026-08-06
