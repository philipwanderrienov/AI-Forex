# Fase 00 — Data Dictionary dan Kontrak JSON

## Status

- Versi kontrak: `v1-draft`
- Berlaku untuk Technical MVP.
- Dokumen ini menjadi sumber canonical untuk backend .NET, EA MQL5, Python bridge, database, API, dan Angular.
- Contoh harga, skor, dan hasil di dokumen hanya fixture struktur, bukan rekomendasi trading.

## 1. Konvensi umum

| Konvensi | Keputusan |
|---|---|
| ID | ULID string, sortable berdasarkan waktu, kecuali ID asli provider/broker |
| Timestamp | UTC ISO-8601 dengan suffix `Z`, misalnya `2026-08-17T08:15:04.123Z` |
| Timezone tampilan | IANA zone ID, terutama `Europe/London` dan `Asia/Jakarta` |
| Harga/money pada JSON | Decimal dikirim sebagai string agar precision tidak hilang |
| Score | Number dalam `[-10, 10]` |
| Confidence | Integer `0–100`; evidence strength, bukan win probability |
| Persentase | Decimal percent, contoh `0.5` berarti 0,5%, bukan 50% |
| Simbol canonical | Uppercase tanpa separator: `EURUSD`, `GBPUSD`, `EURGBP`, `EURCHF`, `XAUUSD` |
| Null | Hanya diizinkan bila tabel menyatakan nullable; field wajib tidak boleh hilang diam-diam |
| Versioning | Setiap payload mempunyai `schemaVersion`; formula/policy mempunyai version tersendiri |
| Audit | Data yang menghasilkan signal/setup/risk decision bersifat immutable; koreksi membuat versi/record baru |

### Enum canonical

```text
InstrumentType     = FOREX | PRECIOUS_METAL
Timeframe          = M15 | H1 | H4
CandleStatus       = PARTIAL | FINAL
Trend              = BULLISH | BEARISH | SIDEWAYS | UNKNOWN
MarketRegime       = TRENDING | RANGING | HIGH_VOLATILITY | LOW_LIQUIDITY | UNKNOWN
OpportunityDirection = LONG_CANDIDATE | SHORT_CANDIDATE | NO_OPPORTUNITY
PositionAction     = OPEN_LONG | OPEN_SHORT | CLOSE_LONG | CLOSE_SHORT | REDUCE | HOLD | SKIP
RiskDecision       = APPROVED | REDUCED | REJECTED
DataQuality        = GOOD | DEGRADED | STALE | INSUFFICIENT
AccountFreshness   = GOOD | WARNING | STALE | UNAVAILABLE
Severity           = INFO | WARNING | BLOCKING
NotificationStatus = UNREAD | READ | EXPIRED | DISMISSED
ExecutionStatus    = PLANNED | USER_REPORTED | FILLED | PARTIALLY_FILLED | CLOSED | CANCELLED
Importance         = LOW | MEDIUM | HIGH | UNKNOWN
TradeSetupStatus   = ACTIVE | EXPIRED | INVALIDATED
NewsImpactStatus   = CLASSIFIED | UNCLASSIFIED | REJECTED
NotificationType  = TRADE_SETUP | DATA_WARNING | RISK_WARNING | SYSTEM
ExitReason         = SL | TP | MANUAL | INVALIDATION | OTHER
```

`LONG_CANDIDATE/SHORT_CANDIDATE` adalah arah opportunity baru. Keduanya tidak sama dengan `CLOSE_SHORT/CLOSE_LONG`. Reversal selalu dicatat sebagai dua tindakan terpisah.

## 2. TradingInstrument

| Field | Type | Wajib | Aturan |
|---|---|---:|---|
| `symbol` | string | Ya | Salah satu universe canonical MVP |
| `instrumentType` | enum | Ya | `FOREX` atau `PRECIOUS_METAL` |
| `baseAsset` | string | Ya | `EUR`, `GBP`, atau `XAU` sesuai simbol |
| `quoteCurrency` | string | Ya | ISO-4217, misalnya `USD`, `GBP`, `CHF` |
| `brokerSymbol` | string | Ya | Simbol nyata MT5, dapat memiliki prefix/suffix |
| `brokerServerAlias` | string | Ya | Alias aman; bukan account number |
| `digits` | integer | Ya | Precision broker, `>= 0` |
| `point` | decimal string | Ya | Nilai point broker, `> 0` |
| `tickSize` | decimal string | Ya | Perubahan harga minimum, `> 0` |
| `tickValue` | decimal string/null | Tidak | Nilai tick dalam account currency bila tersedia |
| `contractSize` | decimal string | Ya | Contract size broker, `> 0` |
| `volumeMin/Max/Step` | decimal string | Ya | Harus konsisten dan `step > 0` |
| `enabled` | boolean | Ya | Hanya enabled instrument masuk scanner |
| `asOf` | timestamp | Ya | Waktu metadata dibaca dari MT5 |

```json
{
  "schemaVersion": "trading-instrument.v1",
  "symbol": "XAUUSD",
  "instrumentType": "PRECIOUS_METAL",
  "baseAsset": "XAU",
  "quoteCurrency": "USD",
  "brokerSymbol": "XAUUSDm",
  "brokerServerAlias": "primary-demo",
  "digits": 2,
  "point": "0.01",
  "tickSize": "0.01",
  "tickValue": "1.00",
  "contractSize": "100",
  "volumeMin": "0.01",
  "volumeMax": "100.00",
  "volumeStep": "0.01",
  "enabled": true,
  "asOf": "2026-08-17T08:15:00Z"
}
```

## 3. Candle

| Field | Type | Wajib | Aturan |
|---|---|---:|---|
| `candleId` | ULID | Ya | Immutable untuk source/instrument/timeframe/openTime |
| `source` | string | Ya | `MT5` pada MVP |
| `brokerServerAlias` | string | Ya | Alias aman |
| `brokerSymbol` | string | Ya | Simbol asli MT5 |
| `instrument` | string | Ya | Simbol canonical |
| `timeframe` | enum | Ya | `M15/H1/H4` |
| `openTime` | timestamp | Ya | Awal interval, inclusive |
| `closeTime` | timestamp | Ya | Akhir interval, exclusive; harus sesuai timeframe |
| `open/high/low/close` | decimal string | Ya | Positive; invariants OHLC berlaku |
| `tickVolume` | integer | Ya | `>= 0`; bukan volume global |
| `realVolume` | decimal string/null | Tidak | Null jika broker tidak menyediakan |
| `spreadPoints` | integer/null | Tidak | Spread candle dari broker bila tersedia |
| `status` | enum | Ya | Hanya `FINAL` boleh masuk scoring |
| `receivedAt` | timestamp | Ya | Waktu bridge menerima data |
| `ingestedAt` | timestamp | Ya | Waktu backend menerima data |
| `dataQuality` | enum | Ya | Status kualitas record |

Invariants:

```text
high >= max(open, close)
low  <= min(open, close)
high >= low
closeTime > openTime
FINAL hanya jika closeTime <= verified server time
unique(source, brokerServerAlias, instrument, timeframe, openTime)
```

```json
{
  "schemaVersion": "candle.v1",
  "candleId": "01J5J4J6A8F2K9XH1M7S4P3Q2R",
  "source": "MT5",
  "brokerServerAlias": "primary-demo",
  "brokerSymbol": "EURUSD.a",
  "instrument": "EURUSD",
  "timeframe": "H1",
  "openTime": "2026-08-17T07:00:00Z",
  "closeTime": "2026-08-17T08:00:00Z",
  "open": "1.17010",
  "high": "1.17220",
  "low": "1.16980",
  "close": "1.17160",
  "tickVolume": 1842,
  "realVolume": null,
  "spreadPoints": 9,
  "status": "FINAL",
  "receivedAt": "2026-08-17T08:00:01.120Z",
  "ingestedAt": "2026-08-17T08:00:01.240Z",
  "dataQuality": "GOOD"
}
```

## 4. AccountSnapshot

| Field | Type | Wajib | Aturan |
|---|---|---:|---|
| `accountSnapshotId` | ULID | Ya | Referensi immutable untuk risk/audit |
| `source` | string | Ya | `MT5` |
| `brokerServerAlias` | string | Ya | Tidak mengandung account number |
| `accountCurrency` | string | Ya | ISO-4217 |
| `balance` | decimal string | Ya | Nilai MT5 |
| `equity` | decimal string | Ya | Nilai MT5 yang dipakai sizing |
| `floatingPnl` | decimal string | Ya | `ACCOUNT_PROFIT` |
| `realizedPnlToday` | decimal string/null | Tidak | Agregasi deal history; null bila belum tersedia |
| `realizedDayZone` | string/null | Tidak | IANA zone untuk definisi pergantian hari |
| `usedMargin/freeMargin` | decimal string | Ya | Nilai MT5 |
| `marginLevelPercent` | decimal string/null | Tidak | Null jika tidak relevan/tidak tersedia |
| `asOf` | timestamp | Ya | Event time dari terminal |
| `receivedAt` | timestamp | Ya | Waktu bridge menerima/membentuk snapshot |
| `freshness` | enum | Ya | `GOOD/WARNING/STALE/UNAVAILABLE` berdasarkan usia snapshot dan status terminal |

```json
{
  "schemaVersion": "account-snapshot.v1",
  "accountSnapshotId": "01J5J4MYYP4DG6E2NZ7VYJ0H2Q",
  "source": "MT5",
  "brokerServerAlias": "primary-demo",
  "accountCurrency": "USD",
  "balance": "10000.00",
  "equity": "9950.00",
  "floatingPnl": "-50.00",
  "realizedPnlToday": "125.00",
  "realizedDayZone": "Europe/London",
  "usedMargin": "300.00",
  "freeMargin": "9650.00",
  "marginLevelPercent": "3316.67",
  "asOf": "2026-08-17T08:15:04Z",
  "receivedAt": "2026-08-17T08:15:04.180Z",
  "freshness": "GOOD"
}
```

## 5. TechnicalSnapshot

| Field | Type | Wajib | Aturan |
|---|---|---:|---|
| `technicalSnapshotId` | ULID | Ya | Immutable |
| `instrument/timeframe` | string/enum | Ya | Canonical |
| `calculatedAt` | timestamp | Ya | UTC |
| `candleCutoff` | timestamp | Ya | Candle setelah cutoff tidak boleh digunakan |
| `lookbackCandles` | integer | Ya | Jumlah candle valid yang digunakan |
| `trend` | enum | Ya | Canonical |
| `indicatorValues` | object | Ya | Nilai indikator dengan unit/parameter |
| `subScores` | object | Ya | Semua komponen dalam `[-10,10]` |
| `technicalScore` | number | Ya | Weighted result `[-10,10]` |
| `dataQuality` | enum | Ya | `STALE/INSUFFICIENT` tidak boleh menjadi active signal |
| `evidence` | array | Ya | Kode, pesan, nilai, contribution |
| `formulaVersion` | string | Ya | Misalnya `technical-v1` |

```json
{
  "schemaVersion": "technical-snapshot.v1",
  "technicalSnapshotId": "01J5J4RBDCDM2H0WMB9XQPAN7T",
  "instrument": "EURUSD",
  "timeframe": "H1",
  "calculatedAt": "2026-08-17T08:00:02Z",
  "candleCutoff": "2026-08-17T08:00:00Z",
  "lookbackCandles": 250,
  "trend": "BULLISH",
  "indicatorValues": {
    "ema20": "1.17080",
    "ema50": "1.16940",
    "ema200": "1.16510",
    "rsi14": 61.2,
    "atr14": "0.00125",
    "macdHistogram": "0.00018"
  },
  "subScores": {
    "emaTrend": 7.0,
    "marketStructure": 6.0,
    "momentum": 4.5,
    "supportResistanceContext": 3.0,
    "volatilitySetup": 5.0
  },
  "technicalScore": 5.7,
  "dataQuality": "GOOD",
  "evidence": [
    {"code": "EMA_BULL_STACK", "message": "EMA20 > EMA50 > EMA200", "contribution": 2.1}
  ],
  "formulaVersion": "technical-v1"
}
```

## 6. EconomicEvent

| Field | Type | Wajib | Aturan |
|---|---|---:|---|
| `economicEventId` | ULID | Ya | Internal immutable ID |
| `provider/providerEventId` | string | Ya | Source attribution dan deduplication |
| `country/currencies` | string/array | Ya | Currency dapat lebih dari satu |
| `title/category` | string | Ya | Normalized |
| `importance` | enum | Ya | `LOW/MEDIUM/HIGH/UNKNOWN` |
| `scheduledAt` | timestamp | Ya | Jadwal UTC |
| `publishedAt/receivedAt` | timestamp/null | Tidak | Null sebelum rilis |
| `actual/forecast/previous` | decimal string/null | Tidak | Unit harus eksplisit |
| `unit` | string/null | Tidak | `%`, `index`, `count`, dll. |
| `revision` | integer | Ya | Mulai 0 |
| `sourceUrl` | string/null | Tidak | Attribution bila diizinkan |

```json
{
  "schemaVersion": "economic-event.v1",
  "economicEventId": "01J5J4V8SHR9B5A7Z6C0M3P2QF",
  "provider": "FMP",
  "providerEventId": "provider-event-123",
  "country": "GB",
  "currencies": ["GBP"],
  "title": "Consumer Price Index",
  "category": "INFLATION",
  "importance": "HIGH",
  "scheduledAt": "2026-08-19T06:00:00Z",
  "publishedAt": null,
  "receivedAt": "2026-08-17T08:10:00Z",
  "actual": null,
  "forecast": "2.3",
  "previous": "2.1",
  "unit": "% YoY",
  "revision": 0,
  "sourceUrl": null
}
```

## 7. NewsImpact

| Field | Type | Wajib | Aturan |
|---|---|---:|---|
| `newsImpactId/newsArticleId` | ULID | Ya | Traceable ke artikel normalized |
| `affectedAssets` | array | Ya | Currency/instrument canonical |
| `category/sentiment/impact/direction/duration` | enum | Ya | Schema-constrained |
| `confidence` | integer | Ya | Model evidence confidence |
| `evidence` | array | Ya | Kutipan pendek/field input yang mendukung |
| `model/promptVersion` | string | Ya | Audit OpenAI |
| `classifiedAt` | timestamp | Ya | UTC |
| `status` | enum | Ya | `CLASSIFIED/UNCLASSIFIED/REJECTED` |

```json
{
  "schemaVersion": "news-impact.v1",
  "newsImpactId": "01J5J50MMPJWJY12GFA4YQBT16",
  "newsArticleId": "01J5J50HVSXX0Y7JR2Y3EER8TR",
  "affectedAssets": ["GBP", "GBPUSD", "EURGBP"],
  "category": "CENTRAL_BANK",
  "sentiment": "NEGATIVE",
  "impact": "HIGH",
  "direction": "GBP_BEARISH",
  "duration": "INTRADAY",
  "confidence": 78,
  "evidence": ["Policy statement was more dovish than prior guidance"],
  "model": "configured-openai-model",
  "promptVersion": "news-classifier-v1",
  "classifiedAt": "2026-08-17T08:12:00Z",
  "status": "CLASSIFIED"
}
```

## 8. TradeSignal

| Field | Type | Wajib | Aturan |
|---|---|---:|---|
| `tradeSignalId` | ULID | Ya | Immutable |
| `instrument` | string | Ya | Canonical |
| `direction` | enum | Ya | Candidate direction, bukan position action |
| `combinedScore` | number | Ya | `[-10,10]` |
| `confidence` | integer | Ya | `0–100` |
| `dataQuality` | enum | Ya | Bad quality memaksa no opportunity |
| `timeframeScores` | object | Ya | M15/H1/H4 |
| `componentScores` | object | Ya | FX/XAU mengikuti formula berbeda |
| `technicalSnapshotIds` | array | Ya | Satu per timeframe |
| `blockingReasons` | array | Ya | Kosong jika tidak ada blocker |
| `generatedAt/expiresAt` | timestamp | Ya | `expiresAt > generatedAt` |
| `formulaVersion` | string | Ya | `score-v1-fx` atau `score-v1-xau` |

```json
{
  "schemaVersion": "trade-signal.v1",
  "tradeSignalId": "01J5J54Q0E4RZ9JWGFS1S8433K",
  "instrument": "EURUSD",
  "direction": "LONG_CANDIDATE",
  "combinedScore": 6.4,
  "confidence": 74,
  "dataQuality": "GOOD",
  "timeframeScores": {"M15": 4.5, "H1": 6.2, "H4": 7.0},
  "componentScores": {"technical": 5.9, "currencyStrengthDifferential": 7.0, "regimeFit": 6.5},
  "technicalSnapshotIds": ["01...M15", "01...H1", "01...H4"],
  "blockingReasons": [],
  "generatedAt": "2026-08-17T08:15:03Z",
  "expiresAt": "2026-08-17T09:00:00Z",
  "formulaVersion": "score-v1-fx"
}
```

## 9. TradeSetup

| Field | Type | Wajib | Aturan |
|---|---|---:|---|
| `tradeSetupId/tradeSignalId` | ULID | Ya | One setup references one signal version |
| `instrument/direction` | string/enum | Ya | Harus sama dengan signal |
| `entryZoneMin/Max` | decimal string | Ya | `min <= max` |
| `invalidationPrice` | decimal string | Ya | Alasan harus ada |
| `stopLoss/takeProfit` | decimal string | Ya | Arah dan urutan harga valid |
| `riskReward` | decimal number | Ya | Minimum policy dipenuhi sebelum approval |
| `createdAt/expiresAt` | timestamp | Ya | London window/TTL diperiksa |
| `evidenceSummary` | array | Ya | Human-readable tetapi source-grounded |
| `status` | enum | Ya | `ACTIVE/EXPIRED/INVALIDATED` |

```json
{
  "schemaVersion": "trade-setup.v1",
  "tradeSetupId": "01J5J58CDE5AV65ZCGF3Z9N6BX",
  "tradeSignalId": "01J5J54Q0E4RZ9JWGFS1S8433K",
  "instrument": "EURUSD",
  "direction": "LONG_CANDIDATE",
  "entryZoneMin": "1.17120",
  "entryZoneMax": "1.17160",
  "invalidationPrice": "1.16880",
  "stopLoss": "1.16880",
  "takeProfit": "1.17720",
  "riskReward": 2.0,
  "createdAt": "2026-08-17T08:15:04Z",
  "expiresAt": "2026-08-17T09:00:00Z",
  "evidenceSummary": ["H1 dan H4 bullish", "EMA bullish stack"],
  "status": "ACTIVE"
}
```

## 10. RiskAssessment

| Field | Type | Wajib | Aturan |
|---|---|---:|---|
| `riskAssessmentId/tradeSetupId` | ULID | Ya | Immutable assessment |
| `decision` | enum | Ya | `APPROVED/REDUCED/REJECTED` |
| `accountSnapshotId` | ULID/null | Kondisional | Wajib untuk active sizing |
| `equity/accountCurrency` | decimal string/string | Kondisional | Harus sama dengan account snapshot |
| `riskPercent/riskAmount` | decimal | Kondisional | Wajib jika approved/reduced |
| `suggestedVolume` | decimal string/null | Tidak | Null bila input stale/incomplete |
| `volumeUnit` | string/null | Tidak | `LOT` pada MT5 |
| `stopLoss/takeProfit` | decimal string | Ya | Diambil dari setup |
| `riskReward` | decimal number | Ya | Diambil dari setup/policy |
| `warnings/blockingReasons` | array | Ya | Blocking reason wajib untuk rejected |
| `policyVersion` | string | Ya | Versioned |
| `assessedAt` | timestamp | Ya | UTC |

```json
{
  "schemaVersion": "risk-assessment.v1",
  "riskAssessmentId": "01J5J5CZ27QTCD09QEA4ABG6GD",
  "tradeSetupId": "01J5J58CDE5AV65ZCGF3Z9N6BX",
  "decision": "APPROVED",
  "accountSnapshotId": "01J5J4MYYP4DG6E2NZ7VYJ0H2Q",
  "equity": "9950.00",
  "accountCurrency": "USD",
  "riskPercent": 0.5,
  "riskAmount": "49.75",
  "suggestedVolume": "0.10",
  "volumeUnit": "LOT",
  "stopLoss": "1.16880",
  "takeProfit": "1.17720",
  "riskReward": 2.0,
  "warnings": [],
  "blockingReasons": [],
  "policyVersion": "risk-v1",
  "assessedAt": "2026-08-17T08:15:04.400Z"
}
```

## 11. TradeDecision

| Field | Type | Wajib | Aturan |
|---|---|---:|---|
| `tradeDecisionId` | ULID | Ya | Append-only |
| `userId` | ULID | Ya | Actor |
| `tradeSetupId/riskAssessmentId` | ULID | Ya | Versi yang dilihat pengguna |
| `action` | enum | Ya | Position action, bukan candidate direction |
| `executionStatus` | enum | Ya | Awal `PLANNED` atau `USER_REPORTED` |
| `decidedAt` | timestamp | Ya | Timestamp backend |
| `displayTimezone` | string | Ya | IANA zone yang dilihat pengguna |
| `marketPriceAtDecision` | decimal string | Ya | Latest price saat pencatatan |
| `marketPriceAsOf` | timestamp | Ya | Waktu harga yang dicatat |
| `reportedEntry/volume/sl/tp` | decimal string/null | Tidak | Input manual |
| `metatraderTicket` | string/null | Tidak | Treat as sensitive; bukan credential |
| `reason/note` | string/null | Tidak | Sanitized length limit |

```json
{
  "schemaVersion": "trade-decision.v1",
  "tradeDecisionId": "01J5J5H1K44JZ4G6VVGX0MGPXE",
  "userId": "01J5USER000000000000000000",
  "tradeSetupId": "01J5J58CDE5AV65ZCGF3Z9N6BX",
  "riskAssessmentId": "01J5J5CZ27QTCD09QEA4ABG6GD",
  "action": "OPEN_LONG",
  "executionStatus": "USER_REPORTED",
  "decidedAt": "2026-08-17T08:18:10Z",
  "displayTimezone": "Asia/Jakarta",
  "marketPriceAtDecision": "1.17145",
  "marketPriceAsOf": "2026-08-17T08:18:09.700Z",
  "reportedEntry": "1.17150",
  "reportedVolume": "0.10",
  "reportedStopLoss": "1.16880",
  "reportedTakeProfit": "1.17720",
  "metatraderTicket": "masked-or-user-entered",
  "reason": null,
  "note": "Entry dicatat setelah eksekusi manual di MT5"
}
```

## 12. TradeOutcome

| Field | Type | Wajib | Aturan |
|---|---|---:|---|
| `tradeOutcomeId/tradeDecisionId` | ULID | Ya | Traceable ke setup asli |
| `openedAt/closedAt` | timestamp | Ya | `closedAt >= openedAt` |
| `averageEntry/averageExit` | decimal string | Ya | User-reported pada MVP |
| `initialVolume/closedVolume` | decimal string | Ya | Volume konsisten |
| `grossPnl/commission/swap/fees/netPnl` | decimal string | Ya | Dalam account currency |
| `accountCurrency` | string | Ya | ISO-4217; currency seluruh nilai P/L |
| `resultR` | decimal number | Ya | Net result / initial risk amount |
| `exitReason` | enum | Ya | `SL/TP/MANUAL/INVALIDATION/OTHER` |
| `notes/tags` | string/array | Tidak | Sanitized |
| `recordedAt` | timestamp | Ya | Backend timestamp |

```json
{
  "schemaVersion": "trade-outcome.v1",
  "tradeOutcomeId": "01J5J5NQ1NQFEVKP5EMDG2Y3A2",
  "tradeDecisionId": "01J5J5H1K44JZ4G6VVGX0MGPXE",
  "openedAt": "2026-08-17T08:18:00Z",
  "closedAt": "2026-08-17T11:42:00Z",
  "averageEntry": "1.17150",
  "averageExit": "1.17690",
  "initialVolume": "0.10",
  "closedVolume": "0.10",
  "grossPnl": "54.00",
  "commission": "-1.20",
  "swap": "0.00",
  "fees": "0.00",
  "netPnl": "52.80",
  "accountCurrency": "USD",
  "resultR": 1.06,
  "exitReason": "MANUAL",
  "notes": "Closed before London window ended",
  "tags": ["london", "trend"],
  "recordedAt": "2026-08-17T11:43:00Z"
}
```

## 13. Notification

| Field | Type | Wajib | Aturan |
|---|---|---:|---|
| `notificationId` | ULID | Ya | Internal |
| `type` | enum | Ya | `TRADE_SETUP/DATA_WARNING/RISK_WARNING/SYSTEM` |
| `severity` | enum | Ya | Canonical |
| `tradeSetupId/riskAssessmentId` | ULID/null | Tidak | Wajib untuk trade setup notification |
| `title/message` | string | Ya | Tidak boleh mengarang fakta |
| `createdAt/expiresAt` | timestamp | Ya | Expiry wajib |
| `status` | enum | Ya | Canonical |
| `deduplicationKey` | string | Ya | Unique selama notification aktif |
| `dataAsOf` | timestamp | Ya | Freshness terlihat |

```json
{
  "schemaVersion": "notification.v1",
  "notificationId": "01J5J5T3YHXA0BPYNZD32BGCFF",
  "type": "TRADE_SETUP",
  "severity": "INFO",
  "tradeSetupId": "01J5J58CDE5AV65ZCGF3Z9N6BX",
  "riskAssessmentId": "01J5J5CZ27QTCD09QEA4ABG6GD",
  "title": "EURUSD long candidate",
  "message": "Score 6.4, evidence confidence 74, risk approved.",
  "createdAt": "2026-08-17T08:15:05Z",
  "expiresAt": "2026-08-17T09:00:00Z",
  "status": "UNREAD",
  "deduplicationKey": "EURUSD:LONG_CANDIDATE:score-v1-fx:20260817T0815",
  "dataAsOf": "2026-08-17T08:15:00Z"
}
```

## 14. MT5 bridge envelope

Envelope digunakan untuk `EA MQL5 → Python bridge` dan `Python bridge → .NET ingestion`.

| Field | Type | Wajib | Aturan |
|---|---|---:|---|
| `schemaVersion` | string | Ya | `mt5-envelope.v1` |
| `batchId` | ULID | Ya | Idempotency key utama |
| `sourceInstanceId` | string | Ya | Random/configured instance ID, bukan account number |
| `brokerServerAlias` | string | Ya | Alias aman |
| `sequence` | integer | Ya | Monotonically increasing per instance |
| `sentAt` | timestamp | Ya | UTC |
| `payloadType` | enum | Ya | `TICKS/CANDLES/ACCOUNT_SNAPSHOT/HEARTBEAT` |
| `records` | array | Ya | Bounded batch; schema mengikuti type |
| `checksum` | string | Ya | Integrity/deduplication, bukan pengganti TLS/auth |

```json
{
  "schemaVersion": "mt5-envelope.v1",
  "batchId": "01J5J5Y22B8NKZ4M6KW7MPNN6C",
  "sourceInstanceId": "mac-mt5-primary",
  "brokerServerAlias": "primary-demo",
  "sequence": 18442,
  "sentAt": "2026-08-17T08:15:04.200Z",
  "payloadType": "ACCOUNT_SNAPSHOT",
  "records": [
    {
      "accountCurrency": "USD",
      "balance": "10000.00",
      "equity": "9950.00",
      "floatingPnl": "-50.00",
      "usedMargin": "300.00",
      "freeMargin": "9650.00",
      "marginLevelPercent": "3316.67",
      "eventTime": "2026-08-17T08:15:04Z"
    }
  ],
  "checksum": "sha256:example-only"
}
```

## 15. Contract-level validation

- Unknown enum value ditolak atau diarahkan ke explicit compatibility handling; tidak dipetakan diam-diam.
- Unknown field boleh diabaikan hanya untuk backward-compatible reader; field wajib yang hilang selalu error.
- Payload invalid masuk quarantine/dead-letter dengan error code dan hash payload, tanpa menyimpan secret.
- API error menggunakan Problem Details dan correlation ID.
- Setiap contract test mempunyai minimal satu valid fixture, missing-required-field fixture, invalid-enum fixture, invalid-decimal fixture, dan boundary-time fixture.
- Kontrak baru harus backward compatible dalam major version yang sama; breaking change menaikkan major schema version.
