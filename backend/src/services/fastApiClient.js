import axios from "axios";

const FASTAPI_BASE_URL = process.env.FASTAPI_URL || "http://localhost:8000";

function ruleBasedFallback(payload) {
  const { bahan, stok_saat_ini_pcs, rata_rata_pemakaian_per_pesanan } = payload;
  const estOrders =
    stok_saat_ini_pcs === 0
      ? 0
      : Math.max(0, Math.round(stok_saat_ini_pcs / Math.max(rata_rata_pemakaian_per_pesanan, 0.25)));

  let status = "SAFE";
  if (estOrders === 0) status = "OUT_OF_STOCK";
  else if (estOrders <= 2) status = "CRITICAL";
  else if (estOrders <= 5) status = "WARNING";

  return {
    bahan,
    nama_tampil: bahan.replace(/_/g, " ").toUpperCase(),
    stok_saat_ini_pcs,
    estimasi_sisa_pesanan: estOrders,
    status,
    pesan_peringatan: `[Mode Cadangan] Perkiraan sisa ${estOrders} pesanan lagi.`,
    trigger_gemini_recommendation: estOrders <= 5,
    is_fallback: true,
  };
}

export async function predictStockEarlyWarning(payload) {
  try {
    const { data } = await axios.post(`${FASTAPI_BASE_URL}/api/v1/predict-stock`, payload, {
      timeout: 3000, // Maksimal tunggu 3 detik agar transaksi kasir tidak terhambat
    });
    return { ...data, is_fallback: false };
  } catch (error) {
    console.warn(`[FastAPI Fallback Active] ${error.message}`);
    return ruleBasedFallback(payload);
  }
}