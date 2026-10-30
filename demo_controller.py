"""Demo helper used by the portal buttons (and usable by hand).

python demo_controller.py break  -> is_valid_url() accepts any URL, commit and push (tests fail)
python demo_controller.py fix    -> restore the correct check, commit and push (tests pass)
"""
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
APP = HERE / "app.py"
LOCK = HERE / ".demo-busy"
LOG = HERE / "demo-log.txt"
GOOD = '    return parsed.scheme in ("http", "https") and bool(parsed.netloc)'
BAD = '    return True  # DEFECT: accepts any URL'


def has_defect():
    return BAD in APP.read_text(encoding="utf-8")


def is_busy():
    return LOCK.exists()


def log(msg):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now():%H:%M:%S}] {msg}\n")


def git(*args):
    r = subprocess.run(["git", *args], cwd=HERE, capture_output=True, text=True)
    log(f"git {' '.join(args)} -> {r.returncode} {r.stdout.strip()} {r.stderr.strip()}")
    return r.returncode


def main(action):
    LOCK.write_text(action)
    try:
        text = APP.read_text(encoding="utf-8")
        if action == "break":
            new, msg = text.replace(GOOD, BAD), "Demo: introduce defect - URL validation accepts any URL"
        else:
            new, msg = text.replace(BAD, GOOD), "Demo: fix defect - restore URL validation"
        if new == text:
            log(f"{action}: nothing to change")
            return
        APP.write_text(new, encoding="utf-8")
        git("add", "app.py")
        git("commit", "-m", msg)
        git("push")
    finally:
        LOCK.unlink(missing_ok=True)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "fix")
