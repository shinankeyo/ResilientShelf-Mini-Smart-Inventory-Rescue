# Công bố các Giả định và Quy tắc Mô phỏng (Assumptions)

**Đội thi:** Team Chuyển Kho — HUIT Data Science Challenge 2026 (Vòng Sơ Khảo)

---

## 1. Phân biệt dữ liệu thật và dữ liệu mô phỏng
- **Dữ liệu THẬT:** Chuỗi doanh số bán lẻ hàng ngày của 04 cửa hàng (`CA_1`, `CA_2`, `CA_3`, `CA_4`) và 03 sản phẩm trong 49 ngày cuối từ bộ dữ liệu công khai **Kaggle M5 Forecasting – Accuracy** (`sales_train_validation.csv`).
- **Dữ liệu MÔ PHỎNG** (vì bộ M5 không công bố tồn kho, sức chứa hay cước vận chuyển):
  - Tồn kho đầu kỳ (`initial_inventory`)
  - Ngưỡng tồn kho an toàn (`safety_target`)
  - Sức chứa lưu kho (`capacity`)
  - Chi phí điều chuyển đơn vị (`unit_cost_usd`)
  - Hệ số phạt thiếu hàng và chi phí tồn dư (`shortage_penalty`, `leftover_cost`)

---

## 2. Giả định vận hành phiên bản sơ khảo (MVP)
- **Quyết định một kỳ (Single-period transfer):** Toàn bộ lệnh điều chuyển được thực hiện **ngay trước ngày đầu tiên** của chu kỳ 7 ngày.
- **Độ trễ vận chuyển (Lead time):** Giả định bằng `0` (hàng chuyển đến ngay đầu kỳ). Báo cáo không khẳng định đã xét độ trễ giao hàng ở vòng sơ khảo; yếu tố độ trễ và điều chuyển nhiều kỳ được xác định là hướng phát triển cho vòng sau.
- **Đại diện nhu cầu (Demand proxy):** Dùng doanh số quan sát trong M5 làm đại diện gần đúng cho nhu cầu. Doanh số thực tế có thể nhỏ hơn nhu cầu khi cửa hàng hết hàng (*censored demand*).
- **Bảo toàn dữ liệu gốc:** Không xóa ngày có doanh số bằng `0`; không sửa doanh số `0` thành số dương.

---

## 3. Quy tắc chống rò rỉ dữ liệu (No Data Leakage)
- 49 ngày cuối được chia cố định:
  - **42 ngày đầu:** Tập lịch sử (dùng cho EDA, tính dự báo $\hat{D}$ và sinh kịch bản).
  - **07 ngày cuối:** Tập kiểm tra (`demand_actual_test.csv`), tách biệt hoàn toàn khỏi quá trình tối ưu.
- Dự báo tổng nhu cầu 7 ngày chỉ dùng 7 ngày lịch sử ngay trước kỳ kiểm tra:
  $$\hat{D}_{ik} = 7 \times \text{mean}(\text{sales trong 7 ngày lịch sử cuối của cửa hàng } i, \text{ SKU } k)$$
- Mọi thuật toán (`Greedy`, `KLA`, `KLA–LS`) chỉ tối ưu trên nhu cầu dự báo $\hat{D}$ (có nhân hệ số kịch bản), **không** nhìn thấy doanh số thực 7 ngày kiểm tra.
- Đánh giá cuối cùng (`Total Cost`, `Unmet Demand`, `Fill Rate`) được tính lại trên doanh số thực 7 ngày kiểm tra đã giữ riêng.

---

## 4. Quy tắc tạo kịch bản tồn kho, sức chứa và chi phí
- **Tồn kho đầu kỳ** (làm tròn về số nguyên từ $\hat{D}$):
  - `CA_1`: `round(0.50 * D_hat)` → Thiếu hàng rõ rệt (~50% nhu cầu dự báo)
  - `CA_2`: `round(1.60 * D_hat)` → Dư hàng (~160% nhu cầu dự báo)
  - `CA_3`: `round(1.60 * D_hat)` → Dư hàng (~160% nhu cầu dự báo)
  - `CA_4`: `round(1.10 * D_hat)` → Cân bằng / dư nhẹ (~110% nhu cầu dự báo)
- **Tồn kho mục tiêu an toàn tại cửa hàng gửi:**
  - `safety_target = round(1.00 * D_hat)`
  - Chỉ cho phép xuất phần hàng vượt ngưỡng an toàn: `max_surplus_send = max(0, initial_inventory - safety_target)`
- **Sức chứa tối đa mỗi cửa hàng – sản phẩm:**
  - `capacity = max(ceil(2.00 * D_hat), initial_inventory)`
- **Ma trận chi phí điều chuyển cố định, đối xứng, đường chéo bằng 0 (USD/đơn vị):**
  - `CA_1 <-> CA_2`: `1.5 USD`
  - `CA_1 <-> CA_3`: `2.5 USD`
  - `CA_1 <-> CA_4`: `3.5 USD`
  - `CA_2 <-> CA_3`: `1.0 USD`
  - `CA_2 <-> CA_4`: `2.0 USD`
  - `CA_3 <-> CA_4`: `3.0 USD`
- **Ba kịch bản nhu cầu:**
  - `NORMAL`: Nhu cầu gốc (hệ số `1.0` toàn mạng lưới).
  - `FLASH_SALE`: Tăng `+30%` (hệ số `1.3`) **chỉ cho 1 cửa hàng (`CA_1`) và 1 sản phẩm** có doanh số cao nhất (không tăng đồng loạt toàn mạng lưới).
  - `SURGE`: Tăng `+50%` (hệ số `1.5`) **chỉ cho 1 cửa hàng (`CA_1`) và 1 sản phẩm** có doanh số cao nhất.

---

## 5. Hàm mục tiêu và chỉ số đánh giá dùng chung
- **Biến quyết định:** $x_{ijk} \in \mathbb{Z}_{\ge 0}$ (số đơn vị SKU $k$ chuyển từ cửa hàng $i$ sang cửa hàng $j$).
- **Tồn kho sau điều chuyển tại đầu kỳ:**
  $$I_{ik,\text{after}} = I_{ik,\text{before}} + \sum_j x_{jik} - \sum_j x_{ijk}$$
- **Hàm mục tiêu thống nhất cho mọi thuật toán (đơn vị: USD):**
  $$F(X) = C_{\text{move}}(X) + 10.0 \times \text{Shortage}(X) + 0.5 \times \text{Leftover}(X)$$
  Trong đó:
  - $C_{\text{move}}(X) = \sum_{i,j,k} c_{ij} x_{ijk}$: Tổng chi phí điều chuyển.
  - `10.0 USD/đv`: Chi phí phạt giả định cho mỗi đơn vị hàng bị thiếu (`unmet demand`).
  - `0.5 USD/đv`: Chi phí lưu kho/tồn dư giả định cho mỗi đơn vị tồn cuối kỳ 7 ngày.
- **Tỷ lệ đáp ứng nhu cầu (Fill Rate):**
  $$\text{FillRate} = 100 \times \frac{\text{TotalDemand} - \text{UnmetDemand}}{\text{TotalDemand}}\ (\%) $$
  Khi `TotalDemand = 0`: ghi `"N/A (không xác định)"`, không tự động gán `100%`.

---

## 6. Cấu hình thử nghiệm thuật toán KLA và KLA–LS
- **Thuật toán gốc tham khảo:** Kirchhoff's Law Algorithm (Ghasemi et al., 2025, *Artificial Intelligence Review*, 58, 325, DOI: `10.1007/s10462-025-11289-5`).
- **Cấu hình thử nghiệm sơ khảo:** `pop_size = 15`, `max_iter = 35`, chạy lặp 5 seeds (`42, 43, 44, 45, 46`) để đánh giá tính ổn định sơ bộ. Đây là cấu hình thử nghiệm cho bản MVP, không khẳng định là siêu tham số tối ưu toàn cục.
- `KLA` (thuần) và `KLA–LS` (lai Local Search) được đánh giá và báo cáo tách biệt.
