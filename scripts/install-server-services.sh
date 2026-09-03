#!/usr/bin/env bash

set -euo pipefail

script_directory=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
repository_root=$(cd -- "$script_directory/.." && pwd)
template_directory="$repository_root/deployment/systemd"
service_user=${SUDO_USER:-${USER:?USER is not set}}
dotnet_path=$(command -v dotnet || true)

if [[ -z $dotnet_path ]]; then
    echo 'dotnet tidak ditemukan di PATH.' >&2
    exit 1
fi
if [[ ! -x "$repository_root/mt5-bridge/.venv/bin/python" ]]; then
    echo 'Python bridge venv belum tersedia di mt5-bridge/.venv.' >&2
    exit 1
fi
if [[ ! -d "$repository_root/mt5-bridge/spool" ]]; then
    echo 'Spool bridge belum tersedia. Jalankan bridge sekali sebelum instalasi service.' >&2
    exit 1
fi

temporary_directory=$(mktemp -d)
cleanup() {
    rm -rf -- "$temporary_directory"
}
trap cleanup EXIT

render_unit() {
    local source=$1
    local destination=$2
    sed \
        -e "s|@@SERVICE_USER@@|$service_user|g" \
        -e "s|@@REPOSITORY_ROOT@@|$repository_root|g" \
        -e "s|@@DOTNET_PATH@@|$dotnet_path|g" \
        "$source" >"$destination"
}

render_unit "$template_directory/forex-intelligence-api.service.in" \
    "$temporary_directory/forex-intelligence-api.service"
render_unit "$template_directory/forex-intelligence-bridge.service.in" \
    "$temporary_directory/forex-intelligence-bridge.service"

if command -v systemd-analyze >/dev/null 2>&1; then
    systemd-analyze verify "$temporary_directory"/*.service
fi

sudo install -d -o root -g root -m 0700 /etc/forex-intelligence
for environment_name in api bridge; do
    environment_path="/etc/forex-intelligence/$environment_name.env"
    if ! sudo test -e "$environment_path"; then
        sudo install -o root -g root -m 0600 \
            "$template_directory/$environment_name.env.example" "$environment_path"
        echo "Dibuat: $environment_path (masih berisi placeholder)"
    else
        echo "Dipertahankan: $environment_path"
    fi
done

sudo install -o root -g root -m 0644 "$temporary_directory"/*.service /etc/systemd/system/
sudo systemctl daemon-reload

echo
echo 'Unit systemd berhasil dipasang tetapi belum diaktifkan.'
echo 'Isi kedua file /etc/forex-intelligence/*.env, lalu ikuti deployment/systemd/README.md.'
