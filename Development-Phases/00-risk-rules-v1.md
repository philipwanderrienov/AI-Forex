# Fase 00 — Tabel Aturan Risk Engine v1

## Status dan prinsip

- Versi policy: `risk-v1`.
- Aplikasi hanya memberi estimasi dan mencatat keputusan; pengguna tetap mengeksekusi manual di MetaTrader 5.
- Risiko dihitung dari `equity`, bukan `balance`, agar floating P/L ikut memengaruhi kapasitas risiko.
- Default risiko per setup `0,5%` equity; hard maximum `1%`.
- Angka berikut adalah baseline konservatif untuk backtest/forward test, bukan jaminan keamanan atau profit.
- Risk Engine tidak boleh menaikkan lot agar mencapai minimum broker.

## 1. Input wajib

| Input | Sumber | Freshness/aturan |
|---|---|---|
| Equity dan account currency | `AccountSnapshot` MT5 | `GOOD <= 3 detik`; `STALE > 15 detik` memblokir approval |
| Entry zone, arah, SL, dan TP | `TradeSetup` | Setup belum expired; urutan harga valid |
| Bid/ask dan spread | MT5 | Harga `<= 5 detik`; spread tidak abnormal |
| Tick size/value dan contract size | Metadata simbol MT5 | Tersedia dan valid |
| Volume min/max/step/limit | Metadata simbol MT5 | Dipakai tanpa asumsi universal |
| Margin estimate | Kalkulasi MT5 | Berhasil untuk volume yang disarankan |
| Posisi terbuka dan risiko aktif | Portfolio state | Diperlukan untuk exposure gabungan |
| Realized P/L hari ini | Deal history MT5 | Mengikuti timezone reporting |

Jika satu input wajib tidak tersedia, hasil `REJECTED` dan `suggestedVolume = null`.

## 2. Harga sizing

Gunakan harga paling konservatif di zona:

| Arah | Harga entry untuk sizing |
|---|---|
| `LONG_CANDIDATE` | `entryZoneMax` atau ask terbaru jika lebih tinggi |
| `SHORT_CANDIDATE` | `entryZoneMin` atau bid terbaru jika lebih rendah |

Jika harga melewati zona lebih dari `0,25 × ATR14(H1)`, tolak dengan `ENTRY_CHASE_BLOCKED`.

## 3. Stop-loss

| Aturan | Long | Short |
|---|---|---|
| Invalidation | Di bawah swing low/support yang membatalkan setup | Di atas swing high/resistance yang membatalkan setup |
| Buffer | `0,15 × ATR14(H1)` di bawah level | `0,15 × ATR14(H1)` di atas level |
| Jarak minimum | Terbesar dari `0,8 × ATR14(H1)`, `3 × spread`, dan minimum stop broker | Sama |
| Jarak maksimum | `2,5 × ATR14(H1)` | Sama |

- Stop tidak boleh dipersempit hanya agar lot membesar.
- Jika stop struktur lebih dekat dari minimum, geser menjauh sampai minimum.
- Stop valid di atas `2,5 ATR` menghasilkan `REJECTED: STOP_TOO_WIDE`.
- Tanpa invalidation yang dapat dijelaskan: `REJECTED: NO_VALID_INVALIDATION`.
- XAUUSD memakai ATR dan metadata broker, bukan asumsi pip forex.

## 4. Take-profit dan risk/reward

```text
riskDistance = abs(entrySizingPrice - stopLoss)
rewardDistance = abs(takeProfit - entrySizingPrice)
riskReward = rewardDistance / riskDistance
```

| Kondisi | Keputusan |
|---|---|
| Target struktur memberi `R/R >= 2,0` | Gunakan target struktur atau `2R`, mana yang lebih konservatif |
| Target struktur memberi `1,5 <= R/R < 2,0` | `REDUCED` |
| Target struktur memberi `R/R < 1,5` | `REJECTED: INSUFFICIENT_RISK_REWARD` |
| Tidak ada target yang dapat dijelaskan | `REJECTED: NO_VALID_TARGET` |

TP bukan jaminan harga tercapai. Trailing stop dan partial take-profit otomatis tidak masuk MVP.

## 5. Risk percent

| Kondisi | Risk percent |
|---|---:|
| Confidence `>= 75`, semua data `GOOD`, R/R `>= 2,0` | `0,50%` |
| Confidence `65–74` atau R/R `1,5–1,99` | `0,25%`, decision `REDUCED` |
| Confidence `< 65` | `0%`, `REJECTED` |
| User override | Maksimum `1,00%`; alasan wajib dicatat |

Risk Engine tidak pernah menaikkan risiko di atas `0,5%` otomatis. Hard maximum `1%` membatasi override pengguna, bukan rekomendasi default.

```text
riskAmount = equity × riskPercent / 100
```

## 6. Perhitungan lot

Metode utama menggunakan estimasi kerugian MT5 dalam account currency sehingga dapat bekerja untuk forex, cross-currency, dan XAUUSD:

```text
lossForOneLot = abs(OrderCalcProfit(direction, 1.00 lot, entrySizingPrice, stopLoss))
rawVolume = riskAmount / lossForOneLot
suggestedVolume = floor(rawVolume / volumeStep) × volumeStep
estimatedLoss = abs(OrderCalcProfit(direction, suggestedVolume, entrySizingPrice, stopLoss))
```

Volume valid hanya jika:

```text
estimatedLoss <= riskAmount
volumeMin <= suggestedVolume <= volumeMax
aggregateDirectionalVolume <= volumeLimit
```

| Kondisi | Hasil |
|---|---|
| Kalkulasi profit/loss gagal atau nol | `REJECTED: LOSS_CALCULATION_UNAVAILABLE` |
| `rawVolume < volumeMin` | `REJECTED: BELOW_MINIMUM_VOLUME` |
| Volume melewati maximum/limit | Cap ke batas terendah dan hitung ulang |
| Metadata volume/tick tidak tersedia | `REJECTED: SYMBOL_METADATA_UNAVAILABLE` |

Rumus pip manual hanya untuk tampilan/diagnostik, bukan sumber utama sizing.

## 7. Margin guard

| Guard awal | Keputusan |
|---|---|
| Estimasi margin MT5 gagal | `REJECTED: MARGIN_CALCULATION_UNAVAILABLE` |
| Required margin `> 30%` free margin saat ini | `REJECTED: EXCESSIVE_MARGIN_USAGE` |
| Proyeksi margin level setelah posisi `< 300%` | `REJECTED: LOW_PROJECTED_MARGIN_LEVEL` |
| Free margin/equity stale | `REJECTED: ACCOUNT_DATA_STALE` |

Margin bukan pengganti stop-loss risk; setup harus lolos keduanya.

## 8. Portfolio dan correlated exposure

Risiko aktif adalah estimasi kerugian menuju stop-loss untuk posisi terbuka, ditambah setup baru.

| Batas MVP | Nilai awal | Jika dilanggar |
|---|---:|---|
| Risiko satu setup otomatis | `0,50%` equity | Cap/reject |
| Hard maximum satu setup | `1,00%` equity | Reject |
| Total risiko aktif + setup baru | `1,50%` equity | Reject |
| Jumlah posisi aktif | Maksimum `2` | Reject |
| Posisi pada instrumen sama | Maksimum `1` | Reject |
| Risiko satu kelompok currency/asset | Maksimum `1,00%` equity | Reduce/reject |

| Kelompok | Instrumen terkait |
|---|---|
| EUR | `EURUSD`, `EURGBP`, `EURCHF` |
| GBP | `GBPUSD`, `EURGBP` |
| USD | `EURUSD`, `GBPUSD`, `XAUUSD` |
| CHF | `EURCHF` |
| Gold | `XAUUSD` |

Arah currency leg harus diperhitungkan. Misalnya `LONG EURUSD` dan `LONG EURGBP` sama-sama menambah long EUR. Korelasi statistik tidak diasumsikan tetap.

## 9. Daily loss dan circuit breaker

| Kondisi sejak awal hari reporting | Tindakan |
|---|---|
| Realized + floating P/L `<= -1,5%` start-of-day equity | Setup baru maksimum `0,25%` dan `REDUCED` |
| Realized + floating P/L `<= -2,0%` | Blokir setup baru sampai hari berikutnya |
| Tiga trade rugi berturut-turut | Cooling-off `60 menit` |
| Drawdown `>= 5%` dari high-water mark 30 hari | `RISK_PAUSE`; perlu review manual |

Tidak ada mekanisme menaikkan lot setelah rugi. Martingale dan averaging-down tidak masuk MVP.

## 10. Blocker canonical

| Kode | Penyebab |
|---|---|
| `ACCOUNT_DATA_STALE` | Equity, free margin, atau posisi tidak fresh |
| `MARKET_DATA_STALE` | Harga/candle melewati freshness limit |
| `SETUP_EXPIRED` | TTL setup berakhir |
| `OUTSIDE_LONDON_WINDOW` | Di luar window MVP |
| `HIGH_IMPACT_EVENT_EMBARGO` | Embargo kalender aktif |
| `SPREAD_ABNORMAL` | Spread melewati rule yang dikalibrasi |
| `ENTRY_CHASE_BLOCKED` | Harga terlalu jauh dari entry zone |
| `NO_VALID_INVALIDATION` | Stop tidak mempunyai alasan struktur |
| `STOP_TOO_WIDE` | Stop melebihi batas ATR |
| `INSUFFICIENT_RISK_REWARD` | R/R di bawah `1,5` |
| `BELOW_MINIMUM_VOLUME` | Minimum lot broker melanggar risk cap |
| `PORTFOLIO_RISK_LIMIT` | Total risiko aktif terlalu besar |
| `CORRELATED_EXPOSURE_LIMIT` | Currency/asset exposure terlalu besar |
| `DAILY_LOSS_LIMIT` | Circuit breaker harian aktif |
| `MARGIN_GUARD_FAILED` | Margin tidak cukup/terlalu agresif |

Satu blocker cukup untuk `REJECTED`; simpan seluruh blocker yang berlaku untuk audit.

## 11. Urutan evaluasi

```text
Validasi freshness dan session
→ validasi setup, entry, SL, TP, dan R/R
→ tentukan risk percent
→ hitung loss 1 lot melalui MT5
→ floor volume sesuai volume step
→ hitung ulang estimated loss
→ validasi margin
→ validasi portfolio/currency exposure
→ APPROVED, REDUCED, atau REJECTED
```

## 12. Contoh sizing ilustratif

```text
Equity               = USD 10.000
Risk percent         = 0,50%
Risk amount          = USD 50
Loss 1 lot entry→SL  = USD 420  (hasil kalkulasi MT5)
Raw volume           = 50 / 420 = 0,119047 lot
Broker volume step   = 0,01 lot
Suggested volume     = floor(0,119047 / 0,01) × 0,01 = 0,11 lot
Estimated loss       = USD 46,20
```

Nilai ini hanya contoh matematika, bukan rekomendasi lot atau setup nyata.

## 13. Fixture pengujian minimum

| Fixture | Expected result |
|---|---|
| Equity `10.000`, risk `0,5%` | Risk amount `50` account currency |
| Raw volume `0,119`, step `0,01` | Volume `0,11`, tidak dibulatkan naik |
| Raw volume di bawah minimum | `REJECTED: BELOW_MINIMUM_VOLUME` |
| Account snapshot berusia `16 detik` | `REJECTED: ACCOUNT_DATA_STALE` |
| R/R `1,49` | `REJECTED: INSUFFICIENT_RISK_REWARD` |
| R/R `1,75`, confidence `70` | Risk `0,25%`, `REDUCED` |
| Active risk `1,25%` + setup `0,5%` | `REJECTED: PORTFOLIO_RISK_LIMIT` |
| Minimum lot menghasilkan loss di atas cap | Reject; jangan naikkan risk cap |
| XAUUSD | Pakai metadata dan kalkulasi MT5, bukan pip EURUSD |
| Margin calculation gagal | Reject dan jangan tampilkan approved volume |

## Referensi implementasi resmi

- [MQL5 `OrderCalcProfit`](https://www.mql5.com/en/docs/trading/ordercalcprofit)
- [MQL5 `OrderCalcMargin`](https://www.mql5.com/en/docs/trading/ordercalcmargin)
- [MQL5 symbol properties](https://www.mql5.com/en/docs/constants/environment_state/marketinfoconstants)
