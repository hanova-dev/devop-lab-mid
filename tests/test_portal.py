"""Automated tests for the submission portal (run with: python -m pytest -v)."""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import app  # noqa: E402


@pytest.fixture
def client(tmp_path):
    """Give every test a fresh, empty submissions file."""
    data_file = tmp_path / "submissions.json"
    app.config["TESTING"] = True
    app.config["DATA_FILE"] = str(data_file)
    with app.test_client() as c:
        yield c, data_file


def saved(data_file):
    if not data_file.exists():
        return []
    return json.loads(data_file.read_text(encoding="utf-8"))


VALID = {
    "name": "Hanan",
    "reg_no": "FA23-BSE-029",
    "title": "Lab Mid",
    "url": "https://github.com/hanova-dev/devop-lab-mid",
}


def test_valid_submission_is_saved_and_listed(client):
    c, data_file = client
    response = c.post("/", data=VALID)
    assert response.status_code == 200
    assert len(saved(data_file)) == 1
    page = c.get("/").get_data(as_text=True)
    assert "FA23-BSE-029" in page
    assert "https://github.com/hanova-dev/devop-lab-mid" in page


def test_missing_registration_number_is_rejected(client):
    c, data_file = client
    data = dict(VALID, reg_no="")
    response = c.post("/", data=data)
    assert response.status_code == 400
    assert "Registration number is required." in response.get_data(as_text=True)
    assert saved(data_file) == []


def test_invalid_url_is_rejected_and_not_saved(client):
    c, data_file = client
    data = dict(VALID, url="not-a-valid-url")
    response = c.post("/", data=data)
    assert response.status_code == 400
    assert "Submission URL is not valid" in response.get_data(as_text=True)
    assert saved(data_file) == []
