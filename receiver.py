"""Local HTTP receiver for CI test reports.

Listens on http://localhost:5001/report. Every report the pipeline POSTs is saved as
test-report.json (latest run) and also copied to reports/report-<run_id>.json (history).
Start it with: python receiver.py
"""
import json
import os
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = int(os.environ.get("RECEIVER_PORT", "5001"))
HERE = os.path.dirname(os.path.abspath(__file__))
REPORT_FILE = os.path.join(HERE, "test-report.json")
HISTORY_DIR = os.path.join(HERE, "reports")


class ReportHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/report":
            self.send_response(404)
            self.end_headers()
            return
        length = int(self.headers.get("Content-Length", 0))
        try:
            report = json.loads(self.rfile.read(length))
        except json.JSONDecodeError:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"invalid JSON")
            return

        with open(REPORT_FILE, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        os.makedirs(HISTORY_DIR, exist_ok=True)
        run_id = report.get("run_id", datetime.now().strftime("%Y%m%d%H%M%S"))
        with open(os.path.join(HISTORY_DIR, f"report-{run_id}.json"), "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        s = report.get("summary", {})
        print(f"[{datetime.now():%H:%M:%S}] Report saved: run {run_id}, "
              f"status={report.get('overall_status')}, passed={s.get('passed')}, failed={s.get('failed')}")
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"saved to test-report.json")

    def do_GET(self):
        # Simple health check: open http://localhost:5001 in a browser.
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Receiver is running. POST reports to /report")

    def log_message(self, *args):
        pass  # keep the console clean


if __name__ == "__main__":
    print(f"Receiver listening on http://localhost:{PORT}/report")
    print(f"Reports will be saved to {REPORT_FILE}")
    HTTPServer(("127.0.0.1", PORT), ReportHandler).serve_forever()
