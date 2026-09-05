#!/usr/bin/env bash

set -euo pipefail

script_directory=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
repository_root=$(cd -- "$script_directory/.." && pwd)
template_directory="$repository_root/deployment/runit"
service_user=${SUDO_USER:-${USER:?USER is not set}}
dotnet_path=$(command -v dotnet || true)
pg_ctlcluster_path=$(command -v pg_ctlcluster || true)

if [[ $(ps -p 1 -o comm= | tr -d ' ') != runit ]]; then
    echo 'Installer ini hanya untuk server antiX yang sedang memakai runit.' >&2
    exit 1
fi
if [[ -z $dotnet_path ]]; then
    echo 'dotnet tidak ditemukan di PATH.' >&2
    exit 1
fi
if [[ -z $pg_ctlcluster_path ]]; then
    echo 'pg_ctlcluster tidak ditemukan di PATH.' >&2
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

mapfile -t postgresql_clusters < <(pg_lsclusters --no-header | awk '$3 == 5432 { print $1 " " $2 " " $5 }')
if [[ ${#postgresql_clusters[@]} -ne 1 ]]; then
    echo 'Harus ada tepat satu cluster PostgreSQL pada port 5432.' >&2
    exit 1
fi
read -r postgresql_version postgresql_cluster postgresql_owner <<<"${postgresql_clusters[0]}"
if [[ $postgresql_owner != postgres ]]; then
    echo 'Cluster PostgreSQL port 5432 harus dimiliki user postgres.' >&2
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
sed \
    -e "s|@@PG_CTLCLUSTER_PATH@@|$pg_ctlcluster_path|g" \
    -e "s|@@POSTGRESQL_VERSION@@|$postgresql_version|g" \
    -e "s|@@POSTGRESQL_CLUSTER@@|$postgresql_cluster|g" \
    "$template_directory/forex-intelligence-postgresql.run.in" \
    >"$temporary_directory/postgresql-run"
chmod 0755 "$temporary_directory/postgresql-run"
sed \
    -e "s|@@PG_CTLCLUSTER_PATH@@|$pg_ctlcluster_path|g" \
    -e "s|@@POSTGRESQL_VERSION@@|$postgresql_version|g" \
    -e "s|@@POSTGRESQL_CLUSTER@@|$postgresql_cluster|g" \
    "$template_directory/forex-intelligence-postgresql.stop.in" \
    >"$temporary_directory/postgresql-stop"
chmod 0755 "$temporary_directory/postgresql-stop"

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

sudo install -d -o root -g root -m 0755 \
    /etc/sv/forex-intelligence-postgresql/control
for control_name in d t; do
    sudo install -o root -g root -m 0755 \
        "$temporary_directory/postgresql-stop" \
        "/etc/sv/forex-intelligence-postgresql/control/$control_name"
done

for service_name in postgresql api bridge; do
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
