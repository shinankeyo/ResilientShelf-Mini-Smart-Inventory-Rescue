# Bản nháp Tóm tắt Ý tưởng Đăng ký (STEP 8 — Hạn trước 02/12/2026)

- **Đội thi:** Team Chuyển Kho
- **Đề tài:** Tối ưu điều chuyển tồn kho đa cửa hàng dưới nhu cầu bất định bằng thuật toán lai Kirchhoff’s Law Algorithm và tìm kiếm cục bộ (KLA–LS)
- **Độ dài nội dung:** 280 từ (đạt chuẩn `<= 300 từ` theo Thể lệ HUIT DSC 2026)

---

Trong bán lẻ đa cửa hàng, chênh lệch nhu cầu theo địa điểm và biến động ngắn hạn thường gây nghịch lý: cùng một sản phẩm nhưng có cửa hàng hết hàng mất doanh thu trong khi cửa hàng khác lại tồn kho dư thừa. Team Chuyển Kho đề xuất giải pháp tối ưu điều chuyển tồn kho nội bộ (lateral transshipment) nhằm cân bằng hàng hóa, giảm thiếu hàng và tối ưu tổng chi phí vận hành.

Ở vòng sơ khảo, nhóm xây dựng mô hình và bộ mô phỏng 7 ngày từ dữ liệu doanh số bán lẻ thật Kaggle M5 Forecasting – Accuracy (04 cửa hàng CA_1–CA_4, 03 sản phẩm FOODS_3_090, FOODS_3_586, FOODS_3_252 trong 49 ngày cuối). Để chống rò rỉ dữ liệu, 42 ngày đầu dùng cho EDA và dự báo nhu cầu 7 ngày; 07 ngày cuối giữ riêng hoàn toàn để hậu kiểm. Tồn kho đầu kỳ, ngưỡng an toàn, sức chứa và chi phí điều chuyển được mô phỏng theo quy tắc minh bạch (giả định điều chuyển ngay đầu kỳ, chưa xét độ trễ giao hàng).

Nhóm cài đặt và đối chứng 04 phương pháp: No Transfer, Greedy, Kirchhoff’s Law Algorithm (KLA) và KLA–Local Search (KLA–LS) trên 03 kịch bản (NORMAL, FLASH_SALE +30%, SURGE +50%). Kết quả trên tập kiểm tra 7 ngày cho thấy KLA–LS giảm 63,8%–65,2% tổng chi phí, nâng Fill Rate từ 83,2%–87,4% lên 97,6%–98,2% và ổn định tuyệt đối qua 5 seeds. Giải pháp được đóng gói thành ứng dụng demo Streamlit trực quan và dự kiến mở rộng sang bài toán nhiều kỳ, xét độ trễ vận chuyển cùng ràng buộc tải trọng ở vòng chung kết.
