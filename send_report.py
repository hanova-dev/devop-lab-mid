"""Build a JSON test report from pytest's results.xml and send it to the local receiver.

Used by the CI pipeline after the test step (for both passing and failing runs).
Usage: python send_report.py results.xml
"""
import json
import os
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

RECEIVER_URL = os.environ.get("RECEIVER_URL", "http://localhost:5001/report")


def read_tests(xml_path):
    tests = []
    if not os.path.exists(xml_path):
        return tests, "results.xml not found - tests could not run"
    root = ET.parse(xml_path).getroot()
    for case in root.iter("testcase"):
        result, message = "passed", None
        for tag in ("failure", "error"):
            node = case.find(tag)
            if node is not None:
                result = "failed"
                message = (node.get("message") or node.text or "").strip()
        if case.find("skipped") is not None:
            result = "skipped"
        tests.append({"name": case.get("name"), "result": result, "failure_message": message})
    return tests, None


def build_report(xml_path):
    tests, problem = read_tests(xml_path)
    passed = sum(1 for t in tests if t["result"] == "passed")
    failed = sum(1 for t in tests if t["result"] == "failed")
    status = "passed" if tests and failed == 0 and not problem else "failed"
    report = {
        "repository": os.environ.get("GITHUB_REPOSITORY", "local"),
        "branch": os.environ.get("GITHUB_REF_NAME", "local"),
        "commit_sha": os.environ.get("GITHUB_SHA", "local"),
        "run_id": os.environ.get("GITHUB_RUN_ID", "local"),
        "run_number": os.environ.get("GITHUB_RUN_NUMBER", "local"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tests": tests,
        "summary": {"total": len(tests), "passed": passed, "failed": failed},
        "overall_status": status,
    }
    if problem:
        report["error"] = problem
    return report


def send(report):
    body = json.dumps(report).encode("utf-8")
    req = urllib.request.Request(RECEIVER_URL, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        print("Receiver replied:", resp.status, resp.read().decode())


if __name__ == "__main__":
    xml_file = sys.argv[1] if len(sys.argv) > 1 else "results.xml"
    data = build_report(xml_file)
    print(json.dumps(data, indent=2))
    # Keep a copy in the workspace so the email step can attach it.
    with open("ci-report.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    try:
        send(data)
    except Exception as exc:  # receiver not running, wrong port, etc.
        print(f"ERROR: could not send report to {RECEIVER_URL}: {exc}")
        print("Make sure receiver.py is running (start_receiver.bat).")
        sys.exit(1)
