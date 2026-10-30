# Assignment Submission Portal with Automated Testing

CSC418 DevOps — Lab Midterm  
Student: Muhammad Abdul Hanan (Hanan bin Saleh)

A small web portal (Python + Flask) where students submit their name, registration number,
assignment title and a submission URL. Every push to GitHub runs the automated tests in a
GitHub Actions pipeline, and the test report is sent to a local receiver that saves it as
`test-report.json`.

## Project files

| File | Purpose |
|---|---|
| `app.py`, `templates/index.html` | The portal (form, validation, saving, list of submissions) |
| `pipeline.py` | Live pipeline panel: reads the latest GitHub run and `test-report.json` |
| `demo_controller.py` | Push defect / Fix & push for the demo |
| `tests/test_portal.py` | 8 automated tests (pytest) |
| `.github/workflows/ci.yml` | CI pipeline: runs tests on every push, sends report, deploys Pages |
| `send_report.py` | Turns pytest's `results.xml` into JSON and POSTs it to the receiver |
| `receiver.py` | Local HTTP receiver on port 5001, saves `test-report.json` |
| `send_email.py` | Emails the test report after every run (bonus) |
| `docs/index.html` | Static demo published to GitHub Pages (bonus) |

## Requirements

- Python 3.10+ and Git
- `python -m pip install -r requirements.txt`

## 1. Run the application

```
python app.py
```
Open http://localhost:5000 (or double-click `start_app.bat`).

The page has two parts:
- **Submit an assignment** – the form and the list of saved submissions. A valid submission also
  starts the CI checks on GitHub Actions automatically.
- **Pipeline checks** – live view (refreshes every 4 s) of the latest GitHub Actions run: Push →
  Tests (laptop) → Report → localhost → Email → GitHub Pages, the pass/fail counts and every test
  from `test-report.json`. Buttons: **Run tests** (workflow_dispatch), **Push defect** and
  **Fix & push** (`demo_controller.py` edits `app.py`, commits and pushes).
  `pipeline.py` talks to the GitHub API using the login Git already saved on the computer.

## 2. Run the tests

```
python -m pytest -v
```
(or double-click `run_tests.bat`). 8 tests:

| Test | Expected result |
|---|---|
| `test_valid_submission_is_saved_and_listed` | Saved and shown in the list |
| `test_missing_registration_number_is_rejected` | Rejected with "Registration number is required." |
| `test_invalid_url_is_rejected_and_not_saved` | Rejected, nothing saved |
| `test_blank_or_whitespace_fields_are_rejected` | Empty or spaces-only fields rejected |
| `test_unsafe_or_incomplete_urls_are_rejected` | `ftp://`, `javascript:`, no scheme, no domain rejected |
| `test_input_is_trimmed_before_saving` | Extra spaces removed before saving |
| `test_multiple_submissions_are_all_listed` | Several submissions saved and listed |
| `test_invalid_attempt_does_not_change_existing_records` | A bad attempt leaves saved data unchanged |

## 3. Start the report receiver

```
python receiver.py
```
(or double-click `start_receiver.bat`). It listens on `http://localhost:5001/report` and writes
`test-report.json` in this folder (plus a copy per run in `reports/`). Keep it running.

## 4. CI pipeline and how the report reaches localhost

A GitHub-hosted runner's `localhost` is the runner itself, not my laptop. So the `test` job uses a
**self-hosted runner installed on my laptop** (`runs-on: self-hosted`). Because the job runs on my
laptop, `send_report.py` can POST straight to `http://localhost:5001/report`. No tunnel is needed.

Pipeline steps (on every push):
1. Checkout the pushed commit
2. Install dependencies
3. Run tests → `results.xml` (a failed test fails this step and the job)
4. Send report (`if: always()`, so it runs for passing **and** failing runs)
5. Upload `ci-report.json` as an artifact (`if: always()`)
6. `email-report` job (bonus, `if: always()`): on a GitHub-hosted runner, emails the report
7. `deploy-pages` job (bonus): only on `main` and only if `test` succeeded

### Start the self-hosted runner

The runner is installed in `D:\actions-runner`. Start it with:
```
cd /d D:\actions-runner
run.cmd
```
(or double-click `start_runner.bat`). It should show "Listening for Jobs".

To install it on another computer: GitHub repo → Settings → Actions → Runners → New self-hosted
runner → Windows, and follow the commands shown.

## Report format (`test-report.json`)

```json
{
  "repository": "hanova-dev/devop-lab-mid",
  "branch": "main",
  "commit_sha": "...",
  "run_id": "...",
  "timestamp": "2026-10-30T10:00:00+00:00",
  "tests": [{"name": "...", "result": "passed", "failure_message": null}],
  "summary": {"total": 8, "passed": 8, "failed": 0},
  "overall_status": "passed"
}
```

## Demo (pass → fail → fix)

1. Start `receiver.py` and the runner.
2. Push → all 8 tests pass → `test-report.json` shows `"overall_status": "passed"`.
3. Introduce a defect, e.g. in `app.py` make `is_valid_url` just `return True`. Push → the two URL
   tests fail → pipeline is red → `test-report.json` shows `"failed": 2`.
4. Undo the defect and push → green again.

## Email report (bonus)

`send_email.py` sends the report (commit, overall result, counts, each test, JSON attached) after
every run through Gmail SMTP. Configure in GitHub → Settings → Secrets and variables → Actions:

| Name | Type | Value |
|---|---|---|
| `SMTP_USER` | Secret | Sender Gmail address |
| `SMTP_PASSWORD` | Secret | Gmail App Password (not the normal password) |
| `REPORT_EMAIL_TO` | Variable | Receiver address(es), comma separated |

The `email-report` job runs on a GitHub-hosted runner (`ubuntu-latest`), so email delivery does not
depend on my laptop; it downloads the report artifact from the `test` job and sends it.
If the secrets are missing, the step prints "Email skipped" instead of failing.

## GitHub Pages (bonus)

https://hanova-dev.github.io/devop-lab-mid/ — updated only when all tests pass on `main`.
