# Fase 00 — Tabel Aturan Scoring v1

## Status dan tujuan

- Versi parameter: `technical-v1`.
- Berlaku untuk `EURUSD`, `GBPUSD`, `EURGBP`, `EURCHF`, dan `XAUUSD` pada `M15`, `H1`, dan `H4`.
- Semua perhitungan hanya memakai candle `FINAL` dan informasi yang tersedia pada `candleCutoff`.
- Angka di bawah adalah baseline deterministik untuk backtest dan forward test, bukan formula yang sudah terbukti menghasilkan profit.
- Skor positif berarti evidence bullish; skor negatif berarti evidence bearish. Skor bukan instruksi menutup posisi yang sudah ada.

## 1. Parameter indikator

| Parameter | Nilai v1 | Keterangan |
|---|---:|---|
| EMA cepat | `20` candle | Arah jangka pendek |
| EMA menengah | `50` candle | Arah menengah |
| EMA lambat | `200` candle | Filter trend utama |
| RSI | `14` candle | Wilder smoothing |
| MACD | `12, 26, 9` | EMA fast, EMA slow, signal |
| ATR | `14` candle | Wilder smoothing |
| ATR percentile lookback | `100` candle final | Menilai regime volatilitas |
| Swing pivot | `2 kiri + 2 kanan` | Pivot baru final setelah dua candle kanan selesai |
| Minimum warm-up | `250` candle final | Kurang dari ini menghasilkan `INSUFFICIENT` |
| Precision internal | Decimal tanpa pembulatan antara | Pembulatan skor satu desimal hanya pada output |

## 2. EMA trend score — bobot 30%

Gunakan `close`, `EMA20`, `EMA50`, dan `EMA200` pada candle final terakhir.

| Kondisi | `emaTrend` |
|---|---:|
| `close > EMA20 > EMA50 > EMA200` | `+10` |
| `EMA20 > EMA50 > EMA200`, tetapi `close <= EMA20` | `+7` |
| `close > EMA20 > EMA50`, tetapi susunan terhadap EMA200 belum bullish penuh | `+4` |
| `close > EMA200` dan susunan EMA bercampur | `+2` |
| Jarak seluruh EMA sangat rapat dan susunannya bercampur | `0` |
| `close < EMA200` dan susunan EMA bercampur | `-2` |
| `close < EMA20 < EMA50`, tetapi susunan terhadap EMA200 belum bearish penuh | `-4` |
| `EMA20 < EMA50 < EMA200`, tetapi `close >= EMA20` | `-7` |
| `close < EMA20 < EMA50 < EMA200` | `-10` |

EMA dianggap “sangat rapat” jika:

```text
(max(EMA20, EMA50, EMA200) - min(EMA20, EMA50, EMA200)) / ATR14 < 0.20
```

Jika lebih dari satu baris cocok, gunakan kondisi paling atas yang paling spesifik. Perbandingan tepat sama (`=`) tidak dianggap menembus level.

## 3. Market structure score — bobot 30%

Bandingkan dua swing high final dan dua swing low final terbaru. Toleransi level adalah `0.10 × ATR14`; perbedaan dalam toleransi dianggap equal high/low.

| Kondisi struktur | `marketStructure` |
|---|---:|
| Higher high + higher low, dan close menembus swing high terakhir | `+10` |
| Higher high + higher low | `+8` |
| Higher low terbentuk; swing high belum terkonfirmasi | `+4` |
| Close menembus resistance terakhir, tetapi belum ada higher low | `+3` |
| Equal/mixed highs dan lows; tidak ada breakout valid | `0` |
| Close menembus support terakhir, tetapi belum ada lower high | `-3` |
| Lower high terbentuk; swing low belum terkonfirmasi | `-4` |
| Lower high + lower low | `-8` |
| Lower high + lower low, dan close menembus swing low terakhir | `-10` |

Breakout valid memerlukan close candle berada sedikitnya `0.05 × ATR14` di luar level. Wick saja tidak dihitung sebagai breakout.

## 4. Momentum score — bobot 20%

Momentum merupakan gabungan RSI dan MACD:

```text
momentum = 50% × rsiScore + 50% × macdScore
```

### 4.1 RSI14

| Kondisi RSI14 | `rsiScore` |
|---|---:|
| `60–69.99` dan RSI naik dibanding candle sebelumnya | `+8` |
| `60–69.99` dan RSI tidak naik | `+6` |
| `55–59.99` | `+5` |
| `50–54.99` | `+2` |
| `45–49.99` | `-2` |
| `40–44.99` | `-5` |
| `30.01–39.99` dan RSI tidak turun | `-6` |
| `30.01–39.99` dan RSI turun dibanding candle sebelumnya | `-8` |
| `>= 70` | `+3` |
| `<= 30` | `-3` |

RSI overbought/oversold tidak otomatis dianggap reversal. Skornya dikurangi karena entry lanjutan mempunyai risiko terlambat, bukan dibalik arahnya.

### 4.2 MACD histogram

Normalisasi histogram agar dapat dibandingkan lintas instrumen:

```text
macdNorm = MACDHistogram / ATR14
```

| Kondisi | `macdScore` |
|---|---:|
| `macdNorm >= +0.10` dan histogram meningkat | `+10` |
| `macdNorm >= +0.05` | `+7` |
| `0 < macdNorm < +0.05` | `+3` |
| `macdNorm = 0` atau absolutnya `< 0.005` | `0` |
| `-0.05 < macdNorm < 0` | `-3` |
| `macdNorm <= -0.10` dan histogram makin negatif | `-10` |
| `macdNorm <= -0.05` | `-7` |

“Meningkat” berarti nilai histogram sekarang lebih besar daripada candle sebelumnya; “makin negatif” berarti lebih kecil.

## 5. Support/resistance context — bobot 10%

Level support/resistance berasal dari swing pivot final. `distance` selalu dinormalisasi terhadap ATR14.

| Kondisi | `supportResistanceContext` |
|---|---:|
| Rejection bullish dari support dalam `0.25 ATR`, lalu close bullish | `+7` |
| Breakout valid di atas resistance dan retest bertahan | `+10` |
| Ruang ke resistance berikutnya `>= 1.5 ATR` dalam konteks bullish | `+4` |
| Harga berada di tengah range tanpa keunggulan arah | `0` |
| Ruang ke support berikutnya `>= 1.5 ATR` dalam konteks bearish | `-4` |
| Rejection bearish dari resistance dalam `0.25 ATR`, lalu close bearish | `-7` |
| Breakout valid di bawah support dan retest gagal naik kembali | `-10` |

Jika support dan resistance sama-sama berjarak `< 0.5 ATR`, skor dipaksa `0` karena ruang pergerakan terlalu sempit. Retest harus terjadi setelah breakout dan hanya menggunakan candle final.

## 6. Volatility setup — bobot 10%

Komponen ini menilai apakah volatilitas mendukung arah evidence lain. Tentukan `provisionalDirection` dari jumlah empat komponen sebelumnya. Jika jumlahnya nol, skor volatilitas juga nol.

| ATR14 percentile terhadap 100 candle | Kondisi candle terakhir | Nilai absolut | Arah skor |
|---:|---|---:|---|
| `< 20` | Volatilitas sangat rendah | `0` | Netral |
| `20–39.99` | Normal-rendah | `3` | Ikuti `provisionalDirection` |
| `40–79.99` | Kondisi normal/aktif | `7` | Ikuti `provisionalDirection` |
| `80–94.99` | Tinggi, tetapi range candle `<= 2 ATR` | `4` | Ikuti `provisionalDirection` |
| `>= 95` atau range candle `> 2 ATR` | Lonjakan ekstrem | `0` | Netral; tambahkan warning |

Jika spread masuk kategori abnormal, komponen ini tidak dihitung dan seluruh rekomendasi baru diblokir oleh data/risk rule.

## 7. Technical score per timeframe

```text
technical(tf) =
  0.30 × emaTrend
+ 0.30 × marketStructure
+ 0.20 × momentum
+ 0.10 × supportResistanceContext
+ 0.10 × volatilitySetup
```

Simpan nilai internal tanpa pembulatan. Output dibulatkan satu desimal dengan metode `away from zero` pada nilai tepat setengah.

## 8. Multi-timeframe score

| Timeframe | Bobot | Fungsi |
|---|---:|---|
| `M15` | `20%` | Timing/confirmation |
| `H1` | `50%` | Keputusan utama |
| `H4` | `30%` | Konteks dan regime |

```text
multiTimeframeTechnical =
  0.20 × technical(M15)
+ 0.50 × technical(H1)
+ 0.30 × technical(H4)
```

### Konflik timeframe

| Kondisi | Hasil |
|---|---|
| H1 dan H4 sama-sama `abs(score) >= 4`, tetapi tandanya berlawanan | `NO_OPPORTUNITY`, blocker `H1_H4_CONFLICT` |
| H1 dan H4 searah, M15 berlawanan dengan `abs(score) >= 4` | Kandidat belum dikirim; tunggu M15 netral/searah, confidence `-15` selama konflik |
| Satu timeframe tidak tersedia atau stale | `NO_OPPORTUNITY`, blocker kualitas data |
| Semua timeframe searah | Tidak ada penalti |

## 9. Regime-fit directional score

| Regime | Kondisi terhadap arah MTF | Skor |
|---|---|---:|
| `TRENDING` | Searah MTF dan H1/H4 | `sign(MTF) × 8` |
| `RANGING` | Harga dekat tepi range dan ada rejection searah | `sign(MTF) × 4` |
| `RANGING` | Harga di tengah range | `0` |
| `HIGH_VOLATILITY` | Bukan spike ekstrem dan spread normal | `sign(MTF) × 2` |
| `HIGH_VOLATILITY` | Spike ekstrem/spread abnormal | `0` dan blocker |
| `LOW_LIQUIDITY` atau `UNKNOWN` | Apa pun | `0`; tidak boleh menambah confidence |

## 10. Currency-strength differential untuk forex

Setiap currency diberi strength `[-10,+10]` dari rata-rata perubahan ternormalisasi dan breadth instrumen yang tersedia. Detail perhitungannya akan divalidasi pada Fase 04.

```text
rawDifferential = baseCurrencyStrength - quoteCurrencyStrength
currencyStrengthDifferential = clamp(rawDifferential / 2, -10, +10)
```

Contoh: strength EUR `+6` dan USD `-4` menghasilkan `(6 - (-4)) / 2 = +5` untuk `EURUSD`. Komponen ini tidak digunakan pada `XAUUSD`.

## 11. Combined score dan arah peluang

Untuk empat instrumen forex:

```text
combinedScore =
  0.60 × multiTimeframeTechnical
+ 0.20 × currencyStrengthDifferential
+ 0.20 × regimeFitDirectionalScore
```

Untuk `XAUUSD`:

```text
combinedScore =
  0.80 × multiTimeframeTechnical
+ 0.20 × regimeFitDirectionalScore
```

| Syarat | Arah peluang |
|---|---|
| Score `>= +4`, confidence `>= 65`, tanpa blocker | `LONG_CANDIDATE` |
| Score `<= -4`, confidence `>= 65`, tanpa blocker | `SHORT_CANDIDATE` |
| Selain itu | `NO_OPPORTUNITY` |

Untuk forex, jika MTF technical dan currency strength masing-masing `abs >= 4` tetapi berbeda tanda, hasil dipaksa `NO_OPPORTUNITY` dengan blocker `ENGINE_DIRECTION_CONFLICT`.

## 12. Confidence v1

```text
confidence = round(100 × (
  0.35 × dataQualityFactor
+ 0.30 × timeframeAgreement
+ 0.20 × min(abs(combinedScore) / 10, 1)
+ 0.15 × regimeFitFactor
))
```

| Input | Nilai |
|---|---|
| Data quality `GOOD` | `1.00` |
| Data quality `DEGRADED` | `0.50`, tetapi tidak boleh menerbitkan kandidat baru sampai gap pulih |
| Data quality `STALE/INSUFFICIENT` | `0.00` dan blocker |
| Tanda M15/H1/H4 sama dan seluruh `abs >= 4` | Agreement `1.00` |
| H1/H4 sama; M15 netral (`abs < 4`) | Agreement `0.80` |
| H1/H4 sama; M15 berlawanan | Agreement `0.50`, lalu penalti konflik `-15` |
| H1/H4 berlawanan | Agreement `0.00` dan blocker |
| Regime mendukung kuat/sedang/netral/berlawanan | `1.00/0.70/0.40/0.00` |

Confidence dibatasi ke `0–100`. Label UI wajib `Evidence confidence`, bukan “peluang menang”.

## 13. Contoh perhitungan

Misalnya EURUSD menghasilkan:

| Komponen | M15 | H1 | H4 |
|---|---:|---:|---:|
| EMA trend | `+4` | `+7` | `+7` |
| Market structure | `+4` | `+8` | `+8` |
| Momentum | `+3` | `+6` | `+4` |
| Support/resistance | `0` | `+4` | `+4` |
| Volatility setup | `+3` | `+7` | `+7` |
| **Technical score** | **`+3.3`** | **`+6.8`** | **`+6.4`** |

```text
MTF = 0.20(3.3) + 0.50(6.8) + 0.30(6.4) = 5.98

Jika currency strength = +5 dan regime fit = +8:
combined = 0.60(5.98) + 0.20(5) + 0.20(8) = 6.188 → 6.2
```

Hasil masih memerlukan confidence `>= 65`, data fresh, spread normal, tidak ada embargo berita, dan risk assessment yang lolos sebelum notifikasi diterbitkan.

## 14. Fixture pengujian minimum

| Fixture | Expected result |
|---|---|
| Semua EMA/structure/timeframe bullish kuat | Score positif kuat; kandidat long jika seluruh gate lolos |
| Semua komponen bearish kuat | Score negatif kuat; kandidat short jika seluruh gate lolos |
| H1 `+6`, H4 `-6` | `NO_OPPORTUNITY`, `H1_H4_CONFLICT` |
| MTF `+6`, currency strength `-5` | `NO_OPPORTUNITY`, `ENGINE_DIRECTION_CONFLICT` |
| RSI `>= 70` dengan trend bullish | RSI tetap positif `+3`, bukan otomatis short |
| ATR percentile `>= 95` | Volatility score `0` dan warning spike |
| Candle H4 masih partial | Candle diabaikan; bila tidak ada H4 final yang fresh, blocker kualitas data |
| Data stale | `NO_OPPORTUNITY` tanpa menghitung rekomendasi aktif |
| Score tepat `+4`, confidence `65` | `LONG_CANDIDATE` jika tidak ada blocker |
| Score tepat `-4`, confidence `65` | `SHORT_CANDIDATE` jika tidak ada blocker |

Setiap perubahan threshold, parameter, atau bobot wajib membuat versi baru dan menjalankan ulang seluruh fixture, backtest, serta out-of-sample validation.
