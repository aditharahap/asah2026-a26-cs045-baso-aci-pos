"""
Generator dummy data transaksi + simulasi stok - Kedai Baso Aci Classic Cileungsi
Tim Doa Mamah (A26-CS045)

SEMUA angka di blok ASUMSI adalah asumsi tim, BUKAN data asli kedai.
Yang dari owner: daftar menu + harga, resep per porsi, stok awal.
Yang dari Google Popular Times: jam buka dan bentuk pola keramaian (dibaca visual, relatif).
"""
import numpy as np
import pandas as pd
from datetime import date, datetime, timedelta

# ============================ ASUMSI ============================
SEED = 42
END_DATE = date(2026, 11, 10)
N_DAYS = 92                       # +- 3 bulan terakhir
MEAN_ORDERS_PER_DAY = 55          # asumsi tim
DAY_NOISE_SD = 7

# faktor volume per hari (Google: weekday & weekend hampir rata, Kamis-Sabtu sedikit di atas)
DAY_FACTOR = {0: 0.90, 1: 0.90, 2: 0.95, 3: 1.05, 4: 1.10, 5: 1.15, 6: 1.00}  # 0=Senin

# jam buka (Google). Minggu mulai 12.30, Sabtu tutup 23.00
HOURS = {d: list(range(10, 22)) for d in range(5)}
HOURS[5] = list(range(10, 23))
HOURS[6] = list(range(12, 22))

# profil keramaian per jam (dibaca dari Popular Times, skala relatif, puncak ~19-21)
BASE_HOUR = {10: .15, 11: .20, 12: .30, 13: .33, 14: .38, 15: .42, 16: .50,
             17: .60, 18: .75, 19: .90, 20: 1.0, 21: .80, 22: .50}
# penyesuaian profil per hari
HOUR_ADJ = {
    0: {21: .90}, 1: {21: .90}, 2: {20: .95},
    3: {20: 1.05, 21: .95}, 4: {20: 1.05, 21: 1.0},
    5: {21: 1.0, 22: .9}, 6: {19: 1.0, 20: 1.05, 21: .85},
}

CHANNELS = ["dine-in", "takeaway", "online"]
CHANNEL_P = [0.50, 0.25, 0.25]

# resep per porsi Baso Aci Komplit (dari owner), split 8 pcs = 3-3-2 diacak (asumsi tim)
SPLIT_BASO = [3, 3, 2]
CUANGKI_LIDAH_PER_PORSI, CUANGKI_TAHU_PER_PORSI, TIKTUK_PER_PORSI = 2, 2, 1

# stok awal (pcs)
STOK_AWAL = {"baso_aci_original_pcs": 1000, "baso_aci_ayam_pcs": 1000, "baso_aci_keju_pcs": 1000,
             "cuangki_lidah_pcs": 4200, "cuangki_tahu_pcs": 1000, "tiktuk_cikur_pcs": 500}
RESTOCK_THRESHOLD = 0.15   # asumsi tim
RESTOCK_MISS_P = 0.35      # peluang restock telat per kejadian restock (asumsi tim)

# ============================ MENU ============================
# (nama, kategori, harga, bobot_pilih)
MAIN = [
    ("Baso Aci Komplit", "Menu Utama", 17000, 35), ("Baso Rangu Komplit", "Menu Utama", 17000, 4),
    ("Baso Urat Komplit", "Menu Utama", 17000, 4), ("Baso Rangu Dan Urat", "Menu Utama", 17000, 3),
    ("Baso Campur", "Menu Utama", 18000, 4), ("Baso Full Rangu", "Menu Utama", 20000, 2),
    ("Baso Full Urat", "Menu Utama", 20000, 2), ("Paket Lengkap", "Menu Utama", 20000, 3),
    ("Bihun Komplit", "Menu Utama", 18000, 2), ("Pangsit Kuah", "Menu Utama", 17000, 2),
    ("Cireng Kuah", "Menu Utama", 16000, 2), ("Baso Tahu Kuah", "Menu Utama", 17000, 2),
    ("Ramen Classic", "Menu Utama", 17000, 2), ("Indomie Soto / Ayam Bawang", "Menu Utama", 8000, 3),
    ("Indomie Goreng", "Menu Utama", 9000, 3), ("Mie Tek Tek Kuah / Goreng", "Menu Utama", 16000, 3),
    ("Seblak Original", "Seblak", 15000, 3), ("Seblak Baso", "Seblak", 18000, 3),
    ("Seblak Cireng", "Seblak", 18000, 2), ("Seblak Ceker", "Seblak", 18000, 2),
    ("Seblak Tulang", "Seblak", 18000, 2), ("Seblak Batagor", "Seblak", 18000, 2),
    ("Seblak Seafood", "Seblak", 20000, 2), ("Seblak Campur", "Seblak", 25000, 2),
    ("Nasi Goreng Classic", "Paket Nasi", 16000, 3), ("Nasi Ayam Penyet / Goreng", "Paket Nasi", 23000, 4),
    ("Nasi Cumi Asin", "Paket Nasi", 22000, 2), ("Nasi Peda Asin", "Paket Nasi", 22000, 2),
    ("Ayam Goreng (tanpa nasi)", "Paket Nasi", 15000, 2),
    ("Pecak Pindang", "Menu Baru", 15000, 2), ("Nasi Komplit Pindang Goreng", "Menu Baru", 23000, 2),
    ("Chicken Wings (Isi 6 potong)", "Menu Baru", 23000, 2),
]
SNACK = [
    ("Tahu Cirawit", 16000), ("Kentang Goreng", 15000), ("Cimol Mozarella", 15000), ("Tahu Walik", 16000),
    ("Pangsit Goreng", 17000), ("Sosis Goreng", 16000), ("Cireng Goreng", 16000), ("Basreng Chili Oil", 16000),
    ("Basreng Cobek", 16000), ("Siomay Goreng", 16000), ("Mix Platter", 25000), ("Pempek", 16000),
    ("Pisang Brown Sugar", 18000), ("Pisang Bakar Coklat Keju", 18000),
]
DRINK = [  # nama, harga, bobot
    ("Mineral", 5000, 8), ("Teh Tawar Panas / Es", 4000, 6), ("Teh Manis Panas / Es", 6000, 25),
    ("Lemon Tea", 10000, 7), ("Es Jelly", 12000, 4), ("Jeruk Peras Panas / Es", 12000, 6),
    ("Teh Tarik Panas / Es", 10000, 5), ("Good Day Freeze", 9000, 3), ("Good Day Mocacinno Panas / Es", 7000, 3),
    ("Good Day Cappucinno Panas / Es", 8000, 3), ("Milo Panas / Es", 8000, 4), ("Red Velvet Milkshake", 14000, 3),
    ("Taro Milkshake", 14000, 3), ("Greentea Milkshake", 14000, 3), ("Teh Jus", 4000, 4), ("Nutrisari", 7000, 3),
    ("Jasjus Anggur", 5000, 2), ("Kukubima / Extrajoss", 7000, 2), ("Kukubima / Extrajoss Susu", 9000, 1),
    ("Kopi Kapal Api / ABC / Oplet", 5000, 4), ("Pop Ice", 6000, 3),
]
# topping: nama, harga, bobot, kolom stok yang dipotong (1 qty = 1 pcs, asumsi tim; Gajih = original)
TOPPING = [
    ("Baso Aci Ayam", 2000, 8, "baso_aci_ayam_pcs"), ("Baso Aci Gajih", 2000, 6, "baso_aci_original_pcs"),
    ("Baso Aci Keju", 2000, 8, "baso_aci_keju_pcs"), ("Cuangki Lidah", 1500, 6, "cuangki_lidah_pcs"),
    ("Cuangki Tahu", 1500, 5, "cuangki_tahu_pcs"), ("Tiktuk Cikur", 1500, 5, "tiktuk_cikur_pcs"),
    ("Baso Rangu", 2500, 4, None), ("Baso Urat", 2500, 4, None), ("Baso Urat Besar", 6000, 2, None),
    ("Dumpling Keju / Ayam", 4000, 2, None), ("Chikuwa", 4000, 2, None), ("Batagor Mini", 4000, 2, None),
    ("Telur Rebus", 5000, 3, None), ("Telur Ceplok", 6000, 3, None), ("Telur Dadar", 7000, 3, None),
    ("Jamur Enoki", 5000, 2, None), ("Mie Telur", 3000, 3, None), ("Mie Gelas", 3000, 2, None),
    ("Bihun", 5000, 2, None), ("Ceker", 2000, 3, None), ("Tulang", 4000, 2, None), ("Cireng", 2000, 3, None),
    ("Sosis Besar", 5000, 2, None), ("Tetelan", 5000, 3, None),
]
PROMO_TEH = {"Pecak Pindang", "Nasi Komplit Pindang Goreng"}
STOCK_COLS = list(STOK_AWAL.keys())

rng = np.random.default_rng(SEED)


def pick(items, weights):
    w = np.array(weights, dtype=float)
    return items[rng.choice(len(items), p=w / w.sum())]


HARI_ID = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
# metode bayar per pesanan (bobot karangan, asumsi tim)
PAY = {"dine-in": (["Tunai", "QRIS", "Transfer"], [0.45, 0.45, 0.10]),
       "takeaway": (["Tunai", "QRIS", "Transfer"], [0.40, 0.50, 0.10]),
       "online": (["E-Wallet", "QRIS"], [0.70, 0.30])}


def make_row(order_id, ts, channel, nama, kategori, qty, harga, stok=None, diskon=0):
    row = {"order_id": order_id, "timestamp": ts, "tanggal": ts.date(), "hari": HARI_ID[ts.weekday()],
           "is_weekend": int(ts.weekday() >= 5), "jam": ts.hour,
           "menu": nama, "kategori": kategori, "qty": qty, "harga_satuan": harga,
           "diskon": diskon, "subtotal": qty * harga - diskon, "channel": channel}
    for c in STOCK_COLS:
        row[c] = 0
    if stok:
        for k, v in stok.items():
            row[k] += v
    return row


def baso_komplit_usage(qty):
    u = {"cuangki_lidah_pcs": 0, "cuangki_tahu_pcs": 0, "tiktuk_cikur_pcs": 0,
         "baso_aci_original_pcs": 0, "baso_aci_ayam_pcs": 0, "baso_aci_keju_pcs": 0}
    for _ in range(qty):
        split = rng.permutation(SPLIT_BASO)
        for col, n in zip(["baso_aci_original_pcs", "baso_aci_ayam_pcs", "baso_aci_keju_pcs"], split):
            u[col] += int(n)
        u["cuangki_lidah_pcs"] += CUANGKI_LIDAH_PER_PORSI
        u["cuangki_tahu_pcs"] += CUANGKI_TAHU_PER_PORSI
        u["tiktuk_cikur_pcs"] += TIKTUK_PER_PORSI
    return u


def gen_order(order_id, ts):
    ch = rng.choice(CHANNELS, p=CHANNEL_P)
    rows = []
    n_main = 1 if rng.random() < 0.88 else 2
    used = set()
    promo = False
    for _ in range(n_main):
        while True:
            m = pick(MAIN, [x[3] for x in MAIN])
            if m[0] not in used:
                used.add(m[0])
                break
        qty = 1 if rng.random() < 0.9 else 2
        stok = baso_komplit_usage(qty) if m[0] == "Baso Aci Komplit" else None
        rows.append(make_row(order_id, ts, ch, m[0], m[1], qty, m[2], stok))
        if m[0] in PROMO_TEH:
            promo = True
    if promo:
        rows.append(make_row(order_id, ts, ch, "Teh Manis Panas / Es", "Minuman", 1, 6000, diskon=6000))
    elif rng.random() < 0.55:
        d = pick(DRINK, [x[2] for x in DRINK])
        rows.append(make_row(order_id, ts, ch, d[0], "Minuman", 1, d[1]))
    if rng.random() < 0.25:
        for _ in range(int(rng.choice([1, 2], p=[0.8, 0.2]))):
            t = pick(TOPPING, [x[2] for x in TOPPING])
            q = int(rng.choice([1, 2, 3], p=[0.6, 0.25, 0.15]))
            rows.append(make_row(order_id, ts, ch, f"Topping {t[0]}", "Topping", q, t[1],
                                 {t[3]: q} if t[3] else None))
    if rng.random() < 0.10:
        s = SNACK[rng.integers(len(SNACK))]
        rows.append(make_row(order_id, ts, ch, s[0], "Camilan", 1, s[1]))
    return rows


def gen_transactions():
    rows, order_id = [], 1000
    start = END_DATE - timedelta(days=N_DAYS - 1)
    for i in range(N_DAYS):
        d = start + timedelta(days=i)
        wd = d.weekday()
        n = max(25, int(round(rng.normal(MEAN_ORDERS_PER_DAY * DAY_FACTOR[wd], DAY_NOISE_SD))))
        hours = HOURS[wd]
        w = np.array([BASE_HOUR[h] * HOUR_ADJ[wd].get(h, 1.0) * (0.5 if (wd == 6 and h == 12) else 1.0)
                      for h in hours])
        chosen = rng.choice(hours, size=n, p=w / w.sum())
        stamps = []
        for h in chosen:
            lo = 30 if (wd == 6 and h == 12) else 0
            stamps.append(datetime(d.year, d.month, d.day, int(h), int(rng.integers(lo, 60)), int(rng.integers(0, 60))))
        for ts in sorted(stamps):
            order_id += 1
            new = gen_order(order_id, ts)
            opts, p = PAY[new[0]["channel"]]
            metode = str(rng.choice(opts, p=p))
            for r in new:
                r["metode_bayar"] = metode
            rows.extend(new)
    df = pd.DataFrame(rows)
    front = ["order_id", "timestamp", "tanggal", "hari", "is_weekend", "jam", "menu", "kategori", "qty",
             "harga_satuan", "diskon", "subtotal", "channel", "metode_bayar"]
    return df[front + STOCK_COLS]


def simulate_stock(df):
    daily = df.assign(tanggal=df["timestamp"].dt.date).groupby("tanggal")[STOCK_COLS].sum()
    stok = dict(STOK_AWAL)
    pending = {c: None for c in STOCK_COLS}   # sisa hari sampai restock datang
    out = []
    for tgl, use in daily.iterrows():
        for c in STOCK_COLS:
            awal = stok[c]
            restock = 0
            if pending[c] is not None:
                pending[c] -= 1
                if pending[c] <= 0:
                    restock = STOK_AWAL[c] - awal
                    awal = STOK_AWAL[c]
                    pending[c] = None
            pakai = int(use[c])
            akhir = awal - pakai
            kurang = max(0, -akhir)
            akhir = max(0, akhir)
            if pending[c] is None and akhir < RESTOCK_THRESHOLD * STOK_AWAL[c]:
                # normal: datang besok; terlewat: telat 3-6 hari (asumsi tim)
                pending[c] = int(rng.integers(3, 7)) if rng.random() < RESTOCK_MISS_P else 1
            out.append({"tanggal": tgl, "hari": HARI_ID[tgl.weekday()], "is_weekend": int(tgl.weekday() >= 5),
                        "bahan": c.replace("_pcs", ""), "stok_awal_hari": awal + 0,
                        "restock_masuk": int(restock), "pemakaian": pakai, "stok_akhir_hari": int(akhir),
                        "stok_habis": int(kurang > 0), "kekurangan_pcs": int(kurang)})
            stok[c] = akhir
    return pd.DataFrame(out)


if __name__ == "__main__":
    trx = gen_transactions()
    stk = simulate_stock(trx)
    trx.to_csv("data/transaksi.csv", index=False)
    stk.to_csv("data/stok_harian.csv", index=False)
    print("transaksi.csv :", trx.shape, "| pesanan:", trx["order_id"].nunique())
    print("stok_harian.csv:", stk.shape)
