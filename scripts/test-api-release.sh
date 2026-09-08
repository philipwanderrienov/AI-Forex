#!/usr/bin/env bash

# Isolated activation/recovery tests; no root, broker, database, or runit needed.
set -euo pipefail
script_directory=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
test_root=$(mktemp -d)
trap 'rm -rf -- "$test_root"' EXIT

for scenario in success unhealthy start_failure first_failure stop_failure rollback_failure; do
    directory="$test_root/$scenario"
    mkdir -p "$directory/releases/old" "$directory/releases/new"
    if [[ $scenario != first_failure ]]; then
        ln -s "$directory/releases/old" "$directory/current"
    fi
    set +e
    bash -s -- "$script_directory" "$directory" "$scenario" <<'TEST'
source "$1/activate-api-release.sh"
release_root=$2
scenario=$3
service=mock-api
health_url=http://unused
health_timeout=1
sv() {
    echo "$*" >>"$release_root/commands"
    if [[ $scenario == stop_failure && $3 == down ]]; then return 1; fi
    if [[ $scenario == start_failure && $3 == up && $(readlink "$release_root/current") == */new ]]; then return 1; fi
    return 0
}
curl() {
    if [[ $scenario == rollback_failure ]]; then return 22; fi
    if [[ $scenario != success && $(readlink "$release_root/current") == */new ]]; then return 22; fi
    printf Healthy
}
activate_release "$release_root/releases/new"
TEST
    result=$?
    set -e
    case $scenario in
        success)
            [[ $result == 0 ]]
            [[ $(readlink "$directory/current") == "$directory/releases/new" ]]
            [[ $(readlink "$directory/previous") == "$directory/releases/old" ]]
            ;;
        first_failure)
            [[ $result != 0 && ! -e $directory/current && ! -L $directory/current ]]
            [[ $(tail -n 1 "$directory/commands") == '-w 30 down mock-api' ]]
            ;;
        *)
            [[ $result != 0 ]]
            [[ $(readlink "$directory/current") == "$directory/releases/old" ]]
            ;;
    esac
    echo "PASS: $scenario"
done
