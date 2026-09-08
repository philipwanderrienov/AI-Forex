#!/usr/bin/env bash

set -euo pipefail
repository_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repository_root"
release_id="$(date -u +%Y%m%dT%H%M%SZ)-$(git rev-parse --short HEAD)"
output="$repository_root/artifacts/api/$release_id"
mkdir -p "$(dirname -- "$output")"
mkdir "$output"
# Publish before touching the running service. Framework-dependent, built on target Linux.
dotnet publish src/ForexIntelligence.Api/ForexIntelligence.Api.csproj \
    --configuration Release --self-contained false -p:UseAppHost=false \
    --output "$output"
git rev-parse HEAD >"$output/REVISION"
git diff --quiet HEAD -- || printf '%s\n' 'Working tree had tracked changes.' >>"$output/REVISION"
printf 'Published: %s\n' "$output"
