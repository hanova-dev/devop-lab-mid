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
| `tests/test_portal.py` | 3 automated tests (pytest) |
| `.github/workflows/ci.yml` | CI pipeline: runs tests on every push, sends report, deploys Pages |
| `send_report.py` | Turns pytest's `results.xml` into JSON and POSTs it to the receiver |
| `receiver.py` | Local HTTP receiver on port 5001, saves `test-report.json` |
| `docs/index.html` | Static demo published to GitHub Pages (bonus) |

## Requirements

- Python 3.10+ and Git
- `python -m pip install -r requirements.txt`

## 1. Run the application

```
python app.py
```
Open http://localhost:5000 (or double-click `start_app.bat`).

## 2. Run the tests

```
python -m pytest -v
```
(or double-click `run_tests.bat`). Tests:

| Test | Expected result |
|---|---|
| `test_valid_submission_is_saved_and_listed` | Saved and shown in the list |
| `test_missing_registration_number_is_rejected` | Rejected with "Registration number is required." |
| `test_invalid_url_is_rejected_and_not_saved` | Rejected, nothing saved |

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
5. `deploy-pages` job (bonus): only on `main` and only if `test` succeeded

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
  "summary": {"total": 3, "passed": 3, "failed": 0},
  "overall_status": "passed"
}
```

## Demo (pass → fail → fix)

1. Start `receiver.py` and the runner.
2. Push → all 3 tests pass → `test-report.json` shows `"overall_status": "passed"`.
3. Introduce a defect, e.g. in `app.py` make `is_valid_url` just `return True`. Push → the invalid URL
   test fails → pipeline is red → `test-report.json` shows `"failed": 1`.
4. Undo the defect and push → green again.

## GitHub Pages (bonus)

https://hanova-dev.github.io/devop-lab-mid/ — updated only when all tests pass on `main`.
