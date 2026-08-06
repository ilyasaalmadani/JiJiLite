#!/usr/bin/env python3

import subprocess
import sys
from pathlib import Path

ROOT = Path.home() / "JiJiLite"
VERSION_FILE = ROOT / "version"
BACKUP_SCRIPT = ROOT / "core" / "backup.sh"
DOCTOR = ROOT / "core" / "doctor.py"
SELFTEST = ROOT / "core" / "selftest.py"

IGNORED_DIRTY_PREFIXES = (
    "?? memory/",
    "?? cache/",
    "?? logs/",
    "?? backups/",
    "?? releases/",
)

def run(command, capture=False, check=True):
    result = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        capture_output=capture,
    )

    if check and result.returncode != 0:
        message = (
            result.stderr.strip()
            if capture
            else "Perintah gagal"
        )
        raise RuntimeError(message)

    return result.stdout.strip() if capture else result.returncode

def current_version():
    return VERSION_FILE.read_text().strip()

def real_local_changes():
    output = run(
        ["git", "status", "--porcelain"],
        capture=True,
    )

    changes = []
    for line in output.splitlines():
        if not any(
            line.startswith(prefix)
            for prefix in IGNORED_DIRTY_PREFIXES
        ):
            changes.append(line)

    return changes

old_version = current_version()
old_commit = run(
    ["git", "rev-parse", "HEAD"],
    capture=True,
)

print("╭─ JiJi Lite Update ─────────────────────╮")
print(f"│ Current : v{old_version:<27}│")
print("╰────────────────────────────────────────╯")
print()
print("Checking GitHub...")

try:
    run(["git", "fetch", "origin", "main"])

    remote_version = run(
        ["git", "show", "origin/main:version"],
        capture=True,
    ).strip()

    remote_commit = run(
        ["git", "rev-parse", "origin/main"],
        capture=True,
    )
except Exception as error:
    print(f"✗ Gagal mengecek update: {error}")
    sys.exit(1)

print(f"Latest  : v{remote_version}")

if old_commit == remote_commit:
    print()
    print("✓ JiJi Lite sudah versi terbaru.")
    sys.exit(0)

changes = real_local_changes()

if changes:
    print()
    print("✗ Update dibatalkan karena ada perubahan kode lokal:")
    for item in changes:
        print(" ", item)
    print()
    print("Publikasikan atau simpan perubahan tersebut terlebih dahulu.")
    sys.exit(1)

print()
print("Creating backup...")

try:
    if BACKUP_SCRIPT.exists():
        run([str(BACKUP_SCRIPT)])
except Exception as error:
    print(f"✗ Backup gagal: {error}")
    sys.exit(1)

print()
print("Installing update...")

try:
    run(["git", "pull", "--ff-only", "origin", "main"])

    if SELFTEST.exists():
        run(["python3", "-m", "core.selftest"])

    if DOCTOR.exists():
        run(["python3", str(DOCTOR)])

except Exception as error:
    print()
    print(f"✗ Update gagal: {error}")
    print("Rollback ke commit sebelumnya...")

    subprocess.run(
        ["git", "reset", "--hard", old_commit],
        cwd=ROOT,
    )

    print("✓ Rollback selesai.")
    sys.exit(1)

new_version = current_version()

print()
print(f"✓ Update selesai: v{old_version} → v{new_version}")
print("✓ Self-test dan System Doctor berhasil.")
