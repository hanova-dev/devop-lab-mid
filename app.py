"""Assignment Submission Portal (CSC418 DevOps Lab Mid).

Students enter name, registration number, assignment title and a submission URL.
Valid submissions are saved to a JSON file and shown in a list.
"""
import json
import os
from datetime import datetime
from urllib.parse import urlparse

from flask import Flask, render_template, request

app = Flask(__name__)
# Where submissions are stored. Tests point this to a temporary file.
app.config["DATA_FILE"] = os.path.join(os.path.dirname(os.path.abspath(__file__)), "submissions.json")

REQUIRED_FIELDS = {
    "name": "Name",
    "reg_no": "Registration number",
    "title": "Assignment title",
    "url": "Submission URL",
}


def is_valid_url(url):
    """A valid URL must start with http:// or https:// and have a domain."""
    parsed = urlparse(url)
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def validate(form):
    """Return a list of error messages. Empty list means the data is valid."""
    errors = []
    for field, label in REQUIRED_FIELDS.items():
        if not form.get(field, "").strip():
            errors.append(f"{label} is required.")
    url = form.get("url", "").strip()
    if url and not is_valid_url(url):
        errors.append("Submission URL is not valid. It must start with http:// or https://")
    return errors


def load_submissions():
    path = app.config["DATA_FILE"]
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_submission(entry):
    submissions = load_submissions()
    submissions.append(entry)
    with open(app.config["DATA_FILE"], "w", encoding="utf-8") as f:
        json.dump(submissions, f, indent=2)


@app.route("/", methods=["GET", "POST"])
def index():
    errors = []
    message = ""
    status = 200
    if request.method == "POST":
        errors = validate(request.form)
        if errors:
            status = 400
        else:
            save_submission({
                "name": request.form["name"].strip(),
                "reg_no": request.form["reg_no"].strip(),
                "title": request.form["title"].strip(),
                "url": request.form["url"].strip(),
                "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            })
            message = "Submission saved successfully."
    return render_template(
        "index.html",
        errors=errors,
        message=message,
        form=request.form,
        submissions=load_submissions(),
    ), status


if __name__ == "__main__":
    app.run(debug=True, port=5000)
