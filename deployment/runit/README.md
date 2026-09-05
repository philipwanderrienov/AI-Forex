# Managed startup pada server antiX dengan runit

Deployment ini menjalankan PostgreSQL sebagai user `postgres`, serta API dan bridge sebagai user
non-root pemilik repository. API dan bridge hanya bind ke localhost, sedangkan secret disimpan
dalam file root-only di luar repository. Runit mengawasi dan memulai ulang proses. Bridge menunggu
readiness API sebelum membuka receiver.

## Instalasi

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
sudo sv up forex-intelligence-api
curl -fsS http://127.0.0.1:5204/health/ready
```

Perintah `grep` harus tidak menghasilkan output. Setelah API ready, aktifkan bridge:

```bash
sudo ln -s /etc/sv/forex-intelligence-bridge /etc/service/forex-intelligence-bridge
sudo sv up forex-intelligence-bridge
curl -fsS http://127.0.0.1:8001/health
```

## Operasi

```bash
sudo sv status forex-intelligence-postgresql forex-intelligence-api forex-intelligence-bridge
sudo sv restart forex-intelligence-api
sudo sv restart forex-intelligence-bridge
sudo sv restart forex-intelligence-postgresql
sudo tail -F /var/log/forex-intelligence/api/current
sudo tail -F /var/log/forex-intelligence/bridge/current
sudo tail -F /var/log/forex-intelligence/postgresql/current
```

Setelah reboot, periksa kedua status, API readiness, terminal health, spool depth, dan quarantine
depth. Jangan menghapus atau replay quarantine secara otomatis.
