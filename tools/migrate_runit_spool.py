"""Copy a stopped runit bridge spool outside the checkout; never delete the source."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile


def manifest(directory):
    if directory.is_symlink() or not directory.is_dir():
        raise ValueError("Spool must be an existing real directory")
    result = {}
    for path in sorted(directory.rglob("*")):
        if path.is_symlink():
            raise ValueError("Symlinks are not supported in spool")
        if path.is_file():
            result[str(path.relative_to(directory))] = hashlib.sha256(path.read_bytes()).hexdigest()
        elif not path.is_dir():
            raise ValueError("Special files are not supported in spool")
    return result


def verified_copy(source, destination):
    if destination.exists() or destination.is_symlink():
        raise ValueError("Destination already exists; inspect it before retrying")
    before = manifest(source)
    shutil.copytree(source, destination)
    if before != manifest(source) or before != manifest(destination):
        raise ValueError("Spool changed or copy verification failed; leave bridge stopped")
    return before


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Stop bridge, verify copy and replace launcher")
    args = parser.parse_args()
    repository = Path(__file__).resolve().parents[1]
    source = repository / "mt5-bridge/spool"
    destination = Path("/var/lib/forex-intelligence/spool")
    launcher = Path("/etc/sv/forex-intelligence-bridge/run")
    original = launcher.read_text()
    old_line = "export MT5_BRIDGE_SPOOL_PATH='" + str(source) + "'"
    new_line = "export MT5_BRIDGE_SPOOL_PATH='" + str(destination) + "'"
    if original.count(old_line) != 1:
        raise SystemExit("Launcher does not contain the expected repository spool assignment; inspect manually.")
    if destination.exists() or destination.is_symlink():
        raise SystemExit("Destination already exists; no overwrite or merge attempted.")
    files = manifest(source)
    print(json.dumps({"source": str(source), "destination": str(destination),
                      "files": len(files), "apply": args.apply}))
    if not args.apply:
        return
    if os.geteuid() != 0:
        raise SystemExit("Run --apply with sudo.")
    # No automatic restart on failure: preserve source, partial copy and diagnostics.
    subprocess.run(["sv", "-w", "20", "down", "forex-intelligence-bridge"], check=True)
    parent = destination.parent
    parent.mkdir(parents=True, exist_ok=True)
    if parent.is_symlink():
        raise SystemExit("Destination parent must not be a symlink")
    backup = Path(tempfile.mkdtemp(prefix="spool-migration-", dir=parent))
    (backup / "run.before").write_text(original)
    hashes = verified_copy(source, destination)
    for path in [destination, *destination.rglob("*")]:
        prior = source / path.relative_to(destination)
        metadata = prior.stat()
        os.chown(path, metadata.st_uid, metadata.st_gid)
    (backup / "manifest.json").write_text(json.dumps(hashes, indent=2) + "\n")
    # Refuse racing edits of the launcher.
    if launcher.read_text() != original:
        raise SystemExit("Launcher changed during migration; bridge remains stopped")
    replacement = launcher.with_name("run.spool-migration")
    with replacement.open("x") as stream:
        stream.write(original.replace(old_line, new_line))
        stream.flush()
        os.fsync(stream.fileno())
    replacement.chmod(launcher.stat().st_mode & 0o777)
    os.replace(replacement, launcher)
    print("Verified copy and launcher installed. Source retained. Backup:", backup)
    subprocess.run(["sv", "up", "forex-intelligence-bridge"], check=True)
    print("Check /health and quarantine count. sv up alone does not prove readiness.")


if __name__ == "__main__":
    main()
