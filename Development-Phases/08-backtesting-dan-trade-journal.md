# Fase 08 — Backtesting dan Trade Journal

## Tujuan

Mengukur apakah aturan dan skor memiliki nilai sebelum dipercaya, serta membangun feedback loop dari setup ke outcome.

## Pekerjaan backtesting

### 1. Point-in-time dataset

- Gunakan hanya data yang telah tersedia pada waktu simulasi.
- Bedakan event time, published time, received time, dan processing time.
- Simpan revisi data ekonomi agar backtest tidak memakai nilai revisi masa depan.
- Gunakan candle final sesuai cutoff dan hindari look-ahead pada multi-timeframe.
- Simpan identitas broker/server, simbol broker, dan dataset version karena candle dan spread dapat berbeda antar-broker.

### 2. Simulation engine

- Reuse calculation/risk rules produksi, bukan membuat formula duplikat.
- Model spread, slippage, commission, swap bila relevan, dan keterbatasan eksekusi candle.
- Gunakan histori dari broker MT5 yang sama jika cukup; bila memakai dataset tambahan, pisahkan hasilnya dan nyatakan source secara eksplisit.
- Definisikan aturan jika SL dan TP tersentuh pada candle yang sama.
- Simpan configuration, code/formula version, dataset version, dan random seed.

### 3. Metrics

- Win rate, expectancy, profit factor, average R, maximum drawdown, Sharpe/Sortino jika tepat.
- Breakdown per pair, timeframe, regime, session, direction, dan confidence bucket.
- Calibration: apakah confidence yang lebih tinggi benar-benar berkorelasi dengan outcome lebih baik.
- Coverage: seberapa sering sistem menghasilkan opportunity dan berapa yang ditolak Risk Engine.

### 4. Validasi strategi

- Pisahkan train/tuning, validation, dan out-of-sample period.
- Gunakan walk-forward testing.
- Hindari memilih parameter hanya karena performa terbaik pada satu periode.
- Bandingkan dengan baseline sederhana dan laporkan hasil negatif.

## Pekerjaan trade journal

- Simpan setup, screenshot/snapshot evidence, rencana entry, SL, TP, dan risk.
- Catat apakah trade diambil atau dilewati beserta alasan pengguna.
- Simpan fill aktual, partial close, biaya, exit, dan outcome dalam R.
- Izinkan tag dan catatan evaluasi.
- Hubungkan outcome ke versi sinyal dan assessment yang asli.

## Deliverables

- CLI/job/API untuk menjalankan backtest reproducible.
- Laporan metrik dan breakdown.
- UI trade journal dan halaman evaluasi.
- Daftar kelemahan strategi serta keputusan go/no-go.

## Kriteria selesai

- Backtest yang sama menghasilkan hasil yang sama.
- Audit membuktikan tidak ada future-data leakage pada sampel kasus.
- Biaya transaksi dan asumsi eksekusi terlihat di laporan.
- Hasil out-of-sample dan baseline tersedia sebelum strategi dinyatakan layak.
- Setup produksi dapat dihubungkan secara utuh ke outcome journal.
