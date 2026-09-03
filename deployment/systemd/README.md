# Managed startup pada server Lubuntu

Unit ini menjalankan API dan bridge sebagai user non-root, mengikat keduanya ke localhost,
memulai ulang proses yang gagal, dan mengambil secret dari file di luar repository. Installer
tidak pernah mengaktifkan service sebelum operator mengganti seluruh placeholder secret.

## Instalasi

Jalankan dari checkout yang akan menjadi lokasi runtime permanen:

```bash
bash scripts/install-server-services.sh
```

Installer mempertahankan file environment yang sudah ada. Edit file berikut sebagai root:

```text
/etc/forex-intelligence/api.env
/etc/forex-intelligence/bridge.env
```

Pastikan kedua nilai bridge API key sama. Jangan menyalin secret ke repository, screenshot,
chat, atau log. Setelah semua placeholder `REPLACE_...` diganti:

```bash
sudo grep -R 'REPLACE_' /etc/forex-intelligence
sudo systemctl enable --now forex-intelligence-api.service
curl -fsS http://127.0.0.1:5204/health/ready
sudo systemctl enable --now forex-intelligence-bridge.service
curl -fsS http://127.0.0.1:8001/health
```

Perintah `grep` harus tidak menghasilkan output sebelum service diaktifkan. Jika proses lama
masih berjalan dari terminal, hentikan proses lama secara normal terlebih dahulu agar port 5204
dan 8001 tidak dipakai dua proses.

## Operasi

```bash
systemctl status forex-intelligence-api.service forex-intelligence-bridge.service
journalctl -u forex-intelligence-api.service -u forex-intelligence-bridge.service -f
sudo systemctl restart forex-intelligence-api.service
sudo systemctl restart forex-intelligence-bridge.service
```

Setelah reboot, verifikasi API readiness, bridge/terminal health, spool depth, dan quarantine
depth. Merotasi bridge key harus dilakukan pada kedua file environment dalam satu maintenance
window, lalu kedua service direstart. Jangan menghapus atau replay quarantine secara otomatis.

## Audit quarantine read-only

```bash
python tools/audit_bridge_quarantine.py
python tools/audit_bridge_quarantine.py --json
```

Tool hanya menampilkan ringkasan metadata serta `batchId`, `sourceInstanceId`, `sequence`, dan
`checksum` untuk HTTP 409. Exit code `1` berarti pasangan payload/metadata perlu diperiksa; tool
tidak memindahkan, menghapus, atau replay file.
