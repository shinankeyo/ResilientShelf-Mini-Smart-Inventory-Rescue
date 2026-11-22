# Team Chuyển Kho — HUIT Data Science Challenge 2026

**Tên đề tài:** Tối ưu điều chuyển tồn kho đa cửa hàng dưới nhu cầu bất định bằng thuật toán lai Kirchhoff's Law Algorithm và tìm kiếm cục bộ (KLA–LS).

---

## 1. Phạm vi phiên bản sơ khảo (MVP)
- **Mạng lưới:** 04 cửa hàng `CA_1`, `CA_2`, `CA_3`, `CA_4` từ bộ dữ liệu Kaggle M5 Forecasting – Accuracy.
- **Hàng hóa:** 03 sản phẩm (`item_id`) có doanh số dương tại cả 04 cửa hàng trong 49 ngày cuối.
- **Phân tách thời gian (chống rò rỉ dữ liệu):** 42 ngày đầu làm lịch sử để phân tích EDA và dự báo; 07 ngày cuối giữ riêng hoàn toàn để đánh giá kiểm tra (out-of-sample).
- **Bài toán:** Một quyết định điều chuyển tồn kho tại đầu kỳ, quan sát tác động trong 07 ngày (giả định hàng chuyển ngay trước ngày đầu tiên, chưa xét độ trễ vận chuyển).
- **Thuật toán đối chứng & đề xuất:** `No Transfer`, `Greedy`, `KLA` (Kirchhoff's Law Algorithm), và `KLA-LS` (KLA lai Local Search).

---

## 2. Cấu trúc thư mục
```text
Team_Chuyen_Kho/
├── data/
│   ├── raw/                     # Đặt file sales_train_validation.csv gốc từ Kaggle tại đây
│   ├── m5_selected.csv          # 12 chuỗi (4 cửa hàng × 3 sản phẩm) × 49 ngày
│   ├── demand_forecast.csv      # Dự báo 7 ngày từ 7 ngày lịch sử cuối
│   ├── demand_actual_test.csv   # Doanh số thực 7 ngày cuối (chỉ dùng kiểm tra)
│   ├── inventory_scenario.csv   # Tồn đầu kỳ, ngưỡng an toàn, sức chứa (mô phỏng)
│   ├── transfer_cost.csv        # Ma trận chi phí điều chuyển (mô phỏng)
│   ├── scenarios.csv            # 3 kịch bản: NORMAL, FLASH_SALE (+30%), SURGE (+50%)
│   └── data_dictionary.md       # Từ điển dữ liệu
├── docs/
│   ├── assumptions.md           # Công bố đầy đủ các giả định và tham số mô phỏng
│   ├── tom_tat_y_tuong_dang_ky.md   # Bản nháp tóm tắt đăng ký (<= 300 từ)
│   ├── kich_ban_video_va_qa.md      # Kịch bản video sơ khảo & bộ 7 câu Q&A
│   └── thanh_vien_va_phan_cong.md   # Danh sách thành viên & bảng phân công STEP 0
├── src/
│   ├── prepare_data.py          # Bước 1–3: Cắt dữ liệu M5, vẽ EDA, dự báo, tạo kịch bản
│   ├── simulator.py             # Bộ mô phỏng 7 ngày, kiểm tra tính khả thi, hàm mục tiêu F(X)
│   ├── greedy.py                # Thuật toán tham lam (Greedy baseline)
│   ├── kla.py                   # Thuật toán Kirchhoff's Law Algorithm (Ghasemi et al., 2025)
│   ├── local_search.py          # Tìm kiếm cục bộ & thuật toán lai KLA–LS
│   ├── run_experiments.py       # Chạy thực nghiệm 3 kịch bản × 4 thuật toán × 5 seeds
│   └── verify_pipeline.py       # Kiểm thử tự động (edge cases, liên tục KLA, kiểm tra rò rỉ)
├── app/
│   └── app.py                   # Ứng dụng demo 1 trang bằng Streamlit
├── results/                     # Kết quả CSV, biểu đồ PNG và log chạy
├── report/
│   └── bao_cao_so_khao.pdf      # Báo cáo nộp vòng sơ khảo
├── video/
│   └── demo_so_khao.mp4         # Video giới thiệu giải pháp (< 5 phút)
├── requirements.txt
└── README.md
```

---

## 3. Hướng dẫn cài đặt và chạy trên Windows

### Bước 1: Cài đặt thư viện
```powershell
py -m pip install -r requirements.txt
```

### Bước 2: Tải dữ liệu M5 gốc từ Kaggle
Do bộ dữ liệu cuộc thi **M5 Forecasting – Accuracy** yêu cầu đăng nhập tài khoản Kaggle và chấp nhận điều khoản cuộc thi:
1. Truy cập https://www.kaggle.com/competitions/m5-forecasting-accuracy/data
2. Đăng nhập và chấp nhận điều khoản (*Join Competition / I Understand and Accept*).
3. Tải file `sales_train_validation.csv` (có thể tải thêm `calendar.csv` nếu muốn).
4. Giải nén (nếu là `.zip`) và chép vào thư mục `data/raw/sales_train_validation.csv`.

### Bước 3: Kiểm thử logic thuật toán (có thể chạy trước khi tải dữ liệu)
```powershell
py src/verify_pipeline.py
```

### Bước 4: Xử lý dữ liệu, EDA và tạo kịch bản
```powershell
py src/prepare_data.py
```

### Bước 5: Chạy thực nghiệm và sinh biểu đồ
```powershell
py src/run_experiments.py
```

### Bước 6: Khởi chạy ứng dụng Demo Streamlit
```powershell
py -m streamlit run app/app.py
```

---

## 4. Tài liệu tham khảo chính
1. Kaggle, *M5 Forecasting – Accuracy*, https://www.kaggle.com/competitions/m5-forecasting-accuracy/data
2. Ghasemi, M., Khodadadi, N., Trojovský, P., Li, L., Mansor, Z., Abualigah, L., Alharbi, A. H., & El-Kenawy, E.-S. M. (2025). *Kirchhoff’s law algorithm (KLA): a novel physics-inspired non-parametric metaheuristic algorithm for optimization problems*. Artificial Intelligence Review, 58, 325. https://doi.org/10.1007/s10462-025-11289-5
3. Mã tham khảo KLA trên MathWorks File Exchange: https://www.mathworks.com/matlabcentral/fileexchange/181589-kirchhoff-s-law-algorithm-kla
