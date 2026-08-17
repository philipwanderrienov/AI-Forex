# Fase 03 — Technical Analysis Engine

## Tujuan

Menghasilkan indikator, market structure, dan technical score yang deterministik, dapat dijelaskan, dan bebas look-ahead bias.

## Pekerjaan

### 1. Indicator calculator

- Implementasikan EMA20, EMA50, EMA200, RSI14, MACD, dan ATR14.
- Definisikan warm-up period dan perilaku ketika candle belum cukup.
- Hitung hanya dari candle final untuk sinyal final.
- Tetapkan precision dan rounding secara konsisten.

### 2. Market structure

- Identifikasi swing high/low dengan aturan yang eksplisit.
- Turunkan higher high, higher low, lower high, dan lower low.
- Tentukan support/resistance dan aturan penggabungan level yang berdekatan.
- Klasifikasikan trend serta kondisi ranging/uncertain.

### 3. Technical scoring

- Implementasikan kondisi dan nilai dari [Tabel Aturan Scoring v1](00-scoring-rules-v1.md) tanpa konstanta tersembunyi.
- Ubah indikator menjadi sub-score pada skala canonical.
- Terapkan bobot dari spesifikasi fase 00.
- Pisahkan `score`, `confidence`, dan `dataQuality`.
- Simpan komponen skor agar alasan hasil dapat direkonstruksi.
- Versioning konfigurasi formula dan parameter indikator.

### 4. Multi-timeframe analysis

- Tentukan timeframe utama dan confirmation timeframe.
- Hindari memakai candle timeframe besar yang belum final.
- Definisikan penalti konflik dan bonus konfluensi.
- Hasilkan status `insufficient_data` jika input tidak mencukupi.

### 5. Penyimpanan snapshot

- Simpan `TechnicalSnapshot` per instrumen, timeframe, dan calculation time.
- Sertakan candle cutoff, formula version, sub-score, dan evidence.
- Pastikan recalculation historis tidak menimpa hasil produksi tanpa jejak.

## Contoh hasil

```json
{
  "instrument": "EURUSD",
  "timeframe": "H1",
  "asOf": "2026-08-14T10:00:00Z",
  "trend": "BEARISH",
  "emaScore": -7.0,
  "rsiScore": -2.0,
  "structureScore": -8.0,
  "momentumScore": -4.5,
  "supportResistanceContext": -7.0,
  "volatilitySetup": -4.0,
  "technicalScore": -6.5,
  "confidence": 78,
  "dataQuality": "GOOD",
  "formulaVersion": "technical-v1"
}
```

## Pengujian

- Golden tests terhadap dataset dan hasil dari library/perhitungan pembanding.
- Unit test flat market, insufficient candles, gap, extreme volatility, dan zero volume.
- Test anti-look-ahead dengan memastikan output pada waktu T tidak berubah karena candle setelah T.
- Performance test untuk seluruh instrument/timeframe MVP, termasuk fixture precision dan volatilitas XAUUSD.

## Kriteria selesai

- Hasil perhitungan reproducible untuk input dan versi formula yang sama.
- Seluruh komponen score dapat dijelaskan dari evidence.
- Tidak ada candle masa depan atau incomplete yang masuk ke sinyal final.
- Runtime memenuhi target scanner yang ditentukan pada fase 00.
