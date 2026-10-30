"""Live pipeline panel for the portal.

Shows the latest GitHub Actions run (test / email / deploy jobs), the local
test-report.json, and gives three demo buttons: Run Tests, Push Defect, Fix & Push.
GitHub is reached with the login Git already saved on this computer.
"""
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

from flask import Blueprint, jsonify

import demo_controller

REPO = os.environ.get("GITHUB_REPO", "hanova-dev/devop-lab-mid")
API = f"https://api.github.com/repos/{REPO}"
HERE = os.path.dirname(os.path.abspath(__file__))
REPORT_FILE = os.path.join(HERE, "test-report.json")

bp = Blueprint("pipeline", __name__)
_token = None
_cache = {"time": 0, "run": None, "error": None}


def github_token():
    """Read the GitHub token saved by Git Credential Manager (never shown or stored)."""
    global _token
    if _token is None:
        env = dict(os.environ, GIT_TERMINAL_PROMPT="0", GCM_INTERACTIVE="never")
        try:
            out = subprocess.run(["git", "credential", "fill"], input="protocol=https\nhost=github.com\n\n",
                                 capture_output=True, text=True, timeout=15, env=env).stdout
            _token = next((l.split("=", 1)[1] for l in out.splitlines() if l.startswith("password=")), "")
        except Exception:
            _token = ""
    return _token


def github(path, method="GET", body=None):
    headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    if github_token():
        headers["Authorization"] = f"Bearer {github_token()}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(path if path.startswith("http") else API + path,
                                 data=data, method=method, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as r:
        raw = r.read()
        return json.loads(raw) if raw else {}


def latest_run():
    """Latest workflow run and its jobs, cached for a few seconds."""
    if time.time() - _cache["time"] < 4:
        return _cache["run"], _cache["error"]
    try:
        runs = github("/actions/runs?per_page=1").get("workflow_runs", [])
        run = None
        if runs:
            r = runs[0]
            jobs = {j["name"]: {"status": j["status"], "conclusion": j["conclusion"]}
                    for j in github(r["jobs_url"]).get("jobs", [])}
            run = {"id": str(r["id"]), "number": r["run_number"], "title": r["display_title"],
                   "event": r["event"], "status": r["status"], "conclusion": r["conclusion"],
                   "sha": r["head_sha"][:7], "branch": r["head_branch"], "url": r["html_url"],
                   "jobs": jobs}
        _cache.update(time=time.time(), run=run, error=None)
    except Exception as exc:
        _cache.update(time=time.time(), error=f"GitHub not reachable: {exc}")
    return _cache["run"], _cache["error"]


def read_report():
    if not os.path.exists(REPORT_FILE):
        return None
    try:
        with open(REPORT_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def trigger_run():
    """Start the CI workflow for the current main branch (workflow_dispatch)."""
    github("/actions/workflows/ci.yml/dispatches", "POST", {"ref": "main"})
    _cache["time"] = 0


@bp.route("/api/status")
def status():
    run, error = latest_run()
    return jsonify(run=run, report=read_report(), error=error,
                   defect=demo_controller.has_defect(), busy=demo_controller.is_busy())


@bp.route("/api/run-tests", methods=["POST"])
def run_tests():
    try:
        trigger_run()
        return jsonify(ok=True, message="Test run requested on GitHub Actions.")
    except Exception as exc:
        return jsonify(ok=False, message=f"Could not start the run: {exc}"), 500


@bp.route("/api/demo/<action>", methods=["POST"])
def demo(action):
    if action not in ("break", "fix"):
        return jsonify(ok=False, message="Unknown action"), 400
    # Separate process, so the commit and push finish even if the page is closed.
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    subprocess.Popen([sys.executable, os.path.join(HERE, "demo_controller.py"), action],
                     cwd=HERE, creationflags=flags)
    _cache["time"] = 0
    text = "Defect is being committed and pushed..." if action == "break" else "Fix is being committed and pushed..."
    return jsonify(ok=True, message=text)
