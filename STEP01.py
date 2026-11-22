import pandas as pd
raw = pd.read_csv("data/raw/sales_train_validation.csv")
raw = raw[raw["store_id"].isin(["CA_1", "CA_2", "CA_3", "CA_4"])]
days = [c for c in raw.columns if c.startswith("d_")]
recent = days[-49:]
raw["last49_sum"] = raw[recent].sum(axis=1)
count_store = raw.groupby("item_id")["store_id"].nunique()
valid_ids = count_store[count_store == 4].index
candidates = raw[raw["item_id"].isin(valid_ids)]
scores = candidates.groupby("item_id")["last49_sum"].sum()
chosen = scores[scores > 0].sort_values(ascending=False).head(3).index
selected = candidates[candidates["item_id"].isin(chosen)]
selected[["item_id", "store_id"] + recent].to_csv(
    "data/m5_selected.csv", index=False)
print("Items:", list(chosen), "Rows:", len(selected))
