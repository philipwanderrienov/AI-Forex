#!/usr/bin/env bash

set -euo pipefail

script_directory=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
repository_root=$(cd -- "$script_directory/.." && pwd)
template_directory="$repository_root/deployment/runit"
service_user=${SUDO_USER:-${USER:?USER is not set}}
dotnet_path=$(command -v dotnet || true)

if [[ $(ps -p 1 -o comm= | tr -d ' ') != runit ]]; then
    echo 'Installer ini hanya untuk server antiX yang sedang memakai runit.' >&2
    exit 1
fi
if [[ -z $dotnet_path ]]; then
    echo 'dotnet tidak ditemukan di PATH.' >&2
    exit 1
fi
for command_name in chpst curl sv svlogd; do
    if ! command -v "$command_name" >/dev/null 2>&1; then
        echo "$command_name tidak ditemukan di PATH." >&2
        exit 1
    fi
done
if [[ ! -x "$repository_root/mt5-bridge/.venv/bin/python" ]]; then
    echo 'Python bridge venv belum tersedia di mt5-bridge/.venv.' >&2
    exit 1
fi
if [[ ! -d "$repository_root/mt5-bridge/spool" ]]; then
    echo 'Spool bridge belum tersedia. Jalankan bridge sekali sebelum instalasi service.' >&2
    exit 1
fi
if [[ ! -d /etc/sv || ! -L /etc/service ]]; then
    echo 'Layout service runit antiX tidak ditemukan.' >&2
    exit 1
fi

temporary_directory=$(mktemp -d)
cleanup() {
    rm -rf -- "$temporary_directory"
}
trap cleanup EXIT

render_run_script() {
    local source=$1
    local destination=$2
    sed \
        -e "s|@@SERVICE_USER@@|$service_user|g" \
        -e "s|@@REPOSITORY_ROOT@@|$repository_root|g" \
        -e "s|@@DOTNET_PATH@@|$dotnet_path|g" \
        "$source" >"$destination"
    chmod 0755 "$destination"
}

render_run_script "$template_directory/forex-intelligence-api.run.in" \
    "$temporary_directory/api-run"
render_run_script "$template_directory/forex-intelligence-bridge.run.in" \
    "$temporary_directory/bridge-run"

sudo install -d -o root -g root -m 0700 /etc/forex-intelligence
for environment_name in api bridge; do
    environment_path="/etc/forex-intelligence/$environment_name.env"
    if ! sudo test -e "$environment_path"; then
        sudo install -o root -g root -m 0600 \
            "$repository_root/deployment/systemd/$environment_name.env.example" "$environment_path"
        echo "Dibuat: $environment_path (masih berisi placeholder)"
    else
        echo "Dipertahankan: $environment_path"
    fi
done

for service_name in api bridge; do
    service_directory="/etc/sv/forex-intelligence-$service_name"
    sudo install -d -o root -g root -m 0755 "$service_directory/log"
    sudo install -o root -g root -m 0755 \
        "$temporary_directory/$service_name-run" "$service_directory/run"
    sed "s|@@LOG_DIRECTORY@@|/var/log/forex-intelligence/$service_name|g" \
        "$template_directory/log.run.in" >"$temporary_directory/$service_name-log-run"
    sudo install -o root -g root -m 0755 \
        "$temporary_directory/$service_name-log-run" "$service_directory/log/run"
done

echo
echo 'Definisi runit berhasil dipasang tetapi belum diaktifkan.'
echo 'Isi /etc/forex-intelligence/*.env, lalu ikuti deployment/runit/README.md.'
