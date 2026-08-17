# Fase 00 — Discovery dan Spesifikasi

## Status dokumen

- Versi: `0.1-draft`
- Tanggal keputusan awal: 17 Agustus 2026
- Status: cukup untuk memulai spike teknis, belum dianggap final sampai seluruh keputusan terbuka dan contoh validasi di bagian akhir diselesaikan.
- Pemilik produk dan pengguna MVP: satu pengguna pribadi yang melakukan eksekusi manual di MetaTrader.

## Tujuan

Mengubah visi arsitektur menjadi definisi produk dan aturan bisnis yang tidak ambigu. Fase ini mencegah setiap modul menggunakan arti pair, waktu, skor, dan sinyal yang berbeda.

> Aplikasi adalah alat analisis dan decision-support, bukan penasihat keuangan dan bukan jaminan profit. Pemilihan pair atau confidence yang tinggi tidak sama dengan probabilitas kemenangan. Semua aturan harus dibuktikan dengan backtest dan forward test sebelum dipercaya.

## 1. Scope produk MVP

### 1.1 Pengguna dan batas tanggung jawab

- Pengguna utama adalah pemilik aplikasi yang melakukan daily/intraday trading secara manual melalui MetaTrader.
- Aplikasi mengumpulkan data, menganalisis, memberi notifikasi, menyarankan setup, dan mencatat keputusan pengguna.
- EA MQL5 read-only membaca market data dari terminal MetaTrader 5 yang sudah login dan mengirimkannya ke Python bridge native macOS. Aplikasi **tidak** mengirim order, memodifikasi order, atau menutup posisi.
- Tombol `BUY` dan `SELL` di aplikasi hanya mencatat tindakan yang telah/akan dilakukan pengguna di MetaTrader. Label UI wajib berbunyi `Catat BUY` dan `Catat SELL` agar tidak dianggap sebagai eksekusi broker.
- Tombol `WAIT/SKIP` tersedia untuk mencatat bahwa suatu saran dilewati.

### 1.2 Universe instrumen dan timeframe

Instrumen canonical MVP:

| Prioritas | Instrumen | Jenis | Alasan awal | Risiko/keterangan |
|---|---|---|---|---|
| 1 | `EURUSD` | Forex | Likuid dan aktif ketika London/Eropa buka | Tetap sensitif terhadap data dan kebijakan AS |
| 2 | `GBPUSD` | Forex | GBP mempunyai hubungan langsung dengan sesi London | Volatilitas/lonjakan spread biasanya lebih tinggi dari EURUSD |
| 3 | `EURGBP` | Forex cross | Merepresentasikan hubungan EUR–GBP selama jam Eropa | Range dapat sempit; biaya spread harus diperhatikan |
| 4 | `EURCHF` | Forex cross | Mata uang Eropa dan relevan pada jam London | Dapat berlikuiditas lebih rendah dan sensitif terhadap kebijakan SNB |
| 5 | `XAUUSD` | Precious metal | London adalah pusat penting pasar emas OTC dan benchmark AM berada dalam window | Bukan currency pair; contract size, tick value, spread, dan volatilitas memerlukan aturan khusus |

Daftar ini dipilih karena relevansi sesi London, **bukan** karena instrumen tertentu otomatis mempunyai win rate lebih tinggi. Universe terdiri dari empat forex pair dan satu precious metal. Risiko USD pada `EURUSD`, `GBPUSD`, dan `XAUUSD`, serta korelasi EUR pada `EURUSD`, `EURGBP`, dan `EURCHF`, harus dihitung sebagai exposure yang saling terkait.

Timeframe canonical MVP:

- `H4`: menentukan regime dan arah konteks utama.
- `H1`: timeframe keputusan utama dan pembentukan setup.
- `M15`: timing entry/confirmation.
- `M5` dan timeframe lain tidak masuk MVP untuk mengurangi noise dan beban data.
- Hanya candle dengan status `FINAL` yang boleh digunakan dalam scoring. Candle yang masih berjalan boleh ditampilkan, tetapi tidak boleh mengubah rekomendasi final.

### 1.3 Jam operasi

- Ingestion berjalan selama terminal MT5 dan koneksi broker tersedia, dari pembukaan minggu hingga penutupan minggu menurut tick/status simbol broker.
- Scanner aktif 24 jam ketika terminal dan feed broker sehat serta simbol dapat diperdagangkan, tetapi notifikasi entry hanya aktif pada sesi likuid yang dikonfigurasi.
- Default tampilan menggunakan `Asia/Jakarta`; penyimpanan dan kontrak API selalu UTC.
- Window notifikasi MVP adalah `08:00–12:59 Europe/London`, sebelum overlap reguler London–New York. Dalam waktu Jakarta (`GMT+07:00`), kira-kira `14:00–18:59` ketika London `GMT+01:00` dan `15:00–19:59` ketika London `GMT+00:00`; aplikasi wajib menghitung DST, bukan memakai offset tetap.
- Scanner dan ingestion tetap berjalan di luar window untuk menjaga histori/freshness, tetapi tidak menerbitkan notifikasi entry baru.
- Tidak ada notifikasi entry baru ketika pasar tutup, spread abnormal, data stale, atau berada dalam embargo berita high-impact.

### 1.4 Kebutuhan real-time dan freshness

MVP bukan sistem high-frequency trading. Target berikut adalah target produk awal dan harus diukur saat burn-in:

| Data/proses | Sehat | Warning | Blokir rekomendasi baru |
|---|---:|---:|---:|
| Usia harga streaming saat pasar buka | `<= 5 detik` | `> 5 detik` | `> 15 detik` |
| Heartbeat terminal/MT5 bridge | `<= 10 detik` | `> 10 detik` | `> 20 detik` |
| Candle final tersedia setelah batas candle | `<= 30 detik` | `> 30 detik` | `> 2 menit` |
| Satu siklus scanner untuk 5 instrumen × 3 timeframe | `<= 5 detik` | `> 5 detik` | hasil lama tidak dipublikasikan setelah `15 detik` |
| API dashboard p95 | `<= 500 ms` | `> 500 ms` | alarm jika p95 `> 2 detik` selama 5 menit |
| Notifikasi setelah setup lolos seluruh rule | `<= 5 detik` | `> 5 detik` | tandai expired sesuai TTL setup |

Weekend dan penutupan pasar menurut broker tidak dianggap stale. Statusnya `MARKET_CLOSED` dan tidak memicu alert operasional.

### 1.5 Fitur MVP

Fitur yang masuk MVP:

1. Dashboard status pasar, terminal MT5, koneksi broker, Python bridge, freshness, dan jam sesi.
2. Scanner lima instrumen dan tiga timeframe.
3. Notifikasi berjalan/in-app untuk setup yang baru lolos rule.
4. Isi notifikasi: instrumen, arah peluang `LONG_CANDIDATE/SHORT_CANDIDATE`, waktu terbentuk, waktu kedaluwarsa, entry zone, SL, TP, risk/reward, confidence, alasan utama, warning, dan ukuran posisi maksimum yang disarankan. Kondisi tanpa peluang tidak mengirim notifikasi entry.
5. Detail pair: candle, histori, bid/ask, spread, tick volume broker, timestamp, indikator, score breakdown, dan kualitas data.
6. Trade setup dengan tombol `Catat BUY`, `Catat SELL`, dan `Catat SKIP/WAIT`.
7. Audit/trade journal untuk menghubungkan saran aplikasi dengan tindakan manual di MetaTrader.
8. Autentikasi satu pengguna dengan JWT access token dan refresh-token rotation.
9. Header global menampilkan jam dan tanggal real-time London dan Jakarta dalam format offset GMT serta status window notifikasi London.
10. Header/account widget menampilkan telemetry read-only dari MT5: balance, equity, floating P/L, realized P/L hari ini, used margin, free margin, margin level, dan account currency, lengkap dengan `asOf` serta freshness status.

`Ukuran posisi maksimum` bukan angka lot statis. Nilainya dihitung Risk Engine dari equity yang dimasukkan pengguna, persentase risiko, entry, stop-loss, nilai pip, mata uang akun, dan batas broker. Default risiko awal adalah `0,5%` equity per trade; hard maximum MVP `1%`. Jika equity atau parameter broker tidak tersedia, aplikasi hanya menampilkan `N/A`, bukan menebak lot.

Aturan numerik lengkap untuk stop-loss, target, lot, margin, exposure, dan circuit breaker berada di [Tabel Aturan Risk Engine v1](00-risk-rules-v1.md).

Fitur yang tidak masuk MVP:

- Eksekusi atau sinkronisasi order otomatis dengan MetaTrader.
- Multi-user, social trading, copy trading, dan mobile push notification.
- Instrumen di luar lima instrumen canonical.
- Machine-learning prediction dan AI sebagai penentu arah.
- News sentiment penuh; MVP hanya membutuhkan perlindungan jadwal event ekonomi jika provider lolos spike.
- Klaim atau optimisasi berdasarkan win rate sebelum backtest tersedia.

### 1.6 Alur utama pengguna

```text
Login → lihat status data/sesi → buka scanner → terima/pilih notifikasi
→ periksa evidence dan risk assessment → eksekusi manual di MetaTrader atau lewati
→ tekan Catat BUY/SELL/SKIP → isi harga/lot/ticket MetaTrader opsional
→ simpan audit trail → lengkapi outcome setelah posisi ditutup
```

### 1.7 Market clock pada header

- Header selalu menampilkan dua clock: `London` (zone ID `Europe/London`) dan `Jakarta` (zone ID `Asia/Jakarta`).
- Format awal: `EEE, dd MMM yyyy HH:mm:ss 'GMT'xxx`, misalnya `Mon, 17 Aug 2026 09:15:04 GMT+01:00` dan `Mon, 17 Aug 2026 15:15:04 GMT+07:00`.
- Kedua clock berasal dari instant UTC yang sama; timezone hanya mengubah cara tampil.
- London wajib mengikuti daylight-saving time secara otomatis: `GMT+00:00` saat winter dan `GMT+01:00` saat BST. Jangan memaksa London menjadi GMT+0 sepanjang tahun.
- Jakarta selalu ditampilkan sebagai `GMT+07:00` tanpa DST.
- Tampilkan status `LONDON WINDOW ACTIVE` ketika waktu London berada pada hari kerja pukul `08:00:00–12:59:59`; selain itu tampilkan `CLOSED`. Status market/broker tetap indikator terpisah karena hari libur atau broker disconnected tidak dapat disimpulkan hanya dari jam.
- Clock berjalan lokal di browser setiap detik tanpa request API per detik, lalu disinkronkan dengan UTC server saat aplikasi dibuka, reconnect, browser kembali aktif, dan secara berkala.
- Jika selisih clock browser terhadap server melebihi 2 detik, tampilkan warning `DEVICE_CLOCK_DRIFT` dan gunakan server-offset untuk rendering.
- Semua event bisnis tetap memakai timestamp UTC dari backend; header clock tidak menjadi sumber timestamp audit atau scoring.

### 1.8 Account telemetry MT5

- EA boleh membaca properti account secara read-only: `ACCOUNT_BALANCE`, `ACCOUNT_EQUITY`, `ACCOUNT_PROFIT`, `ACCOUNT_MARGIN`, `ACCOUNT_MARGIN_FREE`, `ACCOUNT_MARGIN_LEVEL`, dan `ACCOUNT_CURRENCY`.
- `ACCOUNT_PROFIT` ditampilkan sebagai `Floating P/L`, bukan realized P/L.
- `Realized P/L Today` dihitung terpisah dari deal history yang sudah ditutup sejak awal hari menurut timezone account/reporting yang ditetapkan; refresh saat trade transaction dan minimal setiap 60 detik. Definisi hari dan komponen commission/swap/fee wajib terlihat.
- Account number, nama pemilik, password, dan credential broker tidak dikirim atau ditampilkan; identitas sumber cukup berupa broker/server alias yang aman.
- Ketika terminal/feed aktif, EA mengambil account snapshot setiap 1 detik dan mengirim batch bersama heartbeat. Interval dapat dinaikkan menjadi 5 detik di luar window London jika tidak ada posisi terbuka.
- Backend mempertahankan latest snapshot untuk UI, tetapi tidak menyimpan setiap snapshot satu detik sebagai histori permanen.
- Persist snapshot secara durable ketika: risk assessment dibuat, pengguna mencatat tindakan, trade transaction terdeteksi, perubahan equity mencapai threshold material, atau heartbeat audit 1 menit.
- Threshold material awal: perubahan equity/floating P/L `>= 0,1%` dari equity referensi; nilai ini versioned dan ditinjau saat burn-in.
- Freshness account telemetry: `GOOD <= 3 detik`, `WARNING > 3 detik`, `STALE > 15 detik` ketika market/terminal seharusnya aktif.
- Account telemetry `STALE/UNAVAILABLE` membuat suggested lot `N/A` dan memblokir `RiskAssessment.APPROVED`, tetapi histori/dashboard lain tetap dapat dibuka.
- Setiap risk assessment menyimpan equity snapshot ID, nilai equity, account currency, dan `asOf` yang benar-benar dipakai dalam perhitungan.

## 2. Bahasa domain

Bahasa domain adalah kamus resmi agar kata seperti “signal”, “setup”, dan “trade” tidak memiliki arti berbeda di backend, UI, database, dan percakapan produk.

### 2.1 Tipe inti

| Tipe | Arti dan batasnya |
|---|---|
| `Candle` | Ringkasan OHLC untuk satu pair dan timeframe pada interval `[openTime, closeTime)`, termasuk tick volume/real volume bila ada, spread, source broker, dan status final. |
| `TradingInstrument` | Instrumen canonical dengan `InstrumentType=FOREX/PRECIOUS_METAL`, misalnya `EURUSD` atau `XAUUSD`; forex memiliki base/quote currency, sedangkan XAUUSD memiliki metal `XAU` dan quote `USD`. Mapping simbol broker seperti `EURUSD.a`/`XAUUSDm` disimpan terpisah. |
| `TechnicalSnapshot` | Hasil indikator dan structure untuk satu instrumen/timeframe pada cutoff tertentu; immutable dan mempunyai `formulaVersion`. |
| `EconomicEvent` | Fakta terjadwal/terbit: negara, currency, waktu, importance, actual, forecast, previous, unit, dan sumber. |
| `NewsImpact` | Interpretasi terstruktur atas dampak berita; bukan fakta pasar dan tidak digunakan pada Technical MVP. |
| `TradeSignal` | Hasil penilaian arah peluang `LONG_CANDIDATE/SHORT_CANDIDATE/NO_OPPORTUNITY` pada suatu waktu; belum merupakan rencana trade atau tindakan menutup posisi. |
| `TradeSetup` | Signal yang dilengkapi entry zone, expiry, invalidation, SL, TP, dan evidence. |
| `RiskAssessment` | Keputusan terpisah `APPROVED/REDUCED/REJECTED`, ukuran maksimum, R/R, warning, blocking reason, dan versi policy. |
| `TradeDecision` | Catatan eksplisit tindakan posisi pengguna, misalnya `OPEN_LONG`, `OPEN_SHORT`, `CLOSE_LONG`, `CLOSE_SHORT`, atau `SKIP`; bukan bukti bahwa order benar-benar tereksekusi di MetaTrader. |
| `TradeOutcome` | Hasil aktual yang dimasukkan pengguna: fill, exit, biaya, P/L, hasil dalam R, dan catatan. |
| `Notification` | Pesan turunan dari setup yang lolos rule; memiliki waktu dibuat, TTL, status dibaca, dan deduplication key. |

Urutan makna:

```text
MarketFact → AnalysisSnapshot → Opportunity/Signal → TradeSetup
→ RiskAssessment → Notification → User TradeDecision → TradeOutcome
```

Fakta tidak boleh ditimpa oleh interpretasi. `TradeDecision` tidak boleh dibuat otomatis dari `TradeSignal`.

### 2.2 Enum canonical

- `Timeframe`: `M15`, `H1`, `H4`.
- `Trend`: `BULLISH`, `BEARISH`, `SIDEWAYS`, `UNKNOWN`.
- `MarketRegime`: `TRENDING`, `RANGING`, `HIGH_VOLATILITY`, `LOW_LIQUIDITY`, `UNKNOWN`.
- `OpportunityDirection`: `LONG_CANDIDATE`, `SHORT_CANDIDATE`, `NO_OPPORTUNITY`.
- `PositionAction`: `OPEN_LONG`, `OPEN_SHORT`, `CLOSE_LONG`, `CLOSE_SHORT`, `REDUCE`, `HOLD`, `SKIP`.
- `Severity`: `INFO`, `WARNING`, `BLOCKING`.
- `DataQuality`: `GOOD`, `DEGRADED`, `STALE`, `INSUFFICIENT`.
- `RiskDecision`: `APPROVED`, `REDUCED`, `REJECTED`.

Seluruh timestamp disimpan sebagai UTC ISO-8601. Timezone pengguna hanya dipakai ketika render UI; simpan juga timezone yang digunakan saat pengguna membuat keputusan untuk kebutuhan audit.

## 3. Kontrak scoring v1

Tabel kondisi indikator, skor numerik, konflik, confidence, dan fixture canonical berada di [Tabel Aturan Scoring v1](00-scoring-rules-v1.md). Bagian berikut merangkum kontrak tingkat produk.

### 3.1 Arti skala

Semua directional score berada dalam `[-10, +10]`:

| Rentang | Interpretasi |
|---:|---|
| `+7` s.d. `+10` | Bullish sangat kuat; beberapa evidence searah |
| `+4` s.d. `< +7` | Bullish yang layak menjadi kandidat BUY |
| `> -4` s.d. `< +4` | Netral, lemah, atau konflik; WAIT |
| `-7` s.d. `-4` | Bearish yang layak menjadi kandidat SELL |
| `-10` s.d. `< -7` | Bearish sangat kuat; beberapa evidence searah |

Skor wajib menyimpan sub-score dan penjelasan evidence. Contoh: “EMA20 < EMA50 < EMA200 dan harga di bawah EMA20 menghasilkan trend score negatif”, bukan hanya menampilkan angka `-7`.

### 3.2 Formula awal

Technical score per timeframe:

```text
technical(tf) =
  30% × emaTrend
+ 30% × marketStructure
+ 20% × momentum(RSI + MACD)
+ 10% × supportResistanceContext
+ 10% × volatilitySetup
```

Setiap komponen terlebih dahulu dinormalisasi ke `[-10, +10]`. Bobot multi-timeframe:

```text
multiTimeframeTechnical = 20% × technical(M15)
                        + 50% × technical(H1)
                        + 30% × technical(H4)

combinedScore = 60% × multiTimeframeTechnical
              + 20% × currencyStrengthDifferential
              + 20% × regimeFitDirectionalScore
```

Formula di atas berlaku untuk empat instrumen forex. Untuk `XAUUSD`, currency-strength differential tidak digunakan agar tidak memaksakan model currency-pair dan tidak menggandakan bukti teknikal:

```text
combinedScore(XAUUSD) = 80% × multiTimeframeTechnical
                       + 20% × regimeFitDirectionalScore
```

Gunakan formula version terpisah `score-v1-fx` dan `score-v1-xau`. Formula ini adalah baseline untuk diuji, bukan formula yang sudah terbukti profitable. Fundamental/news belum diberi bobot pada Technical MVP. Penambahan engine baru harus menghasilkan formula version baru dan tidak boleh diam-diam mengubah histori.

### 3.3 Konflik timeframe dan engine

Konflik timeframe berarti timeframe memberikan arah berbeda, misalnya M15 bullish tetapi H4 bearish. Konflik engine berarti technical bullish tetapi regime/risk menyatakan kondisi tidak layak.

Aturan v1:

- H1 dan H4 berlawanan dengan kekuatan masing-masing `abs(score) >= 4` → `WAIT`.
- M15 berlawanan dengan H1, tetapi H4 dan H1 searah → tetap kandidat, confidence dikurangi 15 poin dan tunggu confirmation M15.
- Untuk forex, technical dan currency-strength berlawanan kuat (`abs(score) >= 4`) → `WAIT`; aturan ini tidak diterapkan pada XAUUSD.
- `RiskAssessment.REJECTED`, data `STALE/INSUFFICIENT`, spread abnormal, atau event embargo selalu memaksa `WAIT`, berapa pun combined score.

### 3.4 Threshold arah

- `LONG_CANDIDATE`: `combinedScore >= +4`, confidence `>= 65`, dan tidak ada blocker.
- `SHORT_CANDIDATE`: `combinedScore <= -4`, confidence `>= 65`, dan tidak ada blocker.
- `NO_OPPORTUNITY`: semua kondisi lain.
- Notifikasi entry hanya dikirim untuk `LONG_CANDIDATE/SHORT_CANDIDATE` dengan risk decision `APPROVED` atau `REDUCED`.
- Arah peluang tidak pernah berarti menutup posisi yang sudah ada. Contoh: score negatif dapat menghasilkan kandidat membuka short, tetapi `CLOSE_LONG` tetap keputusan pengguna yang terpisah. Reversal dicatat sebagai dua tindakan.

Threshold harus dituning hanya menggunakan dataset training, kemudian diverifikasi pada validation dan out-of-sample data.

### 3.5 Confidence

Confidence berada pada `0–100` dan berarti **kekuatan serta kelengkapan evidence**, bukan probabilitas menang:

```text
confidence = 100 × (
  35% × dataQuality
+ 30% × timeframeAgreement
+ 20% × min(abs(combinedScore) / 10, 1)
+ 15% × regimeFit
)
```

Semua input formula confidence dinormalisasi ke `[0, 1]`. UI wajib menampilkan label `Evidence confidence`, tidak boleh menampilkan “peluang menang”. Setelah data outcome cukup, calibration report membandingkan bucket confidence dengan win rate aktual tanpa otomatis mengganti makna confidence.

### 3.6 Data buruk

- Data hilang pada lookback minimum indikator → `INSUFFICIENT`, tidak menghitung score, hasil `WAIT`.
- Gap candle, terminal/bridge reconnect, atau sebagian timeframe tidak tersedia → `DEGRADED`; lakukan backfill dan jangan publish signal baru sampai konsisten.
- Melewati hard freshness limit → `STALE`, `WAIT`, notification lama ditandai expired.
- Timestamp mundur, OHLC invalid, duplikat berbeda isi, atau spread tidak masuk akal → karantina record dan jangan ikut scoring.
- Satu feed broker berarti tidak ada konsensus lintas-provider pada MVP. Anomali dideteksi terhadap rolling median/spread percentile dan status sesi.
- UI selalu menampilkan `asOf`, usia data, data quality, dan blocking reason.

## 4. Sumber data dan batas operasional

### 4.1 Market data broker melalui MetaTrader 5

Sumber utama MVP adalah **terminal MetaTrader 5 yang terhubung ke broker pengguna**. Pada development macOS, EA MQL5 read-only mengirim feed melalui HTTP ke Python Data Bridge native, lalu bridge meneruskannya ke backend .NET.

- EA menggunakan fungsi native MQL5 seperti `SymbolInfoTick`, `CopyRates`, dan metadata simbol untuk mengambil latest tick, candle/bar, spread, tick volume, real volume bila broker menyediakannya, serta waktu.
- Candle yang digunakan adalah `M15`, `H1`, dan `H4`. Kedalaman histori mengikuti data broker dan konfigurasi `Max. bars in chart` terminal.
- `tick_volume` adalah jumlah aktivitas tick broker, **bukan volume transaksi forex global**; `real_volume` dianggap opsional.
- Mapping simbol ditemukan dari terminal karena broker dapat memakai suffix/prefix: contoh `EURUSD.a→EURUSD` dan `XAUUSDm→XAUUSD`.
- Nama broker/server dan simbol asli disimpan bersama source untuk audit dan reproducibility.
- Terminal menggunakan installer MT5 resmi macOS; Python bridge berjalan native pada macOS tanpa Windows VM.
- EA melakukan HTTP POST secara batch dari `OnTimer`, bukan pada setiap tick, karena `WebRequest` bersifat synchronous. URL localhost/backend wajib ditambahkan manual ke allowed URLs terminal.
- Exporter dan bridge hanya membaca/memindahkan data. `OrderSend`, modifikasi posisi, dan operasi trading lainnya dilarang pada MVP.
- Backend tidak menerima password akun broker; terminal yang sudah login menjadi batas autentikasi broker.
- Twelve Data Basic boleh digunakan hanya sebagai alat development/fallback berstatus `DEGRADED`, bukan sumber notifikasi entry real-time utama.

Referensi resmi:

- [Instalasi resmi MetaTrader 5 pada macOS](https://www.metatrader5.com/en/terminal/help/start_advanced/install_mac)
- [MQL5 `WebRequest`](https://www.mql5.com/en/docs/network/webrequest)
- [MQL5 `CopyRates`](https://www.mql5.com/en/docs/series/copyrates)
- [Panduan belajar Python proyek](panduan-belajar-python-mt5.md)

### 4.2 Economic calendar

- Kandidat gratis pertama untuk technical spike: **Financial Modeling Prep (FMP) Economic Calendar**, karena menyediakan REST endpoint, respons kalender dalam UTC, dan paket Basic tercantum 250 request/hari.
- Aplikasi cukup polling setiap 10 menit dan menyimpan cache, sehingga kebutuhan teoritis sekitar 144 request/hari bila dilakukan 24 jam; polling dapat dihentikan saat weekend.
- Akses endpoint economic calendar pada akun Basic **harus diuji langsung sebelum dikunci**, karena matriks endpoint/paket dapat berubah atau membatasi dataset tertentu.
- Fallback gratis untuk event/data USD adalah **FRED API**. FRED menyediakan release dates dan observations, tetapi bukan pengganti kalender forex global lengkap dan memperingatkan bahwa tanggal rilis tidak selalu sama dengan waktu data tersedia.
- Jika FMP Basic tidak memberikan coverage gratis yang diperlukan, fitur embargo kalender global ditandai `UNAVAILABLE` pada MVP; dilarang scraping situs atau menggunakan feed tanpa izin. Pemilihan provider berbayar menjadi keputusan produk baru.

Referensi resmi:

- [FMP Economic Calendar](https://site.financialmodelingprep.com/developer/docs/stable/economics-calendar)
- [FMP pricing](https://site.financialmodelingprep.com/pricing-plans)
- [FRED release dates API](https://fred.stlouisfed.org/docs/api/fred/releases_dates.html)

## 5. Non-functional requirements

### 5.1 Availability, retention, dan recovery

- Target availability MVP: `99,5%` per bulan saat pasar buka, tidak termasuk maintenance terjadwal, outage broker, dan outage terminal yang berada di luar aplikasi.
- Raw tick/price update: 30 hari.
- Candle M15/H1/H4: target minimum 10 tahun atau sepanjang histori yang tersedia dan diizinkan broker; kekurangan histori harus terlihat sebagai coverage gap.
- Snapshot, signal, setup, notification, risk assessment, user decision, dan outcome: 7 tahun.
- Application log: 30 hari; security/audit log: 1 tahun.
- Backup database: full harian dan incremental/WAL bila tersedia.
- `RPO <= 15 menit`: kehilangan data maksimum yang diterima setelah insiden adalah 15 menit. Candle pasar yang hilang dapat di-backfill; keputusan pengguna tidak boleh bergantung hanya pada cache.
- `RTO <= 4 jam`: target waktu memulihkan layanan setelah insiden adalah empat jam.
- Restore drill dilakukan minimal per kuartal dan hasilnya dicatat.

### 5.2 Security

- Autentikasi menggunakan JWT access token berumur 15 menit dan refresh token berumur maksimum 7 hari dengan rotation dan revocation.
- Password di-hash dengan algoritma password hashing modern yang disediakan framework; tidak pernah dienkripsi secara reversible atau dicatat di log.
- JWT signing key, bridge credential, OpenAI API key, economic-data token, dan database credential berada di secret store/environment, bukan repository.
- OpenAI API key hanya boleh digunakan backend/worker server-side; tidak pernah dikirim ke Angular, browser, MT5, atau Python bridge.
- Gunakan project API key khusus aplikasi agar rotasi, pencabutan, penggunaan, dan biaya tidak bercampur dengan proyek lain.
- Seluruh trafik non-local memakai HTTPS; endpoint login diberi rate limit.
- Walaupun MVP satu pengguna, authorization policy `USER` dan `ADMIN` tetap dipisahkan untuk konfigurasi sensitif.
- Audit event bersifat append-only pada level aplikasi dan mencatat actor, action, target, timestamp UTC, correlation ID, before/after yang aman, serta alasan bila relevan.

### 5.3 Capacity awal

- 1 pengguna aktif.
- 5 instrumen × 3 timeframe = 15 stream analisis.
- Capacity awal bridge dibatasi secara konfigurasi, dengan target menerima sekurangnya latest tick yang memenuhi freshness untuk lima instrumen tanpa memproses setiap perubahan harga sebagai scan baru.
- Scanner menyelesaikan seluruh universe dalam 5 detik.
- Notification dideduplicate per `(instrument, opportunityDirection, setupVersion)` dan tidak dikirim ulang kecuali setup berubah material atau notification sebelumnya expired.
- Target maksimum awal 10.000 audit/event record per hari; angka ditinjau ulang setelah burn-in.

### 5.4 Audit keputusan manual

Saat `Catat BUY/SELL/SKIP` ditekan, simpan:

- user, setup ID/version, signal dan risk-assessment ID/version;
- keputusan, waktu keputusan UTC, timezone tampilan, dan harga pasar saat pencatatan;
- entry, lot, SL, TP, serta ticket MetaTrader sebagai input opsional pengguna;
- snapshot evidence, score, confidence, data freshness, dan warnings yang dilihat pengguna;
- catatan bebas dan alasan skip/override.

Catatan tidak boleh menyatakan `EXECUTED` hanya karena tombol ditekan. Status eksekusi tetap `USER_REPORTED` sampai pengguna memasukkan detail fill atau integrasi MetaTrader dibangun pada fase terpisah.

## 6. Data contract minimum

Definisi field, enum, invariants, dan contoh payload canonical lengkap berada di [Fase 00 — Data Dictionary dan Kontrak JSON](00-data-dictionary.md). Contoh ringkas berikut hanya memperlihatkan hubungan setup, scoring, dan risk assessment.

Contoh notification/setup yang menghubungkan kontrak utama:

```json
{
  "setupId": "01J...",
  "instrument": "EURUSD",
  "direction": "LONG_CANDIDATE",
  "createdAt": "2026-08-17T08:15:04Z",
  "expiresAt": "2026-08-17T09:00:00Z",
  "analysisTimeframe": "H1",
  "entryZone": { "min": "1.17120", "max": "1.17160" },
  "stopLoss": "1.16880",
  "takeProfit": "1.17720",
  "riskReward": 2.0,
  "suggestedMaxLots": "0.10",
  "combinedScore": 6.4,
  "confidence": 74,
  "confidenceMeaning": "EVIDENCE_STRENGTH_NOT_WIN_PROBABILITY",
  "riskDecision": "APPROVED",
  "dataQuality": "GOOD",
  "asOf": "2026-08-17T08:15:00Z",
  "reasons": ["H1 dan H4 bullish", "Market structure higher-high/higher-low"],
  "warnings": [],
  "formulaVersion": "score-v1-fx",
  "riskPolicyVersion": "risk-v1"
}
```

Nilai harga dan lot pada contoh hanya ilustrasi struktur, bukan rekomendasi trading.

## 7. Backlog MVP terurut dan acceptance criteria

1. **MT5 bridge spike:** terminal demo broker dapat mengambil dan menyimpan tick/spread serta candle final untuk lima instrumen × tiga timeframe; mapping simbol, timestamp, volume semantics, coverage histori, dan batas broker dicatat.
2. **Economic-calendar spike:** akun FMP Basic diuji untuk event USD/EUR/GBP/JPY/AUD/CHF; coverage, field, delay, kuota, dan izin penggunaan dicatat. Gagalnya spike menghasilkan status `UNAVAILABLE`, bukan data palsu.
3. **Domain foundation:** tipe dan enum canonical di atas dibuat dengan invariants serta unit test.
4. **Data quality:** gap, duplikat, invalid OHLC, stale stream, market closed, dan reconnect menghasilkan status yang benar.
5. **Scoring v1:** seluruh sub-score dapat ditelusuri; scenario bullish, bearish, conflicting, dan insufficient-data lulus.
6. **Risk sizing:** lot maksimum tidak tersedia tanpa equity/SL; dengan input lengkap, sizing mengikuti risk cap dan pip value pair.
7. **Scanner/notification:** hanya setup lolos threshold dan risk rule yang mengirim notification; duplicate dan expired setup ditangani.
8. **Dashboard dan JWT:** pengguna login dan melihat status/freshness, ranking, detail evidence, serta warning.
9. **Audit decision:** `Catat BUY/SELL/SKIP` membuat record append-only tanpa mengirim order ke provider atau MetaTrader.
10. **Outcome journal:** keputusan dapat dilengkapi hasil aktual dan ditelusuri kembali ke versi setup asli.

## 8. Pengujian/validasi wajib

- Review manual satu candle dari terminal MT5 → Python bridge → normalisasi backend → indikator → score → risk assessment → notification → user decision → outcome.
- Uji formula dengan fixture bullish, bearish, conflicting timeframe, conflicting engine, insufficient-data, stale, spread abnormal, dan event embargo.
- Bandingkan sampel harga/candle tersimpan dengan chart broker pada terminal MT5 dan pastikan hanya candle final masuk scoring.
- Jalankan backtest dan forward test per pair; laporkan win rate, expectancy, drawdown, dan biaya. Pair tidak dikeluarkan hanya berdasarkan win rate tanpa mempertimbangkan sample size dan regime.
- Uji restore untuk membuktikan RPO/RTO, bukan hanya keberadaan backup.
- Pastikan stakeholder dapat menjelaskan perbedaan score, confidence, signal, risk decision, user decision, dan outcome dengan interpretasi yang sama.

## 9. Keputusan yang masih terbuka

- Konfirmasi MetaTrader yang digunakan adalah MT5, bukan MT4; rancangan EA exporter memakai API dan format MQL5.
- Jalankan spike MT5 macOS → EA `WebRequest` → Python localhost pada perangkat pengguna sebelum mengunci pipeline.
- Catat broker/server, pola nama simbol, ketersediaan lima instrumen, kedalaman histori, dan metadata contract/tick/volume dari akun demo pengguna.
- Verifikasi akses dan coverage FMP Economic Calendar pada paket Basic saat spike dilakukan.
- Implementasikan sumber equity utama dari `AccountSnapshot` MT5 read-only; input manual hanya fallback eksplisit dan tidak boleh dianggap fresh tanpa timestamp serta konfirmasi pengguna.
- Tentukan apakah in-app notification cukup atau diperlukan browser/email/mobile notification setelah MVP.
- Kalibrasi bobot, threshold, spread abnormal, session window, dan embargo berita melalui backtest/forward test; nilai v1 di dokumen adalah baseline yang versioned.
- Definisikan acceptance target strategi (minimum jumlah trade, expectancy, dan maximum drawdown); jangan menetapkan target win rate saja.

## Kriteria selesai Fase 00

- Scope MVP dan non-goals disetujui pemilik produk.
- Tidak ada tipe inti atau formula skor yang masih memiliki dua interpretasi.
- MT5 broker feed dan economic-calendar telah lolos spike, termasuk coverage, batas, dan izin penggunaan.
- Pair, timeframe, latency, retention, RPO/RTO, capacity, serta security baseline telah disetujui.
- Contoh validasi manual dan semua scenario scoring mempunyai expected result numerik.
- Backlog fase 01–06 dapat dikerjakan tanpa keputusan produk besar yang tertunda.
