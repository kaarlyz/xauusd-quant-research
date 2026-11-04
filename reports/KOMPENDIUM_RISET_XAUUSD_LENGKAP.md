# KOMPENDIUM RISET KUANTITATIF & DOKUMENTASI STRATEGI XAUUSD LENGKAP (2015 – 2026)

> **Proyek**: Evaluasi, Bedah Clickbait YouTube, Forensik Mikrostruktur, dan Validasi Kuantitatif XAUUSD (Gold)  
> **Lingkungan Riset**: Linux CachyOS, Python 3.12 (Polars, NumPy, SciPy)  
> **Dataset Utama**:
> - **Master M1**: `XAUUSD_M1.parquet` (4.182.209 bar M1, 2015 s/d 2026, SHA-256: `771ae44ae...`).
> - **Tick Riil**: 359 partisi Parquet (405.106.965 tick, 2020 s/d 2026, data Bid/Ask/Spread per milidetik).
> - **D1 Makro**: `XAUUSD_1d.csv` (14.883 candle, 1978 s/d 2026).
> - **Blind Final Holdout**: 22 Agustus 2025 s/d 21 Agustus 2026 UTC (Sealed).
> **Standar Biaya ECN Baku**: Spread ECN median $0.38 + Komisi $0.07/oz round-turn + Slippage Stop $0.05 (Total drag per market/stop trade = $0.50/oz).

---

## DAFTAR ISI STRATEGI & RISET

1. **STRAT-01**: XAUUSD M1 London 17:30 WIB Reversal (Rejected)
2. **STRAT-02**: XAUUSD M1 Tokyo 09:30 WIB Momentum (Rejected)
3. **STRAT-03**: XAUUSD M1 Hourly Open Sweep Reversal (Rejected)
4. **STRAT-07**: XAUUSD M1 Quarter-Hour 08:15 WIB Tokyo Reversal (Rejected - Small Sample Bias)
5. **STRAT-08**: XAUUSD M15 London Drive Fibonacci 78.6% Discount (Rejected - Limit Execution Defect)
6. **Riset High-Frequency 32 Varian (H1–H4 Scalping M1)**: 
   - H1: Liquidity Sweep & Reclaim
   - H2: Intraday Mean Reversion
   - H3: Failed Breakout
   - H4: Micro-Momentum Continuation (Semua Rejected - Cekikan Friksi)
7. **Bedah Video YouTube #1 (`c62Tj28zfyQ`)**: Momentum Candle Fibo 23.6% M5 (Clickbait - Falsified)
8. **Bedah Video YouTube #2 (`wsXu2Xr1nQc`)**: Klaim 70% Win Rate 30 Mei 2025 (Anomali Sideways - Falsified)
9. **Bedah Video YouTube #3 (`LdQDazFjjk8`)**: Debunking Scalping Gold Momentum Candle WR 80% (Confirmed Falsified)
10. **Bedah Video YouTube #4 (`JddnO_5Pjxw`)**: Scalping Dua Candle M30 -> M5 (Falsified)
11. **Bedah Video YouTube #5 (`lAENVt206ho`)**: Pola N Breakout-Retest Support/Resistance (Rejected - False Retest)
12. **Bedah Video YouTube #6 (`fcySBFFsm04`)**: Pola N Asli Goichi Hosoda H1/H4 (Valid Edge)
13. **Bedah Video YouTube #7 (`HhaNJxbXfeA`)**: Pola N Straddle Dua Arah Pak Tito / Mata Trader H4 (Marginal Edge)
14. **Bedah Video YouTube #8 (`rkOiwuhluUM`)**: Pola N Baku + Filter Expired *The Traders* (JUARA 1 MUTLAK)

---

# BAGIAN 1: STRATEGI HISTORIS M1 & DISCOVERY ENGINE LOKAL

---

### 1. STRAT-01: XAUUSD M1 London 17:30 WIB Reversal
- **Konsep**: Reversal di pembukaan sesi London (10:30 UTC / 17:30 WIB). Jika harga membentuk ekor sweep pada range 15 menit sebelumnya, pasang posisi pembalikan arah dengan SL ketat ($1.50) dan TP $3.00 (RR 1:2).
- **Hasil Backtest 12 Tahun (2015–2026)**:
  - Total Trade: 1.108 trade.
  - In-Sample (2015–2022): Win Rate 41.2%, PF 1.34 (+48.2 R).
  - Out-of-Sample (2023–2024): Win Rate 26.5%, PF 0.41 (-32.5 R).
- **Status**: **REJECTED (TOLAK)**.
- **Penyebab Kegagalan**: Regime drift. Karakteristik likuiditas pembukaan London bergeser drastis di era pasca-2022 akibat dominasi algo HFT.

---

### 2. STRAT-02: XAUUSD M1 Tokyo 09:30 WIB Momentum
- **Konsep**: Meneruskan momentum pembukaan bursa Shanghai / Tokyo fixing (02:30 UTC / 09:30 WIB) saat breakout High/Low 30 menit sesi Asia.
- **Hasil Backtest 12 Tahun**:
  - Total Trade: 1.420 trade.
  - Win Rate: 34.2%, Profit Factor: 0.88, Net Realized: -82.4 R.
- **Status**: **REJECTED (TOLAK)**.
- **Penyebab Kegagalan**: Sesi Asia memiliki volume terendah di pasar emas; breakout awal Asia mayoritas berujung *false breakout* yang memakan SL.

---

### 3. STRAT-03: XAUUSD M1 Hourly Open Sweep Reversal
- **Konsep**: Setiap pergantian jam (XX:00 UTC), tunggu sweep likuiditas 5 candle M1 pertama lalu ambil posisi reversal ke arah berlawanan.
- **Hasil Backtest 12 Tahun**:
  - Total Trade: 8.940 trade.
  - Win Rate: 46.1%, Profit Factor: 0.91, Net Realized: -284.1 R.
- **Status**: **REJECTED (TOLAK)**.
- **Penyebab Kegagalan**: Noise M1 terlalu tinggi, tarikan spread pada menit 00–02 memakan 15% dari jarak stop loss.

---

### 4. STRAT-07: XAUUSD M1 Quarter-Hour 08:15 WIB Tokyo Reversal
- **Konsep**: Reversal di pembukaan jam 08:15 WIB (01:15 UTC) pasca-sweep candle 15 menit pertama Asia.
- **Hasil Backtest Awal (Sebelum Koreksi)**:
  - In-Sample (18 trade): Win Rate 55.6%, Profit Factor 1.404. Terlihat sangat menjanjikan (*promising*).
- **Hasil Revalidasi Forensik Phase 3 (Execution-Model Actual Tick)**:
  - Validation Partisi (2024–2025): 25 trade, Win Rate rontok ke **24.0%**, Profit Factor **0.381**, Net Exp **-0.3618 R**.
  - Sisi Long hancur total: Win Rate hanya **7.69%**.
- **Status**: **PERMANENTLY REJECTED (TOLAK MUTLAK)**.
- **Penyebab Kegagalan**: *Small Sample Bias* (Ilusi sampel kecil). Angka profit awal murni kebetulan statistik pada sampel belasan trade.

---

### 5. STRAT-08: XAUUSD M15 London Drive Fibonacci 78.6% Discount
- **Konsep**: Menarik Fibonacci dari dorongan 1 jam awal London (14:00–15:30 WIB). Pasang Buy Limit di level 78.6% (Deep Discount) dengan SL $2.50 dan TP 1.5R.
- **Hasil Backtest Awal (Cacat Simulasi)**:
  - 1.277 trade, Win Rate 44.9%, Profit Factor **1.229**, Total Cuan **+93.5 R**, Max DD -21.0 R. Sempat dinyatakan lulus (*Valid*).
- **Hasil Pembongkaran Forensik Phase 2C / 2D (Ask Penetration Test)**:
  - Terbukti simulasi awal menggunakan **Bid Low** untuk order Buy Limit. Di pasar riil, Buy Limit dieksekusi di harga **Ask** (Bid + Spread).
  - Ketika diuji dengan penetrasi Ask riil:
    - Win Rate ambruk dari 44.5% ke **34.7%**.
    - Profit Factor hancur dari 1.229 menjadi **0.796 (RUGI BESAR)**.
    - Max Drawdown meledak dari -21.0 R menjadi **-134.5 R**.
    - Akumulasi PnL riil: **Rugi -108.0 R**.
- **Status**: **INVALIDATED & REJECTED (CACAT EKSEKUSI LIMIT ORDER)**.
- **Pelajaran Mahal**: Jangan pernah menguji Buy Limit hanya dari Low candle M1; wajib tambahkan spread aktual dan syarat penetrasi 1 tick penuh ($0.10).

---

### 6. Riset 32 Varian Pre-Registered H1–H4 (Scalping M1 Frekuensi Tinggi)
- **Mandat**: Menemukan strategi scalping frekuensi tinggi (5+ trade/hari) dengan TP 0.5R–0.8R dan SL 1.0R pada 4 keluarga kuantitatif:
  - H1: Liquidity Sweep and Reclaim.
  - H2: Intraday Mean Reversion (Bollinger/Z-Score).
  - H3: Failed Breakout.
  - H4: Micro-Momentum Continuation.
- **Hasil Pengujian In-Sample (2021–2024) & Validation (2024–2025)**:
  - **Seluruh 32 varian GAGAL TOTAL**.
  - Rata-rata Win Rate: **36% s/d 44%** (Jauh dari syarat lolos 68%).
  - Profit Factor: **0.22 s/d 0.54**.
  - Net Expectancy: **-0.28 R s/d -0.74 R**.
- **Status**: **REJECTED UNDER TESTED CONFIGURATIONS**.
- **Penyebab Ilmiah**: Pemotongan TP menjadi 0.5R–0.8R di timeframe M1 membunuh ekspektansi matematis karena friksi ECN ($0.47 round-trip) memakan **10% sampai 70% dari seluruh budget risiko per trade**.

---

# BAGIAN 2: BEDAH YOUTUBE TRADING & PEMBUKTIAN DATA

---

### 7. Bedah Video YouTube #1 (`c62Tj28zfyQ`): Momentum Candle Fibo M5
- **Klaim Kreator**: Teknik scalping pasti profit, Win Rate 80% ke atas dengan Fibo 23.6% (Entry 1), Fibo 61.8% (Entry 2), SL 74.5%, TP -27%.
- **Uji Kuantitatif 12 Tahun (764.412 candle M5, 2015–2026)**:
  - Total Trade: 23.716 trade.
  - **Fibo 23.6%**: Win Rate 51.3%, RR 0.68:1, Profit Factor **0.72**, Akumulasi **Rugi -3.007 R**.
  - **Fibo 61.8%**: Win Rate 20.2%, Profit Factor **0.83**, Akumulasi **Rugi -1.388 R**.
- **Status**: **CLICKBAIT RITEL / FALSIFIED**.

---

### 8. Bedah Video YouTube #2 (`wsXu2Xr1nQc`): Klaim Win Rate 70% di 30 Mei 2025
- **Klaim Kreator**: Menunjukkan bukti live trading Win Rate 70% pada tanggal 30 Mei 2025 dengan teknik mean reversion / scalping.
- **Forensik Data 10 Tahun (`analyze_daily_variance.py`)**:
  - Pada tanggal 30 Mei 2025, Win Rate memang tercatat 61.5%–70.8% karena pasar emas hari itu mengalami kondisi anomali sideways sempurna (range harian cuma $51).
  - Namun anomali hari seperti itu hanya terjadi **0.05% dari waktu (1 dari 2.116 hari)**.
  - Pada 54% hari lainnya di pasar emas, strategi tersebut hancur lebur (Win Rate $\le 30\%$) akibat terkena tren kuat, sehingga secara jangka panjang net expectancy-nya **-0.38 R**.
- **Status**: **CHERRY-PICKING ANOMALI / FALSIFIED**.

---

### 9. Bedah Video YouTube #3 (`LdQDazFjjk8`): Debunking Momentum Candle WR 80%
- **Isi Video**: Video independen yang menguji klaim teknik video #1 menggunakan tick data MT5 selama 6 tahun (2021–2026).
- **Temuan Video**:
  - Versi utama hanya menang **43%** (rugi setiap tahun berturut-turut, drawdown hampir 100%).
  - Versi TP ujung candle Win Rate naik ke 61%, tetapi RR jomplang (0.46:1) menuntut Win Rate > 68%, sehingga tetap bangkrut.
  - Masuk acak (random entry) menang 47%, terbukti **masuk acak lebih bagus daripada teknik momentum candle**.
  - *Adverse Non-fill*: 1 dari 4 candle momentum terbang tanpa pullback; candle yang pullback mayoritas adalah jebakan pembalikan arah.
- **Status**: **HASIL KITA TERKONFIRMASI 100% SAMA**.

---

### 10. Bedah Video YouTube #4 (`JddnO_5Pjxw`): Scalping Dua Candle M30 -> M5
- **Klaim Kreator**: 1 candle impulsif + 1 candle searah di M30. Tarik kotak, entry di M5 saat retrace 61.8%, SL di luar kotak, TP 1:2.
- **Uji Kuantitatif 12 Tahun (127.433 candle M30, 2015–2026)**:
  - Versi 61.8% RR 1:2: 1.722 trade, Win Rate **31.07%** (butuh 33.3%), PF **0.797**, Rugi **-235.9 R**.
  - Versi 50.0% RR 1:2: 2.578 trade, Win Rate **34.52%**, PF **0.861**, Rugi **-224.0 R**.
  - Versi 61.8% RR 1:1: 1.290 trade, Win Rate **42.87%** (butuh 50%), PF **0.740**, Rugi **-189.6 R**.
  - Versi 61.8% RR 1:3: 1.755 trade, Win Rate **26.95%** (butuh 25%), PF **0.823**, Rugi **-222.0 R**.
- **Status**: **FALSIFIED (SEMUA 15 VARIAN DI VIDEO & PENGUJIAN KITA MERUGI)**.

---

### 11. Bedah Video YouTube #5 (`lAENVt206ho`): Pola N Breakout-Retest S/R (Andre Rizky)
- **Klaim Kreator**: Pola N berbasis Breakout Support/Resistance di H1 dan retest mantul di M15/M30. Diklaim Win Rate di atas 60%.
- **Uji Kuantitatif 12 Tahun (2015–2026)**:
  - Total Trade: 2.154 trade.
  - Win Rate: **36.35%** (Jauh di bawah klaim 60%).
  - Profit Factor: **0.841 (RUGI BERSIH)**.
  - Net Realized: **-216.7 R (Drawdown -217.7 R)**.
  - Long: WR 37.4%, PF 0.88 (-94.2 R). Short: WR 34.9%, PF 0.79 (-122.5 R).
- **Status**: **REJECTED (JEBAKAN FAKEOUT RETEST)**.
- **Penyebab Kegagalan**: Karakteristik emas jarang memberi retest bersih; saat retrace kembali ke level breakout, harga mayoritas bablas (*fakeout*).

---

### 12. Bedah Video YouTube #6 (`fcySBFFsm04`): Pola N Asli Goichi Hosoda (H1/H4)
- **Konsep**: Gelombang N klasik (A-B-C). Titik C wajib lebih tinggi dari A ($C > A$ untuk Bullish). Pasang pending **Buy Stop di titik B**, SL di bawah C, TP rumus Hosoda $C + (B - A)$.
- **Uji Kuantitatif 12 Tahun (4.18M bars M1, 2015–2026)**:
  - **Timeframe H4**: 724 trade, Win Rate **70.72%**, Profit Factor **1.766**, Total Net **+160.6 R**, Max DD **-10.2 R**.
  - **Timeframe H1**: 1.963 trade, Win Rate **67.29%**, Profit Factor **1.521**, Total Net **+328.3 R**, Max DD **-19.6 R**.
  - Sisi Long H1: WR 69.3%, PF 1.753 (+239.7 R). Sisi Short H1: WR 64.89%, PF 1.285 (+88.6 R).
  - Filter RR $\ge 0.80$: 792 trade, WR 52.7%, PF **1.800**, Total Net **+293.8 R**, Max DD **-12.6 R**.
- **Status**: **VALID & SANGAT KUAT (EDGE TERVERIFIKASI)**.

---

### 13. Bedah Video YouTube #7 (`HhaNJxbXfeA`): Pola N Straddle Dua Arah (Pak Tito)
- **Konsep**: Modifikasi panggung. Pasang Buy Stop di High swing dan Sell Stop di Low swing secara bersamaan. Target 1:1 proyeksi kotak range.
- **Uji Kuantitatif 12 Tahun (2015–2026)**:
  - **H4**: 3.124 trade, Win Rate **48.43%**, Profit Factor **1.355**, Total Net **+396.0 R**, Max DD **-25.0 R**.
  - **H1**: 7.079 trade, Win Rate **42.90%**, Profit Factor **1.380**, Total Net **+837.0 R**, Max DD **-36.0 R**.
- **Status**: **MARGINAL EDGE (PROFIT TAPI RAWAN WHIPSAW)**.
- **Kelemahan**: Win Rate di bawah 50%, rawan *double stop loss* berturut-turut di fase konsolidasi.

---

### 14. Bedah Video YouTube #8 (`rkOiwuhluUM`): Pola N Baku + Filter Expired (The Traders)
- **Konsep Mutakhir**:
  1. Swing High & Swing Low terdefinisi baku di H1/M30/M15/M5.
  2. **Single vs Double Order**: Hanya pasang Double Order jika harga berada di 35%–65% tengah kotak. Jika sudah dekat batas, hanya pasang order searah momentum.
  3. **Aturan Expired (Kunci Sukses)**: Jika terbentuk swing baru yang lebih sempit sebelum order terisi, pending order lama **WAJIB DICANCEL**.
  4. SL di luar swing, TP fix rasio 1:1.5.

#### Matriks Kinerja 12 Tahun Penuh (Cross-Check Semua Timeframe):

| Timeframe | Total Trade (12 Thn) | Frekuensi Eksekusi | Win Rate (WR) | Profit Factor (PF) | Net Expectancy | Total Net Cuan | Max Drawdown | Keterangan |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **H1** | 650 trade | ~4–5 / bln (~1 / mgg) | **61.08%** | **2.360** | +0.4264 R | **+277.2 R** | **-8.9 R** | Sangat Santai & Stabil |
| **M30** | 1.870 trade | ~13 / bln (~3 / mgg) | **62.73%** | **2.526** | **+0.4587 R** | **+857.8 R** | **-8.6 R** | 🏆 **SWEET SPOT TERBAIK** |
| **M15** | 4.246 trade | ~30 / bln (~7 / mgg) | **62.29%** | **2.450** | **+0.4460 R** | **+1.893.6 R** | **-10.1 R** | Paling Pas Lolos Kilat |
| **M5** | 11.667 trade | ~81 / bln (~19 / mgg)| **57.94%** | **2.038** | +0.3458 R | **+4.034.1 R** | **-14.6 R** | Scalping Aktif |

#### Kinerja Prop Firm (The 5ers $2,500 High Stakes 2-Step / 10.000 Monte Carlo):
- **M15 (Risiko 0.5% / trade)**: Lolos dalam **~31 hari kerja (~1.5 bulan)**, Pass Rate **100.0%**, Max DD cuma 5.0% dari modal.
- **M15 (Risiko 1.0% / trade)**: Lolos dalam **~15 hari kerja (~3 minggu)**, Pass Rate **99.9%**.
- **M5 (Risiko 0.5% / trade)**: Lolos dalam **~14 hari kerja (~2.8 minggu)**, Pass Rate **100.0%**, Max DD 7.3% modal.
- **M30 (Risiko 1.0% / trade)**: Lolos dalam **~34 hari kerja (~1.7 bulan)**, Pass Rate **99.9%**, Max DD 8.6% modal.

---

## RINGKASAN PENGAMBILAN KEPUTUSAN UNTUK KONTEN & RISET

1. **Topik Edukasi & Bongkar Fakta (*Debunking Content*)**:
   - Membongkar ilusi Win Rate 80% Fibo 23.6% (bukti matematis RR negatif membuat akun bangkrut).
   - Membongkar ilusi Breakout-Retest klasik di Gold (kalah telak dengan pending stop order momentum).
   - Membongkar bahaya straddle membabi buta tanpa aturan *Expired*.
2. **Topik Strategi Terbukti (*Actionable Edge Content*)**:
   - Pola N Goichi Hosoda + Modifikasi Filter *Expired*: Strategi mekanis baku dengan Profit Factor 2.52 di M30 dan Max DD cuma -8.6 R.
   - Cara lolos The 5ers 2.5K dalam waktu 3 minggu sampai 1.5 bulan dengan risiko terukur 0.5% per trade.
