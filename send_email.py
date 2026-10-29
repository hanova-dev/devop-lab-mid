"""Email the CI test report (bonus task).

Runs in the pipeline after every run (passing or failing) and sends the report to a
configurable address. Credentials come only from environment variables, which the
workflow fills from GitHub Actions secrets:

  SMTP_USER        sender Gmail address                (secret)
  SMTP_PASSWORD    Gmail App Password                  (secret)
  REPORT_EMAIL_TO  receiver address(es), comma separated (repository variable)
  SMTP_HOST / SMTP_PORT   optional, default smtp.gmail.com / 587

Usage: python send_email.py ci-report.json
"""
import json
import os
import smtplib
import sys
from email.message import EmailMessage


def build_message(report, sender, receivers):
    s = report["summary"]
    status = report["overall_status"].upper()
    sha = report["commit_sha"]
    run_url = "{}/{}/actions/runs/{}".format(
        os.environ.get("GITHUB_SERVER_URL", "https://github.com"), report["repository"], report["run_id"])

    lines = [
        f"CSC418 DevOps Lab Mid - automated test report",
        "",
        f"Overall result : {status}",
        f"Tests          : total {s['total']} | passed {s['passed']} | failed {s['failed']}",
        "",
        f"Repository     : {report['repository']}",
        f"Branch         : {report['branch']}",
        f"Commit         : {sha}",
        f"Run ID         : {report['run_id']} (run #{report.get('run_number')})",
        f"Run link       : {run_url}",
        f"Executed at    : {report['timestamp']}",
        "",
        "Individual results:",
    ]
    for t in report["tests"]:
        lines.append(f"  [{t['result'].upper():6}] {t['name']}")
        if t.get("failure_message"):
            lines.append(f"           reason: {t['failure_message'].splitlines()[0]}")
    lines += ["", "The full JSON report is attached (test-report.json)."]

    msg = EmailMessage()
    msg["Subject"] = f"[{status}] CSC418 Lab Mid | run {report['run_id']} | {sha[:7]} | {s['passed']}/{s['total']} passed"
    msg["From"] = sender
    msg["To"] = ", ".join(receivers)
    msg.set_content("\n".join(lines))
    msg.add_attachment(json.dumps(report, indent=2).encode("utf-8"),
                       maintype="application", subtype="json", filename="test-report.json")
    return msg


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "ci-report.json"
    user = os.environ.get("SMTP_USER", "").strip()
    password = os.environ.get("SMTP_PASSWORD", "").replace(" ", "")
    to = os.environ.get("REPORT_EMAIL_TO", "").strip() or user
    if not user or not password:
        print("Email skipped: SMTP_USER / SMTP_PASSWORD secrets are not set.")
        return
    if not os.path.exists(path):
        print(f"ERROR: {path} not found, nothing to email.")
        sys.exit(1)

    with open(path, encoding="utf-8") as f:
        report = json.load(f)
    receivers = [a.strip() for a in to.split(",") if a.strip()]
    msg = build_message(report, user, receivers)

    host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    port = int(os.environ.get("SMTP_PORT", "587"))
    with smtplib.SMTP(host, port, timeout=30) as smtp:
        if os.environ.get("SMTP_STARTTLS", "1") == "1":
            smtp.starttls()
        smtp.login(user, password)
        smtp.send_message(msg)
    print(f"Email sent to {', '.join(receivers)}: {msg['Subject']}")


if __name__ == "__main__":
    main()
