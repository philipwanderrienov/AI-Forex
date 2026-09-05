# Managed startup pada server antiX dengan runit

Deployment ini menjalankan API dan bridge sebagai user non-root, mengikat keduanya ke localhost,
dan menyimpan secret dalam file root-only di luar repository. Runit mengawasi dan memulai ulang
proses. Bridge menunggu readiness API sebelum membuka receiver.

## Instalasi

Jalankan dari checkout permanen pada server antiX:

```bash
bash scripts/install-antix-runit-services.sh
```

Installer memasang definisi ke `/etc/sv`, tetapi tidak mengaktifkannya. Edit sebagai root:

```text
/etc/forex-intelligence/api.env
/etc/forex-intelligence/bridge.env
```

File memakai sintaks shell. Pertahankan single quote pada nilai, dan jangan menaruh secret di
repository, screenshot, chat, atau log. Kedua bridge API key harus identik.

Setelah tidak ada placeholder, aktifkan API lebih dahulu:

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
sudo sv status forex-intelligence-api forex-intelligence-bridge
sudo sv restart forex-intelligence-api
sudo sv restart forex-intelligence-bridge
sudo tail -F /var/log/forex-intelligence/api/current
sudo tail -F /var/log/forex-intelligence/bridge/current
```

Setelah reboot, periksa kedua status, API readiness, terminal health, spool depth, dan quarantine
depth. Jangan menghapus atau replay quarantine secara otomatis.
