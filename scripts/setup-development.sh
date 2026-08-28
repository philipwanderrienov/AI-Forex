#!/usr/bin/env bash

set -euo pipefail

script_directory=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
project_path="$script_directory/../src/ForexIntelligence.Api"

read_default() {
    local label=$1
    local default_value=$2
    local value

    read -r -p "$label [$default_value]: " value
    printf '%s' "${value:-$default_value}"
}

set_project_secret() {
    local key=$1
    local value=$2

    dotnet user-secrets set "$key" "$value" --project "$project_path" >/dev/null
}

cleanup() {
    unset database_password bootstrap_password connection_string jwt_signing_key password_hash
}

trap cleanup EXIT

command -v dotnet >/dev/null 2>&1 || {
    echo 'dotnet tidak ditemukan di PATH.' >&2
    exit 1
}
command -v openssl >/dev/null 2>&1 || {
    echo 'openssl tidak ditemukan di PATH.' >&2
    exit 1
}

echo 'Forex Intelligence development setup'
echo 'Nilai rahasia disimpan di .NET User Secrets dan tidak ditulis ke repository.'

database_host=$(read_default 'PostgreSQL host' '127.0.0.1')
database_port=$(read_default 'PostgreSQL port' '5432')
database_name=$(read_default 'Database name' 'forex_intelligence')
database_user=$(read_default 'Database user' 'forex_app')
read -r -s -p 'Database password (kosongkan jika koneksi lokal tidak memerlukannya): ' database_password
echo
connection_string="Host=$database_host;Port=$database_port;Database=$database_name;Username=$database_user"
if [[ -n $database_password ]]; then
    escaped_database_password=${database_password//\"/\"\"}
    connection_string="$connection_string;Password=\"$escaped_database_password\""
fi

bootstrap_username=$(read_default 'Bootstrap admin username' 'admin')
read -r -s -p 'Bootstrap admin password: ' bootstrap_password
echo
if [[ -z $bootstrap_password ]]; then
    echo 'Bootstrap password tidak boleh kosong.' >&2
    exit 1
fi

password_hash=$(printf '%s\n' "$bootstrap_password" |
    dotnet run --project "$project_path" -- --hash-password |
    awk '/^pbkdf2-sha256\$/{value=$0} END{print value}')
if [[ -z $password_hash ]]; then
    echo 'Output bootstrap password hash tidak ditemukan.' >&2
    exit 1
fi

jwt_signing_key=$(openssl rand -base64 48)
bridge_api_key=$(openssl rand -base64 48)

set_project_secret 'ConnectionStrings:PostgreSql' "$connection_string"
set_project_secret 'Jwt:SigningKey' "$jwt_signing_key"
set_project_secret 'BridgeAuthentication:ApiKey' "$bridge_api_key"
set_project_secret 'BootstrapUser:Username' "$bootstrap_username"
set_project_secret 'BootstrapUser:PasswordHash' "$password_hash"
set_project_secret 'BootstrapUser:Role' 'ADMIN'

echo
echo 'Development secrets berhasil dikonfigurasi.'
echo 'Simpan bridge API key berikut di password manager, lalu gunakan sebagai'
echo 'MT5_BRIDGE_BACKEND_API_KEY pada laptop server:'
echo "$bridge_api_key"
echo
echo 'Jangan kirim key tersebut ke chat dan jangan commit ke Git.'
