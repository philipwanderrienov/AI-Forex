# Fase 05 — Risk Engine

## Tujuan

Memisahkan peluang pasar dari kelayakan mengambil risiko. Kandidat dengan arah yang kuat tetap dapat menghasilkan `WAIT` jika risikonya tidak dapat diterima.

## Pekerjaan

### 1. Risk policy

- Tetapkan risiko maksimum per trade, per hari, dan total exposure.
- Definisikan minimum risk/reward dan batas spread.
- Tentukan batas korelasi, misalnya beberapa posisi yang sama-sama mengekspos USD.
- Tetapkan kill switch untuk drawdown, stale data, atau gangguan provider.
- Simpan policy sebagai konfigurasi versioned dan tervalidasi.

### 2. Stop-loss dan take-profit

- Hitung kandidat SL dari ATR, market structure, dan invalidation level.
- Validasi jarak minimum/maksimum dan spread terhadap SL.
- Hitung TP berdasarkan target structure atau risk/reward.
- Nyatakan harga, pip distance, dan alasan pemilihan level.

### 3. Position sizing

- Input: equity, risk percentage, entry, stop-loss, pair, dan account currency.
- Hitung pip value dan konversi mata uang dengan tepat.
- Terapkan batas ukuran minimum/maksimum dan rounding broker.
- Jika data akun belum tersedia, tampilkan sizing simulasi dengan label yang jelas.

### 4. Event dan volatility protection

- Terapkan penalti atau embargo menjelang berita high-impact.
- Tolak setup saat spread/volatilitas abnormal atau likuiditas rendah.
- Tentukan cooldown setelah shock event.
- Fitur news proximity diaktifkan setelah fase 07; sebelumnya statusnya eksplisit.

### 5. Risk assessment

- Hasilkan `APPROVED`, `REDUCED`, atau `REJECTED`.
- Sertakan warnings, blocking reasons, SL, TP, R/R, dan suggested size.
- Pisahkan risk score dari market-direction score.
- Simpan seluruh input dan policy version untuk audit.

## Pengujian

- Unit test pip value untuk berbagai quote/account currency.
- Boundary test risiko nol, SL terlalu dekat, spread besar, dan size limit.
- Scenario test correlated exposure, daily drawdown, dan high-impact event.
- Property test: memperlebar SL dengan risk amount tetap tidak boleh memperbesar position size.

## Kriteria selesai

- Tidak ada setup yang lolos tanpa SL, risk amount, dan audit trail.
- Position sizing benar pada kasus referensi yang diverifikasi manual.
- Semua rejection memiliki kode dan penjelasan yang dapat ditampilkan UI.
- Risk Engine tetap berfungsi tanpa AI dan gagal secara aman ketika input hilang.

