# Fase 00 — Kesiapan Runtime MT5 pada Lubuntu

## Keputusan arsitektur

- Target host collector: `Lubuntu 24.04.4 LTS (Noble Numbat)`, 64-bit.
- Lubuntu dipasang pada laptop fisik khusus yang terpisah dari MacBook development; bukan virtual machine.
- MT5 berjalan melalui Wine; MT5 bukan aplikasi Linux native.
- EA MQL5 bersifat read-only dan mengirim data ke Python bridge pada host Lubuntu yang sama melalui `127.0.0.1`.
- Python bridge berjalan native Linux. Bridge tidak memakai package Python MetaTrader5 dan tidak memiliki kemampuan mengirim order.
- Development aplikasi tetap dilakukan di macOS. Kode dikirim melalui Git; data/secret runtime tidak disalin ke repository.
- Seluruh runtime MVP—bridge, backend .NET, PostgreSQL, Redis/Valkey, dan Angular—berjalan pada laptop Lubuntu. macOS boleh menjalankan test lokal, tetapi bukan host produksi MVP.
- Dashboard diakses dari MacBook/perangkat pengguna melalui HTTPS pada LAN. Hanya endpoint UI/API yang diperlukan yang boleh mendengarkan interface LAN; receiver EA tetap hanya `127.0.0.1`.

```text
Broker
  → MT5 on Wine (Lubuntu)
  → EA MQL5 read-only
  → HTTP 127.0.0.1
  → Python bridge native Linux + bounded spool
  → authenticated localhost ingestion
  → .NET backend → PostgreSQL/Redis → Angular
  → HTTPS/LAN → browser pengguna
```

## Persiapan perangkat

| Item | Baseline spike | Catatan |
|---|---|---|
| CPU | x86-64, 2 core tersedia | Ukur saat lima instrumen aktif |
| RAM | 4 GB minimum baseline | Bukan jaminan; naikkan jika Wine/terminal swap atau tidak stabil |
| Disk kosong | 25 GB minimum baseline | Untuk OS, Wine prefix, histori MT5, log, dan spool terbatas |
| Jaringan | Stabil; kabel lebih disukai | Wi-Fi boleh untuk spike tetapi reconnect wajib diuji |
| Daya | Auto power-on; UPS bila perangkat fisik selalu aktif | Hindari sleep/suspend saat market aktif |
| Waktu | NTP aktif, timezone OS boleh Jakarta | Semua payload dan audit tetap UTC |
| Desktop session | LXQt/X11 yang persisten | MT5 adalah aplikasi GUI di bawah Wine |

Angka hardware adalah titik awal pengujian, bukan persyaratan resmi MetaTrader. Kelayakan ditentukan dari telemetry dan soak test.

## Checklist instalasi aman

1. Unduh ISO hanya dari situs resmi Lubuntu dan verifikasi checksum.
2. Install seluruh update keamanan Lubuntu sebelum memasang MT5.
3. Buat user Linux khusus collector tanpa login root dan tanpa akses ke repository secret lain.
4. Install MT5 memakai petunjuk/script resmi MetaTrader untuk Linux. Script dijalankan sebagai user biasa; elevasi hanya ketika installer meminta pemasangan package.
5. Izinkan Wine Mono/Gecko jika installer resmi memerlukannya, lalu reboot.
6. Login terlebih dahulu ke akun **demo**, pilih server broker, dan pastikan lima instrumen tersedia.
7. Simpan versi Lubuntu, kernel, Wine, MT5 build, broker server alias, dan waktu instalasi dalam inventory—tanpa account number/password.
8. Install Python versi distro, buat virtual environment, lalu jalankan bridge sebagai user yang sama.
9. Bind listener EA hanya ke `127.0.0.1`; jangan membuka port receiver EA ke internet/LAN.
10. Tambahkan URL localhost bridge pada daftar allowed `WebRequest` MT5.
11. Pasang EA read-only dan lakukan pemeriksaan source bahwa tidak ada `OrderSend`, perubahan, atau penutupan posisi.
12. Nonaktifkan sleep/suspend otomatis dan konfigurasikan autostart terkontrol untuk desktop session, MT5, serta bridge.

## Spike wajib sebelum pipeline dikunci

| Uji | Durasi/kriteria awal |
|---|---|
| MT5 membuka dan login kembali setelah reboot | 3 reboot berturut-turut berhasil |
| EA → bridge localhost | Heartbeat dan batch diterima tanpa order permission |
| Lima instrumen | Simbol broker, digits, tick size/value, contract size, volume limits ditemukan |
| Candle | M15/H1/H4 final cocok dengan chart terminal pada sampel manual |
| Account telemetry | Balance/equity/P&L/margin cocok tanpa account identity keluar |
| Reconnect broker | Gap terdeteksi, backfill berjalan, tidak ada duplikat |
| Backend mati | Spool bounded menyimpan data dan replay idempotent setelah pulih |
| Clock | Drift terukur; timestamp tidak mundur |
| Soak test | Minimum 5 hari trading, termasuk seluruh window London |
| Resource usage | Tidak ada swap berat, disk runaway, crash loop, atau backlog bertumbuh |

Spike dinyatakan gagal jika MT5/Wine sering berhenti, EA tidak pulih setelah reconnect, data tidak konsisten dengan chart broker, atau freshness tidak memenuhi batas Fase 00. Kegagalan spike tidak boleh ditutupi dengan data sintetis.

## Operasional dan keamanan

- Firewall default-deny untuk inbound yang tidak diperlukan.
- SSH, jika diperlukan, memakai key authentication; password login dan root login dinonaktifkan setelah akses teruji.
- Secret bridge disimpan dengan permission user-only dan tidak ditulis ke log.
- Folder spool memiliki batas ukuran, retention, checksum, dan alert.
- Update OS/Wine/MT5 dilakukan di luar window trading, lalu smoke test; jangan melakukan unattended restart selama sesi.
- Backup hanya mencakup konfigurasi, source EA, checkpoint, dan data yang perlu. Password/account session Wine tidak dimasukkan ke Git.
- Sediakan watchdog/health check untuk mendeteksi terminal, broker, EA heartbeat, bridge, disk, dan clock; restart otomatis dibatasi agar tidak menjadi crash loop.
- Akses desktop jarak jauh tidak dibuka ke internet secara langsung; gunakan LAN/VPN bila nanti diperlukan.

## Bukti yang harus disimpan

- Inventory versi runtime.
- Mapping lima simbol broker ke simbol canonical.
- Screenshot/config non-sensitif Market Watch dan allowed URL.
- Sampel payload dan hasil perbandingan candle.
- Catatan reboot/reconnect/soak test.
- Penggunaan CPU, RAM, disk, latency, gap, duplicate, dan freshness.
- Daftar masalah Wine/MT5 beserta langkah recovery.

## Referensi resmi

- [Instalasi MetaTrader 5 pada Linux](https://www.metatrader5.com/en/terminal/help/start_advanced/install_linux)
- [Unduhan resmi Lubuntu](https://lubuntu.me/downloads/)
- [Manual Lubuntu 24.04 LTS](https://manual.lubuntu.me/lts/)
