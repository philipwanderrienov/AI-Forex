# Fase 04 — Market Brain dan Instrument Scanner

## Tujuan

Mengubah snapshot analisis menjadi gambaran kekuatan mata uang, regime pasar, ranking pair, dan opportunity yang dapat disaring.

## Batas tanggung jawab

- **Analysis Engine:** menghasilkan evidence dan skor per dimensi.
- **Market Brain:** menggabungkan evidence dan mendeteksi konflik.
- **Instrument Scanner:** menjalankan evaluasi untuk seluruh universe instrumen.
- **Opportunity Engine:** menentukan apakah kandidat layak diteruskan ke Risk Engine.

## Pekerjaan

### 1. Currency strength

- Definisikan cara mengagregasi kontribusi semua pair untuk setiap mata uang.
- Normalisasi agar mata uang yang muncul pada lebih banyak pair tidak otomatis unggul.
- Pisahkan strength per timeframe dan composite strength.
- Tangani pair yang datanya stale atau tidak lengkap.
- Currency strength hanya berlaku pada empat instrumen forex; XAUUSD tidak dimasukkan sebagai currency pair.

### 2. Market regime

- Klasifikasikan trending, ranging, high-volatility, low-volatility, atau uncertain.
- Gunakan fitur yang terukur seperti ATR, slope, structure, dan dispersion.
- Versioning threshold regime agar dapat diuji historis.
- Izinkan strategi/aturan berbeda menurut regime.

### 3. Instrument score

- Untuk forex, kombinasikan currency-strength differential, technical score, regime fit, dan data quality.
- Untuk XAUUSD, gunakan formula khusus tanpa currency-strength differential sesuai fase 00.
- Deteksi konflik, misalnya trend H4 bullish tetapi struktur H1 bearish.
- Simpan kontribusi setiap faktor dan alasan penalti.
- Jangan masukkan fundamental/news sampai modul tersebut tersedia; gunakan status `not_available`.

### 4. Opportunity rules

- Tetapkan minimum score, confidence, liquidity/session, spread, dan freshness.
- Hasilkan `BUY_CANDIDATE`, `SELL_CANDIDATE`, atau `NO_OPPORTUNITY`.
- Cegah kandidat jika data stale, spread abnormal, atau confidence terlalu rendah.
- Buat rules sebagai konfigurasi versioned, bukan angka tersebar di kode.

### 5. Scanner scheduling

- Jalankan setelah candle relevan final atau pada jadwal yang jelas.
- Pastikan satu pair gagal tidak menggagalkan semua pair.
- Simpan ranking snapshot agar pengguna melihat keadaan yang konsisten.
- Publikasikan perubahan ranking ke lapisan API/real-time.

## Deliverables

- Currency strength board.
- Market regime per instrument/timeframe.
- Instrument ranking lengkap dengan score breakdown dan formula version sesuai instrument type.
- Opportunity candidate yang siap diperiksa Risk Engine.

## Pengujian

- Scenario test untuk strong-vs-weak currency, conflicting timeframe, ranging, dan stale data.
- Property test agar pembalikan pair tidak menghasilkan arah yang tidak logis.
- Determinism test untuk ranking dengan input yang sama.
- Load test untuk seluruh universe pair.

## Kriteria selesai

- Ranking dapat direkonstruksi dari snapshot input.
- Setiap kandidat memiliki evidence dan alasan lolos/gagal.
- Kondisi data buruk selalu menghasilkan blokir atau confidence penalty yang terlihat.
- Scanner memenuhi target waktu pemrosesan MVP.
