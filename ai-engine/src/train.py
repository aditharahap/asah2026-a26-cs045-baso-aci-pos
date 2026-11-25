import os
import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import GroupShuffleSplit
from sklearn.metrics import mean_absolute_error, root_mean_squared_error, r2_score

STOCK_COLS = [
    "baso_aci_original_pcs",
    "baso_aci_ayam_pcs",
    "baso_aci_keju_pcs",
    "cuangki_lidah_pcs",
    "cuangki_tahu_pcs",
    "tiktuk_cikur_pcs",
]

STOK_KAPASITAS = {
    "baso_aci_original": 1000,
    "baso_aci_ayam": 1000,
    "baso_aci_keju": 1000,
    "cuangki_lidah": 4200,
    "cuangki_tahu": 1000,
    "tiktuk_cikur": 500,
}

NUM_FEATURES = [
    "stok_saat_ini_pcs",
    "rasio_stok",
    "pemakaian_1_jam_terakhir",
    "pesanan_1_jam_terakhir",
    "rata_rata_pemakaian_per_pesanan",
    "est_runway_orders",
    "jam",
    "is_weekend",
]
CAT_FEATURES = ["bahan"]
TARGET = "sisa_pesanan_sebelum_habis"


def build_training_dataset(trx_path: str, stk_path: str) -> pd.DataFrame:
    trx = pd.read_csv(trx_path)
    stk = pd.read_csv(stk_path)

    trx["timestamp"] = pd.to_datetime(trx["timestamp"])
    trx["tanggal"] = pd.to_datetime(trx["tanggal"]).dt.date
    stk["tanggal"] = pd.to_datetime(stk["tanggal"]).dt.date

    orders = (
        trx.groupby(["order_id", "timestamp", "tanggal", "is_weekend", "jam"], as_index=False)
        .agg({c: "sum" for c in STOCK_COLS})
        .sort_values("timestamp")
        .reset_index(drop=True)
    )

    order_times = orders["timestamp"].values
    orders["pesanan_1_jam_terakhir"] = [
        idx - int(np.searchsorted(order_times, t - np.timedelta64(60, "m"), side="left")) + 1
        for idx, t in enumerate(order_times)
    ]

    restock_lookup = stk.set_index(["tanggal", "bahan"])["restock_masuk"].to_dict()
    records = []

    for col in STOCK_COLS:
        bahan = col.replace("_pcs", "")
        kapasitas = STOK_KAPASITAS[bahan]
        stok_now = kapasitas
        current_day = None
        cycle_num = 1

        bahan_history = []
        usage_arr = orders[col].values
        global_mean_usage = float(usage_arr.mean())

        for idx in range(len(orders)):
            row_date = orders.loc[idx, "tanggal"]
            if row_date != current_day:
                current_day = row_date
                if restock_lookup.get((current_day, bahan), 0) > 0:
                    stok_now = kapasitas
                    cycle_num += 1

            stok_now = max(0, stok_now - int(usage_arr[idx]))

            t = order_times[idx]
            left = int(np.searchsorted(order_times, t - np.timedelta64(60, "m"), side="left"))
            u60 = int(usage_arr[left : idx + 1].sum())
            p60 = int(orders.loc[idx, "pesanan_1_jam_terakhir"])

            win_start = max(0, idx - 29)
            r_avg = float(0.7 * usage_arr[win_start : idx + 1].mean() + 0.3 * global_mean_usage)
            est_runway = stok_now / max(r_avg, 0.05)

            bahan_history.append({
                "cycle_id": f"{bahan}_c{cycle_num}",
                "bahan": bahan,
                "jam": int(orders.loc[idx, "jam"]),
                "is_weekend": int(orders.loc[idx, "is_weekend"]),
                "stok_saat_ini_pcs": stok_now,
                "rasio_stok": round(stok_now / kapasitas, 4),
                "pemakaian_1_jam_terakhir": u60,
                "pesanan_1_jam_terakhir": p60,
                "rata_rata_pemakaian_per_pesanan": round(r_avg, 4),
                "est_runway_orders": round(est_runway, 4),
            })

        for i in range(len(bahan_history)):
            s_now = bahan_history[i]["stok_saat_ini_pcs"]
            if s_now == 0:
                rem_orders = 0
            else:
                cum_future, steps, depleted = 0, 0, False
                for j in range(i + 1, len(orders)):
                    cum_future += int(usage_arr[j])
                    steps += 1
                    if cum_future >= s_now:
                        depleted = True
                        break
                rem_orders = steps if depleted else int(round(s_now / max(global_mean_usage, 0.05)))

            if rem_orders <= 80:
                bahan_history[i][TARGET] = rem_orders
                records.append(bahan_history[i])

    return pd.DataFrame(records)


def main():
    ml_df = build_training_dataset(
        trx_path="../../data-science/data/transaksi.csv",
        stk_path="../../data-science/data/stok_harian.csv",
    )

    gss = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=42)
    train_idx, test_idx = next(gss.split(ml_df, ml_df[TARGET], groups=ml_df["cycle_id"]))
    train_df, test_df = ml_df.iloc[train_idx], ml_df.iloc[test_idx]

    X_train, y_train = train_df[NUM_FEATURES + CAT_FEATURES], train_df[TARGET]
    X_test, y_test = test_df[NUM_FEATURES + CAT_FEATURES], test_df[TARGET]

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), NUM_FEATURES),
            ("cat", OneHotEncoder(handle_unknown="ignore"), CAT_FEATURES),
        ]
    )

    candidates = {
        "Ridge Regression": Ridge(alpha=1.0, random_state=42),
        "Random Forest Regressor": RandomForestRegressor(
            n_estimators=200, max_depth=8, min_samples_leaf=5, random_state=42, n_jobs=-1
        ),
        "Gradient Boosting Regressor": GradientBoostingRegressor(
            n_estimators=180, learning_rate=0.05, max_depth=3, min_samples_leaf=5, random_state=42
        ),
    }

    results = []
    best_pipe, best_mae, best_name = None, float("inf"), ""

    for name, reg in candidates.items():
        pipe = Pipeline([("prep", preprocessor), ("model", reg)])
        pipe.fit(X_train, y_train)
        preds = np.clip(pipe.predict(X_test), 0, None)

        mae = mean_absolute_error(y_test, preds)
        rmse = root_mean_squared_error(y_test, preds)
        r2 = r2_score(y_test, preds)
        results.append({"Model": name, "MAE": round(mae, 3), "RMSE": round(rmse, 3), "R2": round(r2, 4)})

        if mae < best_mae:
            best_mae, best_pipe, best_name = mae, pipe, name

    print(pd.DataFrame(results).sort_values("MAE").to_markdown(index=False))
    os.makedirs("../models", exist_ok=True)
    joblib.dump(best_pipe, "../models/stock_early_warning_model.joblib")
    print(f"Model terbaik ({best_name}) berhasil disimpan.")


if __name__ == "__main__":
    main()