from datetime import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class StockPredictionRequest(BaseModel):
    bahan: str = Field(..., example="baso_aci_original", description="Kode nama bahan baku utama")
    stok_saat_ini_pcs: float = Field(..., ge=0, example=24, description="Sisa stok bahan saat ini (pcs)")
    rata_rata_pemakaian_per_pesanan: float = Field(
        default=3.0,
        gt=0,
        example=3.0,
        description="Rata-rata pemakaian bahan (pcs) per 1 pesanan menu",
    )
    stok_awal_pcs: Optional[float] = Field(
        default=None,
        ge=0,
        example=120,
        description="Stok awal harian (opsional)",
    )
    jam: int = Field(
        default_factory=lambda: datetime.now().hour,
        ge=0,
        le=23,
        example=19,
        description="Jam operasional transaksi (0-23)",
    )
    is_weekend: int = Field(
        default_factory=lambda: 1 if datetime.now().weekday() >= 5 else 0,
        ge=0,
        le=1,
        example=0,
        description="1 jika Sabtu/Minggu, 0 jika hari kerja",
    )


class StockPredictionResponse(BaseModel):
    bahan: str
    nama_tampil: str
    stok_saat_ini_pcs: float
    estimasi_sisa_pesanan: int
    status: Literal["SAFE", "WARNING", "CRITICAL", "OUT_OF_STOCK"]
    pesan_peringatan: str
    trigger_gemini_recommendation: bool
    is_fallback: bool = False


class BatchStockPredictionRequest(BaseModel):
    items: List[StockPredictionRequest]


class BatchStockPredictionResponse(BaseModel):
    total_items: int
    critical_count: int
    predictions: List[StockPredictionResponse]