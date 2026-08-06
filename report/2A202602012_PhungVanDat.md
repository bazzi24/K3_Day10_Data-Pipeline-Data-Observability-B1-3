# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin           | Nội dung                                                     |
| :------------------ | :----------------------------------------------------------- |
| **Họ và tên**       | Phùng Văn Đạt                                                |
| **MSSV**            | [Điền MSSV]                                                  |
| **Khóa/Lớp**        | K3                                                           |
| **Tên nhóm**        | Nhóm 4 người — Data Pipeline Lab                             |
| **Vai trò chính**   | **Role 1: Integrator / Configuration & Orchestration Owner** |
| **Repository**      | `K3_Day10_Data-Pipeline-Data-Observability-B1-3`             |
| **Ngày hoàn thành** | 2026-08-06                                                   |

---

## 2. Vai trò và phạm vi công việc

### Phạm vi phụ trách

* Cấu hình môi trường và kiểm tra dependency của dự án.
* Điều phối (orchestration) pipeline giữa các thành viên.
* Thống nhất branch, artifact và tiêu chí hoàn thành.
* Chuẩn bị pipeline phục vụ release và demo.

### Công việc thực hiện trong mốc Day 10

| Nhiệm vụ            | Nội dung thực hiện                                                                                    | Kết quả    |
| :------------------ | :---------------------------------------------------------------------------------------------------- | :--------- |
| Chốt phân công      | Thống nhất role của từng thành viên, branch làm việc và tiêu chí hoàn thành của từng checkpoint       | Hoàn thành |
| Kiểm tra môi trường | Kiểm tra Python 3.11–3.13, virtual environment, dependencies, provider configuration và `.env` cục bộ | Hoàn thành |
| Thiết kế pipeline   | Xây dựng sơ đồ handoff giữa các module từ Data Ingestion đến Evaluation                               | Hoàn thành |
| Điều phối artifact  | Thống nhất đường dẫn lưu trữ dữ liệu raw, clean, embeddings, reports và metrics                       | Hoàn thành |

---

## 3. Kết quả theo vai trò

### 3.1. Thiết lập cấu hình dự án

* Kiểm tra môi trường Python đáp ứng yêu cầu của bài lab.
* Xác nhận virtual environment hoạt động đúng.
* Kiểm tra các package trong `requirements.txt`.
* Kiểm tra cấu hình `.env` và provider trước khi chạy pipeline.
* Đảm bảo các thành viên sử dụng cùng cấu hình để tránh sai lệch kết quả.

---

### 3.2. Điều phối pipeline

Pipeline của dự án được thống nhất theo luồng:

```text
Crossref API
        │
        ▼
Raw Response
        │
        ▼
Raw Records
        │
        ▼
Clean Dataset
        │
        ▼
Embedding + ChromaDB
        │
        ▼
Evaluation
        │
        ▼
Quality / Freshness
        │
        ▼
Reports
```

Luồng dữ liệu được thống nhất giữa các role để bảo đảm mỗi module chỉ sử dụng artifact do module trước sinh ra.

---

### 3.3. Chuẩn hóa artifact

Các artifact được thống nhất trước khi phát triển:

* `data/raw/crossref_response.json`
* `data/raw/crossref_records.json`
* `data/clean/papers_clean.csv`
* `data/clean/papers_clean.json`
* `data/embeddings/papers_embeddings.json`
* `data/results/*.json`
* `data/reports/*.md`

Việc thống nhất tên file và đường dẫn giúp các module hoạt động đồng nhất và giảm lỗi tích hợp.

---

## 4. Quyết định kỹ thuật

### Bối cảnh

Nhiều thành viên phát triển song song trên các module khác nhau nên dễ xảy ra lỗi tích hợp nếu không thống nhất cấu hình và artifact.

### Quyết định

* Thống nhất cấu trúc thư mục và đường dẫn dữ liệu.
* Thống nhất phiên bản Python hỗ trợ (3.11–3.13).
* Thống nhất provider configuration thông qua `.env`.
* Thống nhất artifact được sinh ở mỗi checkpoint.

### Lý do

Giảm xung đột khi merge code, giúp pipeline có thể chạy end-to-end và thuận lợi cho quá trình demo.

---

## 5. Kết quả đạt được

* Pipeline giữa các module được thống nhất.
* Các thành viên làm việc trên branch riêng và tích hợp theo cùng data contract.
* Môi trường chạy được chuẩn hóa trước khi phát triển.
* Artifact được đặt tên thống nhất giữa các module.
* Hỗ trợ quá trình release và demo của nhóm.

---

## 6. Khó khăn và cách xử lý

Trong quá trình tích hợp xuất hiện một số lỗi về import module, cấu hình package và môi trường Python. Việc chuẩn hóa cấu hình dự án, virtual environment và dependency giúp các thành viên sử dụng cùng môi trường, giảm lỗi khi chạy pipeline.

---

## 7. Kết luận

Role 1 tập trung vào điều phối toàn bộ pipeline thay vì phát triển thuật toán. Các quyết định về cấu hình, artifact và quy trình tích hợp giúp các module của nhóm hoạt động thống nhất, hỗ trợ quá trình đánh giá, repair và demo cuối cùng.

---

## 8. Cam kết

* [x] Báo cáo phản ánh đúng phần việc tôi phụ trách.
* [x] Tôi hiểu luồng pipeline end-to-end của hệ thống.
* [x] Các quyết định kỹ thuật đều dựa trên artifact và cấu hình của dự án.
* [x] Báo cáo không chứa API key hoặc thông tin nhạy cảm.
* [x] Báo cáo không sao chép nguyên văn báo cáo của thành viên khác.

**Họ và tên:** Phùng Văn Đạt

**Ngày xác nhận:** 2026-08-06
