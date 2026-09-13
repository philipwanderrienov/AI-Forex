# Database PostgreSQL melalui DBeaver

Database memakai PostgreSQL native. Seluruh script SQL pada folder ini dibuat untuk langsung
dijalankan melalui DBeaver tanpa perintah khusus terminal.

## Instalasi baru

1. Buka koneksi administrator DBeaver ke database bawaan `postgres`.
2. Buka `000-create-database.sql` dan ganti `CHANGE_ME_STRONG_PASSWORD`.
3. Jalankan blok pembuatan role. Jalankan `CREATE DATABASE` hanya jika database
   `forex_intelligence` belum tersedia.
4. Arahkan koneksi DBeaver administrator ke database `forex_intelligence`, atau buat koneksi
   terpisah sebagai `forex_app` bila diinginkan.
5. Buka SQL Editor dari koneksi tersebut dan pastikan selector toolbar menunjukkan
   `public@forex_intelligence`, bukan `public@postgres`.
6. Jalankan seluruh `001-complete-schema.sql` dengan **Execute SQL Script** (`Alt+X`). Script
   memakai `SET LOCAL ROLE forex_app`, sehingga koneksi administrator boleh digunakan tetapi
   seluruh object tetap dibuat dan dimiliki oleh `forex_app`.
7. Jalankan `999-verify-schema.sql`. Verifikasi melempar exception jika target koneksi salah,
   schema belum lengkap, primary key/index hilang, atau ownership tidak sesuai.

Jangan simpan password nyata ke file SQL atau Git. Setelah setup, kembalikan placeholder
password sebelum menyimpan file.

## Schema terbaru

- `__EFMigrationsHistory`: histori migration EF Core;
- `candles`: candle market-data;
- `refresh_tokens`: hash refresh token, family, expiry, rotation, dan revocation;
- `market_data_batches`: ledger batch idempotent berdasarkan batch ID dan source sequence;
- unique index candle berdasarkan instrument, timeframe, dan open time;
- unique index refresh-token hash;
- index refresh-token family dan expiry.
- unique index source instance dan sequence batch market-data.

Tidak ada seed user atau password di database. Connection string, username/password hash
bootstrap, dan JWT signing key tetap disimpan melalui environment atau .NET user-secrets.

## Diagnosis gap XAUUSD H1

Jalankan `010-diagnose-xauusd-h1-gaps.sql` pada koneksi database `forex_intelligence`
di server antiX menggunakan **Execute SQL Script** (`Alt+X`). Ini diagnosis opsional,
bukan migration; transaksi read-only dan seluruh kolom waktu hasil ditampilkan dalam WIB.
Jika script gagal di tengah transaksi, jalankan `ROLLBACK;` sebelum mengulang.

Default rentang adalah delapan hari terakhir. Untuk membandingkan snapshot status tertentu,
ganti `CURRENT_TIMESTAMP` pada CTE `parameters` dengan waktu `asOf` snapshot API sebagai
`TIMESTAMPTZ '2026-09-10 00:08:49+00'` (contoh, bukan waktu snapshot yang sudah diverifikasi).
Query membatasi open time sampai waktu tersebut, sedangkan API saat ini hanya memiliki batas
bawah lookback. Perbandingan mengasumsikan tidak ada candle bertimestamp masa depan. Query
pada database saat ini juga tidak dapat merekonstruksi isi database sebelum backfill berikutnya.

Setiap baris menunjukkan satu interval antarcandle yang lebih panjang dari satu jam:

- `previous_open_wib` / `next_open_wib`: batas interval untuk dicocokkan dengan chart/history MT5.
- `api_gap_slots`: jumlah slot kosong menurut jadwal API Minggu 22:00-Jumat 22:00 UTC.
- `hypothesis_open_missing_slots`: slot kosong saat sesi XAUUSD diperkirakan buka,
  dengan hipotesis broker UTC+3 dan sesi Senin-Jumat 00:00-23:00 waktu broker.
- `api_slots_explained_by_hypothesis`: gap versi API yang jatuh pada sesi tutup dalam hipotesis.
- `first_open_missing_wib`: slot pertama yang perlu dibandingkan dengan history MT5.
- `total_api_gap_slots` / `total_hypothesis_open_missing_slots`: total seluruh interval,
  diulang pada setiap baris; jangan dijumlahkan lagi antarbaris.

`CLOSED_UNDER_UTC_PLUS_3_HYPOTHESIS` belum membuktikan data lengkap. Offset +3 hanya dugaan
untuk periode pengamatan September 2026, bukan aturan DST historis. Jangan memakai hasil ini
untuk mengubah timestamp atau mereplay data sebelum dibandingkan dengan sesi/history broker.
`CHECK_TIMESTAMP_ALIGNMENT` memerlukan pemeriksaan timestamp; hitungan slot pada interval
yang tidak bulat satu jam hanya indikasi. `INSUFFICIENT_DATA` berarti kurang dari dua candle.

Query menghitung gap internal di antara candle FINAL yang tersimpan, seperti algoritma API.
Ia tidak menghitung kekurangan sebelum candle pertama atau setelah candle terakhir, sehingga
`NO_INTERNAL_GAPS` tidak membuktikan freshness atau kelengkapan seluruh histori. Periksa juga
`candle_count`, `first_stored_open_wib`, dan `last_stored_close_wib`.

Bagikan hasil tabel diagnosis untuk langkah kalibrasi berikutnya. Tidak perlu menyertakan
credential, connection string, atau identitas akun broker. Pertahankan quarantine dan backup.

## Recovery ledger inspection

`011-inspect-recovery-ledger.sql` is a read-only DBeaver script for source sequence
maxima and incident sample rows, with WIB storage times. It does not initialize or
modify sequences. Compare with pending spool, quarantine and stopped terminal state
before setting an exporter floor; see `mt5-exporter/RECOVERY.md`.


### Scoped recovery preview

012-preview-xauusd-h1-recovery.sql is an optional incident-specific manual repair,
not a schema migration. Execute the ENTIRE script in DBeaver. Final ROLLBACK
discards inserts; review count and 16 rows before replacing only the final
ROLLBACK with COMMIT and executing the entire script again. On error execute
ROLLBACK. Identical existing candles are skipped; differing rows cause an error.
CSV provenance and the tick-volume discrepancy are recorded in the script.
No batch ledger, checkpoint or quarantine changes are made.


013-preview-xauusd-h1-second-recovery.sql follows the same transaction workflow
for 15 additional broker CSV candles (September 10 12:00–September 11 02:00 WIB).
It excludes the four slots with no bars in the export. Default ROLLBACK; review
the 15-row result before committing. This is also optional manual recovery.
