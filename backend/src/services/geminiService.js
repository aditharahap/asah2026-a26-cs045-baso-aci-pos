import { GoogleGenAI } from "@google/genai";

const ai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY });

const STATIC_FALLBACK_MENU = {
  baso_aci_ayam: "Sarankan pelanggan beralih ke Baso Rangu Komplit atau Baso Urat Komplit (Rp17.000).",
  baso_aci_keju: "Sarankan pelanggan memilih Baso Rangu Komplit atau Seblak Baso (Rp17.000–Rp18.000).",
  baso_aci_original: "Sarankan pelanggan memilih Paket Lengkap atau Mie Tek Tek Kuah (Rp16.000–Rp20.000).",
  cuangki_lidah: "Tawarkan penggantian topping ke Batagor Mini atau Siomay Goreng sebagai pelengkap.",
  cuangki_tahu: "Tawarkan penggantian topping ke Tahu Walik atau Pangsit Goreng.",
  tiktuk_cikur: "Informasikan stok Tiktuk Cikur menipis; tawarkan tambahan porsi Baso Urat atau Ceker.",
};

export async function generateMenuRecommendation({ bahan, namaTampil, estimasiSisaPesanan }) {
  const prompt = `
Anda adalah asisten operasional kasir Kedai Baso Aci Classic Cileungsi.
Kondisi saat ini: Bahan "${namaTampil}" diperkirakan habis dalam ${estimasiSisaPesanan} pesanan lagi.
Menu alternatif yang tersedia: Baso Rangu Komplit (Rp17.000), Baso Urat Komplit (Rp17.000), Baso Campur (Rp18.000), Seblak Baso (Rp18.000), Mie Tek Tek Kuah (Rp16.000), serta topping Batagor Mini, Chikuwa, dan Tahu Walik.

Tugas: Buat 1 kalimat singkat, sopan, dan persuasif (maksimal 25 kata) yang dapat langsung dibacakan staf kasir kepada pelanggan untuk menawarkan menu pengganti yang setara. Jangan gunakan format markdown.
  `.trim();

  try {
    const response = await ai.models.generateContent({
      model: "gemini-2.5-flash",
      contents: prompt,
    });

    const text = response?.text?.trim();
    if (!text) throw new Error("Respons Gemini kosong");

    return {
      source: "gemini-api",
      recommendation: text,
      isFallback: false,
    };
  } catch (error) {
    console.error("[GeminiService Error]:", error.message);
    return {
      source: "static-fallback",
      recommendation:
        STATIC_FALLBACK_MENU[bahan] ||
        "Sarankan pelanggan mencoba menu favorit lain seperti Baso Rangu Komplit atau Seblak Baso.",
      isFallback: true,
      errorMessage: "Layanan AI sedang sibuk/mencapai batas kuota, menampilkan saran standar.",
    };
  }
}

export async function generateDailyStockSummary({ tanggal, ringkasanStok }) {
  // ringkasanStok: array [{ bahan, stok_awal, terpakai, sisa_stok, status }]
  const daftarStokText = ringkasanStok
    .map((item) => `- ${item.bahan}: awal ${item.stok_awal} pcs, terpakai ${item.terpakai} pcs, sisa ${item.sisa_stok} pcs (${item.status})`)
    .join("\n");

  const prompt = `
Anda adalah asisten manajer operasional Kedai Baso Aci Classic Cileungsi.
Berikut laporan pemakaian bahan utama tanggal ${tanggal}:
${daftarStokText}

Tugas: Buat ringkasan evaluasi stok harian dalam 2-3 kalimat singkat untuk pemilik kedai (Ibu Intan). Sebutkan bahan yang paling cepat habis dan bahan mana yang harus segera di-restock besok pagi. Gunakan bahasa Indonesia yang jelas dan lugas.
  `.trim();

  try {
    const response = await ai.models.generateContent({
      model: "gemini-2.5-flash",
      contents: prompt,
    });

    const text = response?.text?.trim();
    if (!text) throw new Error("Respons ringkasan Gemini kosong");

    return {
      source: "gemini-api",
      summary: text,
      isFallback: false,
    };
  } catch (error) {
    console.error("[Gemini Daily Summary Error]:", error.message);
    const menipis = ringkasanStok
      .filter((i) => i.status !== "SAFE")
      .map((i) => i.bahan)
      .join(", ");

    return {
      source: "static-fallback",
      summary: menipis
        ? `Perhatian restock besok pagi: stok ${menipis} berada dalam status menipis/kritis berdasarkan pemakaian hari ini.`
        : "Seluruh stok bahan utama hari ini dalam kondisi aman dan mencukupi untuk operasional awal besok.",
      isFallback: true,
    };
  }
}