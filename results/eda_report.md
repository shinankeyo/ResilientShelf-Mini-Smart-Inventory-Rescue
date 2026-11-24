# Báo cáo Kiểm tra Dữ liệu & EDA (STEP 2)

- **Số chuỗi (`store × item`):** 12
- **Số ngày quan sát:** 49 (`d_1865 .. d_1913`)
  - Lịch sử (*History*): 42 ngày (`d_1865 .. d_1906`)
  - Kiểm tra (*Test*): 7 ngày (`d_1907 .. d_1913`)
- **Số giá trị thiếu (`NaN`):** 0
- **Số giá trị âm (`< 0`):** 0
- **Số ngày doanh số `= 0`:** 0 / 588 (0.00%) *(Giữ nguyên, không xóa)*

## So sánh sai số dự báo 7 ngày trên tập test *(chỉ tham khảo EDA)*
- **MAE Trung bình 7 ngày lịch sử cuối (dùng cho MVP):** `22.58 đơn vị`
- **MAE Đối chứng 7 ngày tuần liền trước đó (`lag 2w`):** `18.67 đơn vị`

## Bảng tổng hợp Dự báo 7 ngày vs Thực tế 7 ngày

```text
    item_id store_id  daily_mean_last7_hist  forecast_7d  seasonal_naive_7d  actual_7d
FOODS_3_090     CA_1                53.0000        371.0              371.0        381
FOODS_3_090     CA_2                51.1429        358.0              324.0        382
FOODS_3_090     CA_3               123.1429        862.0              740.0        761
FOODS_3_090     CA_4                28.4286        199.0              182.0        172
FOODS_3_586     CA_1                37.2857        261.0              278.0        268
FOODS_3_586     CA_2                31.2857        219.0              226.0        252
FOODS_3_586     CA_3                69.1429        484.0              501.0        483
FOODS_3_586     CA_4                16.7143        117.0              106.0        111
FOODS_3_252     CA_1                34.7143        243.0              280.0        260
FOODS_3_252     CA_2                31.8571        223.0              257.0        234
FOODS_3_252     CA_3                50.8571        356.0              329.0        325
FOODS_3_252     CA_4                16.0000        112.0              128.0        109
```
