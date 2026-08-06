#!/usr/bin/env python3

import sys
import subprocess
from pathlib import Path

ROOT = Path.home() / "JiJiLite"

args = sys.argv[1:]

if len(args) == 0:
    subprocess.run(["python3", str(ROOT/"main.py")])
    sys.exit()

cmd = args[0].lower()

if cmd == "doctor":
    subprocess.run(["python3", str(ROOT/"core/doctor.py")])

elif cmd == "update":
    subprocess.run(["python3", str(ROOT/"core/update.py")])

elif cmd == "version":
    print((ROOT/"version").read_text().strip())

elif cmd == "about":
    print("JiJi Lite")
    print("AI Workspace")
    print("Version :", (ROOT/"version").read_text().strip())

else:
    subprocess.run(["python3", str(ROOT/"main.py"), *args])
