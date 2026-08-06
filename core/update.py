#!/usr/bin/env python3

import subprocess
import sys
from pathlib import Path

ROOT = Path.home() / "JiJiLite"
VERSION_FILE = ROOT / "version"
BACKUP = ROOT / "core" / "backup.sh"

def run(command, capture=False):
    result = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        capture_output=capture
    )
    if result.returncode != 0:
        if capture:
            print(result.stderr.strip())
        sys.exit(result.returncode)
    return result.stdout.strip() if capture else ""

local_version = VERSION_FILE.read_text().strip()

print("╭─ JiJi Lite Update ─────────────────────╮")
print(f"│ Current : v{local_version:<27}│")
print("╰────────────────────────────────────────╯")
print()
print("Checking GitHub...")

run(["git", "fetch", "origin", "main"])

remote_version = run(
    ["git", "show", "origin/main:version"],
    capture=True
).strip()

print(f"Latest  : v{remote_version}")

local_commit = run(["git", "rev-parse", "HEAD"], capture=True)
remote_commit = run(["git", "rev-parse", "origin/main"], capture=True)

if local_commit == remote_commit:
    print()
    print("✓ JiJi Lite sudah versi terbaru.")
    sys.exit(0)

changes = run(["git", "status", "--porcelain"], capture=True)

if changes:
    print()
    print("Update dibatalkan: ada perubahan lokal yang belum dipublikasikan.")
    print("Jalankan: jiji publish")
    sys.exit(1)

print()
print("Creating backup...")

if BACKUP.exists():
    run([str(BACKUP)])

print()
print("Installing update...")

run(["git", "pull", "--ff-only", "origin", "main"])

installer = ROOT / "install.sh"
if installer.exists():
    run([str(installer)])

new_version = VERSION_FILE.read_text().strip()

print()
print(f"✓ Update selesai: v{local_version} → v{new_version}")
print("Jalankan kembali JiJi Lite.")
