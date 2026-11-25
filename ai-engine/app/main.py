import os
from typing import Literal
import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(
    title="Doa Mamah - Stock Early Warning API",
    description="API Prediksi Sisa Pesanan Bahan Utama - Kedai Baso Aci Classic Cileungsi",
    version="1.0.0",
)

MODEL_PATH = os.getenv("MODEL_PATH", "models/stock_early_warning_model.joblib")
model = joblib.load(MODEL_PATH)

STOK_KAPASITAS = {
    "baso_aci_original": 1000,
    "baso_aci_ayam": 1000,
    "baso_aci_keju": 1000,
    "cuangki_lidah": 4200,
    "cuangki_tahu": 1000,
    "tiktuk_cikur": 500,
}

LABEL_BAHAN = {
    "baso_aci_original": "Baso Aci Original",
    "baso_aci_ayam": "Baso Aci Ayam",
    "baso_aci_keju": "Baso Aci Keju",
    "cuangki_lidah": "Cuangki Lidah",
    "cuangki_tahu": "Cuangki Tahu",
    "tiktuk_cikur": "Tiktuk Cikur",
}


class StockPredictRequest(BaseModel):
    bahan: Literal[
        "baso_aci_original",
        "baso_aci_ayam",
        "baso_aci_keju",
        "cuangki_lidah",
        "cuangki_tahu",
        "tiktuk_cikur",
    ] = Field(..., example="baso_aci_ayam")
    stok_saat_ini_pcs: int = Field(..., ge=0, example=6)
    pemakaian_1_jam_terakhir: int = Field(..., ge=0, example=15)
    pesanan_1_jam_terakhir: int = Field(..., ge=0, example=8)
    rata_rata_pemakaian_per_pesanan: float = Field(..., gt=0, example=1.15)
    jam: int = Field(..., ge=0, le=23, example=19)
    is_weekend: int = Field(..., ge=0, le=1, example=1)


class StockPredictResponse(BaseModel):
    bahan: str
    nama_tampil: str
    stok_saat_ini_pcs: int
    estimasi_sisa_pesanan: int
    status: Literal["SAFE", "WARNING", "CRITICAL", "OUT_OF_STOCK"]
    pesan_peringatan: str
    trigger_gemini_recommendation: bool


@app.get("/health")
def health_check():
    return {"status": "healthy", "model_ready": model is not None}


@app.post("/api/v1/predict-stock", response_model=StockPredictResponse)
def predict_stock(req: StockPredictRequest):
    nama_tampil = LABEL_BAHAN[req.bahan]

    if req.stok_saat_ini_pcs == 0:
        return StockPredictResponse(
            bahan=req.bahan,
            nama_tampil=nama_tampil,
            stok_saat_ini_pcs=0,
            estimasi_sisa_pesanan=0,
            status="OUT_OF_STOCK",
            pesan_peringatan=f"Stok {nama_tampil} HABIS (0 pcs). Menu terkait otomatis dinonaktifkan.",
            trigger_gemini_recommendation=True,
        )

    try:
        kapasitas = STOK_KAPASITAS[req.bahan]
        rasio_stok = round(req.stok_saat_ini_pcs / kapasitas, 4)
        est_runway = round(req.stok_saat_ini_pcs / max(req.rata_rata_pemakaian_per_pesanan, 0.05), 4)

        features = pd.DataFrame([{
            "stok_saat_ini_pcs": req.stok_saat_ini_pcs,
            "rasio_stok": rasio_stok,
            "pemakaian_1_jam_terakhir": req.pemakaian_1_jam_terakhir,
            "pesanan_1_jam_terakhir": req.pesanan_1_jam_terakhir,
            "rata_rata_pemakaian_per_pesanan": req.rata_rata_pemakaian_per_pesanan,
            "est_runway_orders": est_runway,
            "jam": req.jam,
            "is_weekend": req.is_weekend,
            "bahan": req.bahan,
        }])

        pred_raw = float(model.predict(features)[0])
        est_orders = max(0, int(round(pred_raw)))

        if est_orders <= 2:
            status = "CRITICAL"
            msg = f"KRITIS: {nama_tampil} diperkirakan habis dalam {est_orders} pesanan lagi!"
            trigger_ai = True
        elif est_orders <= 5:
            status = "WARNING"
            msg = f"PERINGATAN: {nama_tampil} menipis, perkiraan cukup untuk ±{est_orders} pesanan lagi."
            trigger_ai = True
        else:
            status = "SAFE"
            msg = f"Stok {nama_tampil} aman (±{est_orders} pesanan lagi)."
            trigger_ai = False

        return StockPredictResponse(
            bahan=req.bahan,
            nama_tampil=nama_tampil,
            stok_saat_ini_pcs=req.stok_saat_ini_pcs,
            estimasi_sisa_pesanan=est_orders,
            status=status,
            pesan_peringatan=msg,
            trigger_gemini_recommendation=trigger_ai,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Gagal menjalankan inferensi model: {str(exc)}")