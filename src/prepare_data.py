"""
prepare_data.py
---------------
Thực hiện trọn vẹn STEP 1, STEP 2 và STEP 3 theo hướng dẫn vòng sơ khảo:
- STEP 1: Đọc tiết kiệm RAM từ data/raw/sales_train_validation.csv, lọc 4 cửa hàng
          CA_1..CA_4, chọn 3 item_id có tổng doanh số > 0 ở cả 4 cửa hàng trong
          49 ngày cuối -> lưu data/m5_selected.csv.
- STEP 2: Kiểm tra chất lượng dữ liệu (không xóa ngày doanh số = 0), vẽ 3 biểu đồ
          EDA (results/eda_01.png, eda_02.png, eda_03.png), tách chặt 42 ngày lịch
          sử / 7 ngày kiểm tra (chống data leakage), tính dự báo 7 ngày từ trung
          bình 7 ngày lịch sử cuối -> lưu data/demand_forecast.csv và
          data/demand_actual_test.csv.
- STEP 3: Sinh kịch bản tồn kho đầu kỳ (CA_1 ~50%, CA_2/CA_3 ~160%, CA_4 ~110%),
          ngưỡng an toàn 100%, sức chứa >=200%, ma trận chi phí điều chuyển đối
          xứng 1.0–3.5 USD/đơn vị, và 3 kịch bản NORMAL / FLASH_SALE / SURGE
          -> lưu data/inventory_scenario.csv, data/transfer_cost.csv, data/scenarios.csv.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import List, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_CSV = DATA_DIR / "raw" / "sales_train_validation.csv"
RESULTS_DIR = PROJECT_ROOT / "results"

STORES: List[str] = ["CA_1", "CA_2", "CA_3", "CA_4"]
N_ITEMS = 3
N_RECENT_DAYS = 49
N_HISTORY_DAYS = 42
N_TEST_DAYS = 7

# Quy tắc mô phỏng tồn kho đầu kỳ (công bố trong docs/assumptions.md)
INITIAL_INV_RATIO = {
    "CA_1": 0.50,
    "CA_2": 1.60,
    "CA_3": 1.60,
    "CA_4": 1.10,
}
SAFETY_TARGET_RATIO = 1.00
CAPACITY_RATIO = 2.00

# Ma trận chi phí điều chuyển giả định (USD/đơn vị), đối xứng, đường chéo = 0
TRANSFER_COST_MATRIX = {
    ("CA_1", "CA_2"): 1.5,
    ("CA_1", "CA_3"): 2.5,
    ("CA_1", "CA_4"): 3.5,
    ("CA_2", "CA_3"): 1.0,
    ("CA_2", "CA_4"): 2.0,
    ("CA_3", "CA_4"): 3.0,
}


def step1_select_m5_data(raw_csv: Path = RAW_CSV) -> Tuple[pd.DataFrame, List[str], List[str]]:
    """STEP 1: Lọc 4 cửa hàng × 3 sản phẩm × 49 ngày cuối từ file M5 gốc."""
    if not raw_csv.exists() or raw_csv.stat().st_size == 0:
        raise FileNotFoundError(
            f"Không tìm thấy dữ liệu M5 gốc tại: {raw_csv}\n"
            "Hãy tải file sales_train_validation.csv từ "
            "https://www.kaggle.com/competitions/m5-forecasting-accuracy/data "
            "và đặt vào thư mục data/raw/."
        )

    # Đọc dòng tiêu đề trước để chỉ nạp 49 cột ngày cuối (tiết kiệm RAM)
    header_cols = pd.read_csv(raw_csv, nrows=0).columns.tolist()
    day_cols = [c for c in header_cols if c.startswith("d_")]
    if len(day_cols) < N_RECENT_DAYS:
        raise ValueError(f"File dữ liệu chỉ có {len(day_cols)} cột ngày (< {N_RECENT_DAYS}).")

    recent_days = day_cols[-N_RECENT_DAYS:]
    usecols = ["item_id", "store_id"] + recent_days

    print(f"[STEP 1] Đang đọc {raw_csv.name} (chỉ nạp {len(usecols)} cột cho {len(STORES)} cửa hàng)...")
    raw = pd.read_csv(raw_csv, usecols=usecols)
    raw = raw[raw["store_id"].isin(STORES)].copy()

    history_days = recent_days[:N_HISTORY_DAYS]
    last7_hist_days = history_days[-7:]

    raw["last49_sum"] = raw[recent_days].sum(axis=1)
    raw["last7_hist_sum"] = raw[last7_hist_days].sum(axis=1)

    # Yêu cầu chặt theo ghi chú STEP 1:
    # - Xuất hiện đủ ở cả 4 cửa hàng
    # - Mỗi chuỗi (store_id x item_id) đều có tổng bán > 0 trong 49 ngày
    #   (và ưu tiên sản phẩm có tổng bán > 0 trong 7 ngày lịch sử cuối để dự báo > 0)
    store_counts = raw.groupby("item_id")["store_id"].nunique()
    min_49_by_item = raw.groupby("item_id")["last49_sum"].min()
    min_7h_by_item = raw.groupby("item_id")["last7_hist_sum"].min()

    valid_ids = store_counts[
        (store_counts == len(STORES))
        & (min_49_by_item > 0)
        & (min_7h_by_item > 0)
    ].index

    if len(valid_ids) < N_ITEMS:
        # Dự phòng: chỉ yêu cầu mỗi chuỗi > 0 trong 49 ngày
        valid_ids = store_counts[(store_counts == len(STORES)) & (min_49_by_item > 0)].index

    if len(valid_ids) < N_ITEMS:
        raise ValueError("Không tìm đủ 3 sản phẩm thỏa mãn bán ở cả 4 cửa hàng với doanh số dương.")

    candidates = raw[raw["item_id"].isin(valid_ids)].copy()
    scores = candidates.groupby("item_id")["last49_sum"].sum()
    chosen_items = scores.sort_values(ascending=False).head(N_ITEMS).index.tolist()

    selected = candidates[candidates["item_id"].isin(chosen_items)].copy()
    selected["store_id"] = pd.Categorical(selected["store_id"], categories=STORES, ordered=True)
    selected["item_id"] = pd.Categorical(selected["item_id"], categories=chosen_items, ordered=True)
    selected = selected.sort_values(["item_id", "store_id"]).reset_index(drop=True)
    selected["item_id"] = selected["item_id"].astype(str)
    selected["store_id"] = selected["store_id"].astype(str)

    out_cols = ["item_id", "store_id"] + recent_days
    out_df = selected[out_cols].copy()
    out_path = DATA_DIR / "m5_selected.csv"
    out_df.to_csv(out_path, index=False)

    print(f"[STEP 1 OK] Đã lưu {out_path.name} | Items: {chosen_items} | Rows: {len(out_df)}")
    return out_df, chosen_items, recent_days


def step2_eda_and_forecast(
    selected: pd.DataFrame,
    chosen_items: List[str],
    recent_days: List[str],
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """STEP 2: Kiểm tra chất lượng dữ liệu, vẽ 3 biểu đồ EDA, tạo dự báo & tập test."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    history_days = recent_days[:N_HISTORY_DAYS]
    test_days = recent_days[N_HISTORY_DAYS:]
    assert len(history_days) == N_HISTORY_DAYS and len(test_days) == N_TEST_DAYS

    # --- 1. Kiểm tra chất lượng dữ liệu ---
    sales_values = selected[recent_days].to_numpy()
    n_rows = len(selected)
    n_days = len(recent_days)
    n_missing = int(pd.isna(sales_values).sum())
    n_negative = int((sales_values < 0).sum())
    n_zeros = int((sales_values == 0).sum())
    zero_pct = 100.0 * n_zeros / sales_values.size

    # --- 2. Dự báo đơn giản (CHỈ dùng lịch sử, KHÔNG nhìn thấy 7 ngày test) ---
    last7_hist = history_days[-7:]
    prev7_hist = history_days[-14:-7]  # Dùng so sánh Seasonal Naive (tuần trước đó)

    forecast_rows = []
    actual_rows = []
    for _, row in selected.iterrows():
        item_id = row["item_id"]
        store_id = row["store_id"]

        hist_last7_vals = row[last7_hist].to_numpy(dtype=float)
        daily_mean = float(np.mean(hist_last7_vals))
        forecast_7d = 7.0 * daily_mean
        seasonal_naive_7d = float(np.sum(row[prev7_hist].to_numpy(dtype=float)))

        forecast_rows.append(
            {
                "item_id": item_id,
                "store_id": store_id,
                "daily_mean_last7_hist": round(daily_mean, 4),
                "forecast_7d": round(forecast_7d, 4),
                "seasonal_naive_7d": round(seasonal_naive_7d, 4),
            }
        )

        test_vals = {d: int(row[d]) for d in test_days}
        actual_record = {
            "item_id": item_id,
            "store_id": store_id,
            **test_vals,
            "actual_7d": int(sum(test_vals.values())),
        }
        actual_rows.append(actual_record)

    forecast_df = pd.DataFrame(forecast_rows)
    actual_df = pd.DataFrame(actual_rows)

    forecast_df.to_csv(DATA_DIR / "demand_forecast.csv", index=False)
    actual_df.to_csv(DATA_DIR / "demand_actual_test.csv", index=False)

    # Đánh giá độ chính xác dự báo (chỉ để báo cáo EDA, không tuning)
    merged_eval = forecast_df.merge(actual_df[["item_id", "store_id", "actual_7d"]], on=["item_id", "store_id"])
    mae_ma7 = float(np.mean(np.abs(merged_eval["forecast_7d"] - merged_eval["actual_7d"])))
    mae_snaive = float(np.mean(np.abs(merged_eval["seasonal_naive_7d"] - merged_eval["actual_7d"])))

    # --- 3. Biểu đồ EDA 01: Biến động doanh số 49 ngày theo sản phẩm & cửa hàng ---
    fig, axes = plt.subplots(len(chosen_items), 1, figsize=(11, 8.5), sharex=True)
    if len(chosen_items) == 1:
        axes = [axes]
    x_idx = np.arange(1, N_RECENT_DAYS + 1)
    for ax, item_id in zip(axes, chosen_items):
        sub = selected[selected["item_id"] == item_id]
        for store_id in STORES:
            srow = sub[sub["store_id"] == store_id]
            if not srow.empty:
                y = srow[recent_days].iloc[0].to_numpy(dtype=float)
                ax.plot(x_idx, y, marker="o", markersize=2.5, linewidth=1.4, label=store_id)
        ax.axvline(N_HISTORY_DAYS + 0.5, color="crimson", linestyle="--", linewidth=1.3, label="Ranh giới History / Test" if ax is axes[0] else None)
        ax.set_title(f"Biến động doanh số 49 ngày gần nhất — {item_id}", fontsize=10.5, fontweight="bold")
        ax.set_ylabel("Doanh số (đv/ngày)")
        ax.grid(alpha=0.3)
        ax.legend(loc="upper right", ncol=5, fontsize=8)
    axes[-1].set_xlabel(f"Ngày trong cửa sổ 49 ngày ({recent_days[0]} → {recent_days[-1]}) | Ngày 1–42: Lịch sử, Ngày 43–49: Test")
    fig.suptitle("EDA 01: Chuỗi thời gian doanh số bán lẻ M5 (4 cửa hàng × 3 sản phẩm)", fontsize=12, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    fig.savefig(RESULTS_DIR / "eda_01.png", dpi=150)
    plt.close(fig)

    # --- 4. Biểu đồ EDA 02: Tổng doanh số 42 ngày lịch sử theo cửa hàng & sản phẩm ---
    hist_totals = selected[["item_id", "store_id"]].copy()
    hist_totals["total_42d"] = selected[history_days].sum(axis=1)
    pivot_42 = hist_totals.pivot(index="store_id", columns="item_id", values="total_42d").loc[STORES, chosen_items]

    fig, ax = plt.subplots(figsize=(9, 5))
    pivot_42.plot(kind="bar", ax=ax, width=0.72)
    ax.set_title("EDA 02: Tổng doanh số 42 ngày lịch sử theo cửa hàng và sản phẩm", fontsize=11.5, fontweight="bold")
    ax.set_xlabel("Cửa hàng")
    ax.set_ylabel("Tổng doanh số 42 ngày (đơn vị)")
    ax.tick_params(axis="x", rotation=0)
    ax.grid(axis="y", alpha=0.3)
    for container in ax.containers:
        ax.bar_label(container, fmt="%.0f", fontsize=8, padding=2)
    ax.legend(title="Sản phẩm")
    fig.tight_layout()
    fig.savefig(RESULTS_DIR / "eda_02.png", dpi=150)
    plt.close(fig)

    # --- 5. Biểu đồ EDA 03: Chênh lệch nhu cầu 7 ngày dự báo giữa các cửa hàng ---
    pivot_f7 = forecast_df.pivot(index="item_id", columns="store_id", values="forecast_7d").loc[chosen_items, STORES]
    fig, ax = plt.subplots(figsize=(9, 5))
    pivot_f7.plot(kind="bar", ax=ax, width=0.72)
    ax.set_title("EDA 03: Mức chênh lệch nhu cầu dự báo 7 ngày giữa 4 cửa hàng", fontsize=11.5, fontweight="bold")
    ax.set_xlabel("Sản phẩm (SKU)")
    ax.set_ylabel("Dự báo nhu cầu 7 ngày (đơn vị)")
    ax.tick_params(axis="x", rotation=0)
    ax.grid(axis="y", alpha=0.3)
    for container in ax.containers:
        ax.bar_label(container, fmt="%.0f", fontsize=8, padding=2)
    ax.legend(title="Cửa hàng")
    fig.tight_layout()
    fig.savefig(RESULTS_DIR / "eda_03.png", dpi=150)
    plt.close(fig)

    # --- 6. Lưu báo cáo EDA Markdown để dễ trích dẫn vào báo cáo sơ khảo ---
    eda_lines = [
        "# Báo cáo Kiểm tra Dữ liệu & EDA (STEP 2)",
        "",
        f"- **Số chuỗi (`store × item`):** {n_rows}",
        f"- **Số ngày quan sát:** {n_days} (`{recent_days[0]} .. {recent_days[-1]}`)",
        f"  - Lịch sử (*History*): {N_HISTORY_DAYS} ngày (`{history_days[0]} .. {history_days[-1]}`)",
        f"  - Kiểm tra (*Test*): {N_TEST_DAYS} ngày (`{test_days[0]} .. {test_days[-1]}`)",
        f"- **Số giá trị thiếu (`NaN`):** {n_missing}",
        f"- **Số giá trị âm (`< 0`):** {n_negative}",
        f"- **Số ngày doanh số `= 0`:** {n_zeros} / {sales_values.size} ({zero_pct:.2f}%) *(Giữ nguyên, không xóa)*",
        "",
        "## So sánh sai số dự báo 7 ngày trên tập test *(chỉ tham khảo EDA)*",
        f"- **MAE Trung bình 7 ngày lịch sử cuối (dùng cho MVP):** `{mae_ma7:.2f} đơn vị`",
        f"- **MAE Đối chứng 7 ngày tuần liền trước đó (`lag 2w`):** `{mae_snaive:.2f} đơn vị`",
        "",
        "## Bảng tổng hợp Dự báo 7 ngày vs Thực tế 7 ngày",
        "",
        "```text",
        merged_eval.to_string(index=False),
        "```",
    ]
    (RESULTS_DIR / "eda_report.md").write_text("\n".join(eda_lines) + "\n", encoding="utf-8")

    print(f"[STEP 2 OK] Đã lưu demand_forecast.csv, demand_actual_test.csv và 3 biểu đồ eda_01..03.png.")
    print(f"            Kiểm tra chất lượng: NaN={n_missing}, âm={n_negative}, bằng 0={n_zeros} ({zero_pct:.2f}%).")
    return forecast_df, actual_df


def step3_create_scenarios(
    forecast_df: pd.DataFrame,
    chosen_items: List[str],
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """STEP 3: Sinh tồn kho đầu kỳ, sức chứa, ma trận chi phí và 3 kịch bản nhu cầu."""
    # --- 1. Tồn kho đầu kỳ, ngưỡng an toàn, sức chứa (CHỈ từ forecast_7d) ---
    inv_rows = []
    for _, row in forecast_df.iterrows():
        item_id = row["item_id"]
        store_id = row["store_id"]
        f7 = float(row["forecast_7d"])

        init_inv = int(round(INITIAL_INV_RATIO[store_id] * f7))
        safety_target = int(round(SAFETY_TARGET_RATIO * f7))
        max_surplus = max(0, init_inv - safety_target)
        capacity = max(int(math.ceil(CAPACITY_RATIO * f7)), init_inv)

        inv_rows.append(
            {
                "item_id": item_id,
                "store_id": store_id,
                "forecast_7d": round(f7, 4),
                "initial_inventory": init_inv,
                "safety_target": safety_target,
                "max_surplus_send": max_surplus,
                "capacity": capacity,
            }
        )
    inv_df = pd.DataFrame(inv_rows)
    inv_df.to_csv(DATA_DIR / "inventory_scenario.csv", index=False)

    # --- 2. Ma trận chi phí điều chuyển đối xứng, đường chéo = 0 ---
    cost_rows = []
    for s_from in STORES:
        for s_to in STORES:
            if s_from == s_to:
                c = 0.0
            else:
                pair = (s_from, s_to) if (s_from, s_to) in TRANSFER_COST_MATRIX else (s_to, s_from)
                c = float(TRANSFER_COST_MATRIX[pair])
            cost_rows.append({"from_store": s_from, "to_store": s_to, "unit_cost_usd": c})
    cost_df = pd.DataFrame(cost_rows)
    cost_df.to_csv(DATA_DIR / "transfer_cost.csv", index=False)

    # --- 3. Định nghĩa 3 kịch bản (hệ số tăng chỉ áp dụng cho 1 cửa hàng & 1 sản phẩm) ---
    target_store = "CA_1"
    target_item = chosen_items[0]  # Sản phẩm doanh số lớn nhất trong 3 SKU được chọn
    scenarios_rows = [
        {
            "scenario": "NORMAL",
            "item_id": "ALL",
            "store_id": "ALL",
            "multiplier": 1.0,
            "description": "Nhu cầu gốc theo dữ liệu M5 (không có sốc cầu).",
        },
        {
            "scenario": "FLASH_SALE",
            "item_id": target_item,
            "store_id": target_store,
            "multiplier": 1.3,
            "description": f"Tăng +30% nhu cầu cục bộ tại {target_store} cho sản phẩm {target_item}.",
        },
        {
            "scenario": "SURGE",
            "item_id": target_item,
            "store_id": target_store,
            "multiplier": 1.5,
            "description": f"Tăng +50% nhu cầu đột biến cục bộ tại {target_store} cho sản phẩm {target_item}.",
        },
    ]
    scenarios_df = pd.DataFrame(scenarios_rows)
    scenarios_df.to_csv(DATA_DIR / "scenarios.csv", index=False)

    print("[STEP 3 OK] Đã lưu inventory_scenario.csv, transfer_cost.csv và scenarios.csv.")
    return inv_df, cost_df, scenarios_df


def main() -> int:
    selected, chosen_items, recent_days = step1_select_m5_data()
    forecast_df, _ = step2_eda_and_forecast(selected, chosen_items, recent_days)
    step3_create_scenarios(forecast_df, chosen_items)
    print("\n[DONE] Hoàn tất chuẩn bị dữ liệu STEP 1–3. Bước tiếp theo: py src/run_experiments.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
