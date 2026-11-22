# Data Dictionary — Team Chuyển Kho (HUIT Data Science Challenge 2026)

> **Lưu ý quan trọng về bản chất dữ liệu:**
> - Bộ dữ liệu gốc **Kaggle M5 Forecasting – Accuracy** (`sales_train_validation.csv`) là **dữ liệu doanh số bán lẻ** (unit sales), **không phải** dữ liệu tồn kho thực tế.
> - Trong phiên bản sơ khảo (MVP), nhóm sử dụng lịch sử doanh số làm đại diện gần đúng cho nhu cầu khách hàng (*demand proxy*). Do doanh số quan sát có thể bị chặn dưới khi cửa hàng hết hàng (*censored demand*), đây được công bố rõ là một giới hạn nghiên cứu của mô hình.
> - Các thông số tồn kho đầu kỳ, ngưỡng tồn an toàn, sức chứa cửa hàng và chi phí điều chuyển là **dữ liệu mô phỏng** theo quy tắc minh bạch (xem `docs/assumptions.md`).

---

## 1. `data/raw/sales_train_validation.csv` (Dữ liệu thật từ Kaggle M5)
- `id`: Mã định danh duy nhất của chuỗi (`item_id + store_id + validation`).
- `item_id`: Mã sản phẩm (SKU), ví dụ `FOODS_3_090`.
- `dept_id`: Mã nhóm hàng (department).
- `cat_id`: Mã ngành hàng (`HOBBIES`, `HOUSEHOLD`, `FOODS`).
- `store_id`: Mã cửa hàng (`CA_1`, `CA_2`, `CA_3`, `CA_4`, `TX_1..3`, `WI_1..3`).
- `state_id`: Mã bang (`CA`, `TX`, `WI`).
- `d_1..d_1913`: Số lượng đơn vị sản phẩm bán ra (`sales`, số nguyên `>= 0`) theo từng ngày.

---

## 2. `data/m5_selected.csv` (Dữ liệu thật sau khi lọc phạm vi MINI)
- **Số dòng:** 12 chuỗi (04 cửa hàng `CA_1..CA_4` × 03 sản phẩm có tổng bán > 0 tại cả 4 cửa hàng trong 49 ngày cuối).
- `item_id`: Mã sản phẩm (03 SKU được chọn).
- `store_id`: Mã cửa hàng trong `{CA_1, CA_2, CA_3, CA_4}`.
- `d_1865..d_1913` (49 cột ngày cuối):
  - **42 ngày đầu (`d_1865..d_1906`):** Tập lịch sử dùng cho EDA và dự báo.
  - **07 ngày cuối (`d_1907..d_1913`):** Tập kiểm tra (test) giữ riêng, không đưa vào bước tối ưu.

---

## 3. `data/demand_forecast.csv` (Dự báo từ lịch sử — KHÔNG dùng tập test)
- `item_id`: Mã sản phẩm.
- `store_id`: Mã cửa hàng.
- `daily_mean_last7_hist`: Trung bình doanh số/ngày trong 7 ngày lịch sử cuối.
- `forecast_7d`: Dự báo tổng nhu cầu 7 ngày = `7 × daily_mean_last7_hist`.
- `seasonal_naive_7d`: Dự báo đối chứng 7 ngày tuần liền trước đó (`lag 2w`, `d-14..d-8`) dùng để so sánh chất lượng dự báo trong EDA.

---

## 4. `data/demand_actual_test.csv` (Tập kiểm tra 7 ngày — Giữ riêng)
- `item_id`: Mã sản phẩm.
- `store_id`: Mã cửa hàng.
- `d_1907..d_1913` (7 ngày cuối): Doanh số thực quan sát được từng ngày trong kỳ test.
- `actual_7d`: Tổng doanh số thực quan sát được trong 7 ngày kiểm tra.

---

## 5. `data/inventory_scenario.csv` (Dữ liệu tồn kho & sức chứa MÔ PHỎNG)
- `item_id`: Mã sản phẩm.
- `store_id`: Mã cửa hàng.
- `forecast_7d`: Tổng nhu cầu dự báo 7 ngày (từ `demand_forecast.csv`).
- `initial_inventory`: Tồn kho đầu kỳ giả lập (làm tròn nguyên): `CA_1 ≈ 50%`, `CA_2 ≈ 160%`, `CA_3 ≈ 160%`, `CA_4 ≈ 110%` của `forecast_7d`.
- `safety_target`: Ngưỡng tồn kho an toàn mục tiêu = `round(100% × forecast_7d)`.
- `max_surplus_send`: Lượng hàng dư tối đa được phép xuất đi = `max(0, initial_inventory - safety_target)`.
- `capacity`: Sức chứa tối đa = `max(ceil(200% × forecast_7d), initial_inventory)`.

---

## 6. `data/transfer_cost.csv` (Ma trận chi phí điều chuyển MÔ PHỎNG)
- `from_store`: Cửa hàng gửi (`CA_1..CA_4`).
- `to_store`: Cửa hàng nhận (`CA_1..CA_4`).
- `unit_cost_usd`: Chi phí điều chuyển giả định (USD/đơn vị), đối xứng, đường chéo = `0`, nằm trong khoảng `1.0 – 3.5 USD/đơn vị` (không phải báo giá vận tải thật).

---

## 7. `data/scenarios.csv` (Định nghĩa các kịch bản nhu cầu)
- `scenario`: Tên kịch bản (`NORMAL`, `FLASH_SALE`, `SURGE`).
- `item_id`: Mã sản phẩm áp dụng hệ số nhân.
- `store_id`: Mã cửa hàng áp dụng hệ số nhân.
- `multiplier`: Hệ số nhân nhu cầu (`1.0` cho `NORMAL`; `1.3` cho `FLASH_SALE` và `1.5` cho `SURGE` chỉ áp dụng lên 1 cặp cửa hàng–sản phẩm mục tiêu để mô phỏng sốc cục bộ).
- `description`: Mô tả ngắn ý nghĩa kịch bản.
