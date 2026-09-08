# Managed startup pada server antiX dengan runit

Deployment ini menjalankan PostgreSQL sebagai user `postgres`, serta API dan bridge sebagai user
non-root pemilik repository. API dan bridge hanya bind ke localhost, sedangkan secret disimpan
dalam file root-only di luar repository. Runit mengawasi dan memulai ulang proses. Bridge menunggu
readiness API sebelum membuka receiver.

## Migrasi server yang sudah menjalankan runit

Jalankan dari direktori repository permanen sebagai user repository. Jalankan tiap blok terpisah
dan lanjutkan hanya bila berhasil. PostgreSQL dan bridge tetap berjalan selama migrasi API.

1. Periksa perubahan lokal dan tarik branch yang memuat tooling ini. Jika working tree berisi
   perubahan, simpan/review dahulu; jangan reset atau overwrite konfigurasi lokal.

   ```bash
   git status --short
   git pull --ff-only origin Codex
   sudo sv status forex-intelligence-postgresql forex-intelligence-api forex-intelligence-bridge
   curl -fsS http://127.0.0.1:5204/health/ready
   curl -fsS http://127.0.0.1:8001/health
   ```

2. Jalankan tes terisolasi dan publish tanpa sudo. Catat path `Published:`.

   ```bash
   bash scripts/test-api-release.sh
   bash scripts/publish-api-release.sh
   read -r -p 'Path lengkap dari Published: ' api_release_path
   test -s "$api_release_path/REVISION"
   ```

3. Backup launcher, lalu hentikan API. Pertahankan terminal ini agar variabel backup tersedia.

   ```bash
   api_launcher_backup="/etc/sv/forex-intelligence-api/run.source-backup.$(date -u +%Y%m%dT%H%M%SZ)"
   sudo cp -a /etc/sv/forex-intelligence-api/run "$api_launcher_backup"
   printf 'Backup launcher: %s\n' "$api_launcher_backup"
   sudo sv -w 30 down forex-intelligence-api
   ```

4. Pasang template terbaru, kemudian aktifkan artifact. Installer mempertahankan env yang sudah
   ada dan tidak perlu membuat ulang symlink service. Jangan menjalankan ulang transisi SysV di bawah.

   ```bash
   bash scripts/install-antix-runit-services.sh
   sudo bash scripts/activate-api-release.sh "$api_release_path"
   ```

5. Verifikasi readiness, kontrak 15 seri, dan spool. Masukkan password bootstrap saat diminta.

   ```bash
   readlink -f /opt/forex-intelligence/api/current
   sudo sv status forex-intelligence-postgresql forex-intelligence-api forex-intelligence-bridge
   curl -fsS http://127.0.0.1:5204/health/ready
   python3 tools/verify_market_data_status.py --base-url http://127.0.0.1:5204
   curl -fsS http://127.0.0.1:8001/health
   ```

   API harus `Healthy`, verifier `PASS`, spool akhirnya 0, dan quarantine tidak bertambah dibanding
   baseline. `PASS` memverifikasi kontrak; status freshness/gap masih perlu ditinjau terpisah.

6. Uji restart API (`sudo sv -w 30 restart forex-intelligence-api`), kemudian ulangi pemeriksaan
   pada langkah 5. Setelah itu lakukan reboot terencana dan ulangi pemeriksaan yang sama. MT5/EA
   tetap perlu dijalankan seperti biasa agar terminal kembali `HEALTHY`.

Jika aktivasi pertama gagal, simpan log untuk diagnosis lalu pulihkan launcher sumber:

```bash
sudo tail -n 60 /var/log/forex-intelligence/api/current
sudo sv -w 30 down forex-intelligence-api
sudo cp -a "$api_launcher_backup" /etc/sv/forex-intelligence-api/run
sudo sv -w 90 up forex-intelligence-api
curl -fsS http://127.0.0.1:5204/health/ready
```

Jalankan tiap perintah hanya setelah perintah sebelumnya berhasil. Bila terminal sudah ditutup,
isi ulang `api_launcher_backup` dengan path backup yang dicatat. Pemulihan source launcher masih
melakukan build; jika readiness belum Healthy, tunggu dan periksa log. Rollback otomatis/manual
berbasis release tersedia setelah ada release sebelumnya, bukan pada migrasi pertama.

## Instalasi awal

API dijalankan dari `/opt/forex-intelligence/api/current/ForexIntelligence.Api.dll`.
Publish terlebih dahulu sebagai user repository pada server Linux (SDK .NET 10.0.4xx):

```bash
bash scripts/publish-api-release.sh
```

Script mencetak direktori `artifacts/api/<release-id>`. Simpan path tersebut untuk aktivasi.
Build gagal tidak menyentuh service. Artifact tidak boleh memuat credential; konfigurasi runtime
tetap berasal dari `/etc/forex-intelligence/api.env`. Release framework-dependent membutuhkan
ASP.NET Core runtime .NET 10 pada server.

Untuk migrasi dari launcher `dotnet run`, publish dahulu, simpan salinan
`/etc/sv/forex-intelligence-api/run`, lalu `sudo sv -w 30 down forex-intelligence-api`
sebelum menjalankan installer berikut. Bridge tetap menyimpan envelope selama API tidak tersedia.
Migrasi pertama belum memiliki release sebelumnya untuk rollback otomatis; bila aktivasi pertama
gagal, pulihkan salinan launcher dan jalankan `sudo sv up forex-intelligence-api`.

Jalankan dari checkout permanen pada server antiX:

```bash
bash scripts/install-antix-runit-services.sh
```

Installer mendeteksi tepat satu cluster PostgreSQL pada port 5432 dan memasang ketiga definisi ke
`/etc/sv`, tetapi tidak mengaktifkannya. Edit sebagai root:

```text
/etc/forex-intelligence/api.env
/etc/forex-intelligence/bridge.env
```

File memakai sintaks shell. Pertahankan single quote pada nilai, dan jangan menaruh secret di
repository, screenshot, chat, atau log. Kedua bridge API key harus identik.

Setelah tidak ada placeholder, pindahkan PostgreSQL dari kontrol manual/SysV ke runit dalam satu
maintenance window:

```bash
sudo service postgresql stop
sudo ln -s /etc/sv/forex-intelligence-postgresql /etc/service/forex-intelligence-postgresql
sudo sv up forex-intelligence-postgresql
pg_isready -h 127.0.0.1 -p 5432
```

Setelah PostgreSQL menerima koneksi, aktifkan API:

```bash
sudo grep -R 'REPLACE_' /etc/forex-intelligence
sudo ln -s /etc/sv/forex-intelligence-api /etc/service/forex-intelligence-api
sudo bash scripts/activate-api-release.sh artifacts/api/<release-id>
curl -fsS http://127.0.0.1:5204/health/ready
```

Perintah `grep` harus tidak menghasilkan output. Setelah API ready, aktifkan bridge:

```bash
sudo ln -s /etc/sv/forex-intelligence-bridge /etc/service/forex-intelligence-bridge
sudo sv up forex-intelligence-bridge
curl -fsS http://127.0.0.1:8001/health
```

## Operasi

Untuk update berikutnya, publish sebelum maintenance singkat, kemudian aktifkan path yang dicetak:

```bash
bash scripts/publish-api-release.sh
sudo bash scripts/activate-api-release.sh artifacts/api/<release-id>
```

Aktivasi memakai lock untuk mencegah deployment bersamaan, menyalin artifact ke direktori release
root-owned, menghentikan API sampai selesai, dan mengganti symlink `current` secara atomik.
Runit menjalankan DLL tanpa restore/build. Health check menunggu maksimum sekitar 60 detik
(ditambah request yang sedang berlangsung) untuk respons `Healthy` dari `/health/ready`.
Kegagalan startup/health mengembalikan symlink dan memeriksa kesehatan release sebelumnya;
command tetap keluar nonzero agar deployment gagal terlihat. Bila penghentian proses gagal,
script berhenti untuk pemeriksaan operator. Pergantian symlink atomik bukan zero-downtime.

Rollback manual ke release sukses sebelumnya:

```bash
sudo bash scripts/activate-api-release.sh --rollback
```

Release lama dipertahankan; script tidak menghapus artifact atau menjalankan migrasi database.
Rollback hanya mencakup binary API, sehingga perubahan schema harus tetap kompatibel dengan
release sebelumnya. File `REVISION` merekam commit sumber dan penanda perubahan tracked lokal.

Verifikasi target setelah migrasi: restart API dan reboot server, ukur waktu sampai readiness
Healthy, jalankan `tools/verify_market_data_status.py`, pastikan spool kembali 0 dan quarantine
tidak bertambah. Uji rollback manual sesudah dua release sukses. Simulasi kegagalan otomatis
dapat dijalankan tanpa service nyata: `bash scripts/test-api-release.sh`.

```bash
sudo sv status forex-intelligence-postgresql forex-intelligence-api forex-intelligence-bridge
sudo sv restart forex-intelligence-api
sudo sv restart forex-intelligence-bridge
sudo sv restart forex-intelligence-postgresql
sudo tail -F /var/log/forex-intelligence/api/current
sudo tail -F /var/log/forex-intelligence/bridge/current
sudo tail -F /var/log/forex-intelligence/postgresql/current
```

Handler `control/d` dan `control/t` menghentikan cluster melalui `pg_ctlcluster stop`, sehingga
`sv down` dan `sv restart` memakai shutdown PostgreSQL yang terkontrol alih-alih hanya mengirim
SIGTERM ke wrapper foreground.

Setelah reboot, periksa kedua status, API readiness, terminal health, spool depth, dan quarantine
depth. Jangan menghapus atau replay quarantine secara otomatis.
