# Fase 09 — Production Hardening dan Operasional

## Tujuan

Menjadikan aplikasi aman, teramati, resilien, dan dapat dipulihkan. Fase ini juga menentukan kapan komponen perlu dipisahkan, bukan memecahnya hanya karena rancangan awal.

## Pekerjaan

### 1. Security

- Threat modeling untuk API, terminal/bridge MT5, credential bridge, AI prompt, dan data pengguna.
- Gunakan secret store, rotasi credential, least privilege, dan audit log.
- Authentication/authorization, rate limiting, secure headers, dan dependency scanning.
- Sanitasi log serta aturan retention/deletion data.
- Review risiko prompt injection dan data exfiltration pada pipeline berita.

### 2. Reliability

- Timeout, retry dengan jitter, circuit breaker, bulkhead, dan graceful degradation.
- Idempotency untuk ingestion dan job processing.
- Dead-letter/reprocessing workflow jika message queue kemudian digunakan.
- Kill switch rekomendasi saat data stale, kalkulasi gagal, terminal MT5 mati, bridge terputus, atau broker tidak sehat.
- Uji restart dan recovery di tengah proses.

### 3. Observability

- Structured logs, metrics, dan distributed traces dengan correlation ID.
- SLI/SLO untuk freshness data, pipeline success, scanner latency, API availability, dan AI error rate.
- Dashboard operasional serta alert dengan runbook.
- Audit trail dari rekomendasi kembali ke source data dan version.

### 4. Performance dan capacity

- Load test ingestion, calculation, scanner, SignalR, dan query dashboard.
- Optimalkan indeks, query plan, cache, batching, dan payload.
- Tetapkan capacity model serta biaya hosting, broker data, dan AI per pengguna atau per hari; pertahankan biaya nol selama free tier memenuhi kebutuhan dan risiko operasional diterima.
- Lakukan soak test untuk mendeteksi leak dan backlog bertahap.

### 5. Deployment

- Container image yang reproducible dan non-root bila memungkinkan.
- CI/CD dengan build, test, security check, migration check, dan approval produksi.
- Environment development, staging, dan production yang terpisah.
- Strategi database migration backward-compatible dan rollback aplikasi.
- Backup PostgreSQL, restore drill, retention, dan disaster-recovery runbook.
- Sediakan runbook desktop-session/autostart, restart terminal MT5/Wine pada Lubuntu, EA exporter, dan Python bridge; containerisasi collector tidak diwajibkan karena terminal MT5 adalah dependency GUI/Wine lokal.

### 6. Release dan operasi

- Feature flags untuk engine/formula baru.
- Shadow mode sebelum sinyal baru memengaruhi pengguna.
- Canary/gradual rollout serta monitoring pasca-release.
- Incident response, ownership, escalation, dan postmortem.
- Dokumentasikan batas sistem serta disclaimer pengguna.

### 7. Evaluasi kebutuhan distribusi

Pertimbangkan RabbitMQ atau pemisahan service hanya jika ada bukti seperti:

- throughput pipeline menyebabkan coupling atau backlog;
- worker perlu diskalakan secara independen;
- kegagalan satu modul harus benar-benar diisolasi;
- tim membutuhkan deployment ownership terpisah;
- durability event tidak dapat dipenuhi oleh mekanisme saat ini.

Jika belum ada bukti tersebut, pertahankan modular monolith untuk mengurangi biaya operasional.

## Kriteria selesai

- SLO, alert, dashboard, dan runbook telah diuji lewat simulasi insiden.
- Backup berhasil direstore dalam target recovery.
- Security review tidak memiliki temuan kritis terbuka.
- Staging melewati load/soak test dan failure-injection yang disepakati.
- Deployment dan rollback dapat dilakukan secara terdokumentasi.
- Production release dimulai dalam mode observasi/terbatas sebelum digunakan lebih luas.
