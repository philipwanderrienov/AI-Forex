#!/usr/bin/env bash

set -Eeuo pipefail

atomic_link() {
    local target=$1 link=$2
    ln -s -- "$target" "$link.next"
    mv -Tf -- "$link.next" "$link"
}

wait_ready() {
    local deadline=$((SECONDS + health_timeout))
    while (( SECONDS < deadline )); do
        if [[ $(curl --fail --silent --max-time 2 "$health_url") == Healthy ]]; then
            return 0
        fi
        sleep 1
    done
    return 1
}

recover_release() {
    trap - ERR INT TERM
    echo 'Activation failed; recovering the previous release.' >&2
    # Never start another process if the failed candidate could not be stopped.
    if ! sv -w 30 down "$service"; then
        echo 'STOP FAILED: inspect runit before manual recovery.' >&2
        exit 1
    fi
    if [[ -n $old_release ]]; then
        rm -f -- "$release_root/current.next"
        atomic_link "$old_release" "$release_root/current"
        if sv -w 30 up "$service" && wait_ready; then
            echo "Recovered: $old_release" >&2
        else
            echo 'ROLLBACK UNHEALTHY: inspect API and PostgreSQL logs.' >&2
        fi
    else
        rm -f -- "$release_root/current"
        echo 'No previous release; API remains stopped.' >&2
    fi
    exit 1
}

activate_release() {
    local candidate=$1
    old_release=
    if [[ -L $release_root/current ]]; then
        old_release=$(readlink -e "$release_root/current")
    fi
    if [[ $candidate == "$old_release" ]]; then
        echo 'Release is already current; checking readiness.'
        wait_ready
        return
    fi
    # Stop completion precedes switching: an old process cannot satisfy readiness.
    sv -w 30 down "$service"
    trap recover_release ERR INT TERM
    atomic_link "$candidate" "$release_root/current"
    sv -w 30 up "$service"
    wait_ready
    if [[ -n $old_release ]]; then
        atomic_link "$old_release" "$release_root/previous"
    fi
    trap - ERR INT TERM
    printf 'Active: %s (ready after %ss)\n' "$candidate" "$SECONDS"
}

main() {
    if [[ $EUID -ne 0 || $# -ne 1 ]]; then
        echo 'Usage: sudo bash scripts/activate-api-release.sh ARTIFACT_DIRECTORY|--rollback' >&2
        exit 1
    fi
    release_root=/opt/forex-intelligence/api
    service=/etc/service/forex-intelligence-api
    health_url=http://127.0.0.1:5204/health/ready
    health_timeout=60
    for command_name in flock sv curl readlink; do command -v "$command_name" >/dev/null; done
    [[ -d $service && -r /etc/forex-intelligence/api.env ]]
    # Refuse the old source launcher: otherwise health could validate the wrong code.
    grep -Fq '/opt/forex-intelligence/api/current' "$service/run"
    install -d -o root -g root -m 0755 "$release_root/releases"
    exec 9>"$release_root/.deploy.lock"
    flock -n 9 || { echo 'Another deployment is running.' >&2; exit 1; }
    [[ ! -e $release_root/current || -L $release_root/current ]]
    [[ ! -e $release_root/previous || -L $release_root/previous ]]
    if [[ -L $release_root/current ]]; then
        local current_target
        current_target=$(readlink -e "$release_root/current")
        [[ $current_target == "$release_root/releases/"* && -s $current_target/ForexIntelligence.Api.dll ]]
    fi
    rm -f -- "$release_root/current.next" "$release_root/previous.next"
    local candidate source release_id
    if [[ $1 == --rollback ]]; then
        candidate=$(readlink -f "$release_root/previous")
        [[ $candidate == "$release_root/releases/"* && -f $candidate/ForexIntelligence.Api.dll ]]
    else
        source=$(realpath -- "$1")
        for file in ForexIntelligence.Api.dll ForexIntelligence.Api.deps.json ForexIntelligence.Api.runtimeconfig.json REVISION; do
            [[ -s $source/$file ]] || { echo "Missing artifact: $file" >&2; exit 1; }
        done
        # Do not copy links or secret files into the release tree.
        [[ -z $(find "$source" -type l -print -quit) ]]
        [[ -z $(find "$source" -name '.env*' -print -quit) ]]
        release_id=$(basename -- "$source")
        [[ $release_id =~ ^[0-9]{8}T[0-9]{6}Z-[a-f0-9]+$ ]]
        candidate="$release_root/releases/$release_id"
        [[ ! -e $candidate ]] || { echo 'Release already exists; publish a new version.' >&2; exit 1; }
        install -d -m 0755 "$candidate"
        cp -R -- "$source/." "$candidate/"
        chown -R root:root "$candidate"
        chmod -R u=rwX,go=rX "$candidate"
    fi
    activate_release "$candidate"
}

if [[ ${BASH_SOURCE[0]} == "$0" ]]; then
    main "$@"
fi
