from datetime import datetime
from typing import Any, Dict
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

CATEGORICAL_FEATURES = ["bahan"]
NUMERIC_FEATURES = [
    "stok_saat_ini_pcs",
    "rata_rata_pemakaian_per_pesanan",
    "stok_awal_pcs",
    "rasio_sisa_stok",
    "jam",
    "is_weekend",
]
ALL_FEATURES = CATEGORICAL_FEATURES + NUMERIC_FEATURES


def build_preprocessor() -> ColumnTransformer:
    """Membangun pipeline preprocessing untuk fitur kategorikal dan numerik."""
    numeric_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )

    categorical_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )

    return ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, NUMERIC_FEATURES),
            ("cat", categorical_transformer, CATEGORICAL_FEATURES),
        ]
    )


def prepare_inference_df(payload: Dict[str, Any]) -> pd.DataFrame:
    """Mengubah payload JSON dari FastAPI menjadi DataFrame siap prediksi."""
    now = datetime.now()
    stok_saat_ini = float(payload.get("stok_saat_ini_pcs", 0))
    stok_awal = float(payload.get("stok_awal_pcs") or max(stok_saat_ini, 1.0))
    rata_pemakaian = max(float(payload.get("rata_rata_pemakaian_per_pesanan", 1.0)), 0.1)
    jam = int(payload.get("jam", now.hour))
    is_weekend = int(payload.get("is_weekend", 1 if now.weekday() >= 5 else 0))
    rasio_sisa = min(stok_saat_ini / max(stok_awal, 1.0), 1.0)

    row = {
        "bahan": str(payload["bahan"]).strip().lower(),
        "stok_saat_ini_pcs": stok_saat_ini,
        "rata_rata_pemakaian_per_pesanan": rata_pemakaian,
        "stok_awal_pcs": stok_awal,
        "rasio_sisa_stok": rasio_sisa,
        "jam": jam,
        "is_weekend": is_weekend,
    }
    return pd.DataFrame([row], columns=ALL_FEATURES)