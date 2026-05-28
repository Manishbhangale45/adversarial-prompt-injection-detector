import json
import logging
import os
from logging.handlers import RotatingFileHandler
from urllib import error, request

from flask import Flask, flash, redirect, render_template, request as flask_request, url_for

from config import Config
from database import fetch_all_logs, fetch_dashboard_stats, fetch_recent_logs, init_db, insert_log
from detector import analyze_prompt, sanitize_prompt
from ml_model import load_detector_model


app = Flask(__name__)
app.config.from_object(Config)


def setup_logging():
    os.makedirs(os.path.dirname(Config.LOG_FILE), exist_ok=True)
    handler = RotatingFileHandler(Config.LOG_FILE, maxBytes=100_000, backupCount=3)
    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)


def call_openai_api(prompt):
    if not Config.OPENAI_API_KEY:
        return "Mock AI response: no OpenAI API key configured. The request was considered safe, so it would normally be forwarded to the model here."

    payload = json.dumps(
        {
            "model": Config.OPENAI_MODEL,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.4,
        }
    ).encode("utf-8")

    api_request = request.Request(
        url="https://api.openai.com/v1/chat/completions",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {Config.OPENAI_API_KEY}",
        },
        method="POST",
    )

    try:
        with request.urlopen(api_request, timeout=20) as response:
            response_data = json.loads(response.read().decode("utf-8"))
            return response_data["choices"][0]["message"]["content"].strip()
    except error.URLError as exc:
        app.logger.exception("OpenAI request failed: %s", exc)
        return "Mock AI response: the OpenAI request failed, so the app returned a safe fallback message."


def validate_prompt(prompt):
    if not prompt or not prompt.strip():
        return False, "Please enter a prompt before scanning."
    if len(prompt.strip()) < 3:
        return False, "Prompt is too short to analyze."
    return True, ""


def load_model_or_fallback():
    return load_detector_model(Config.MODEL_PATH)


init_db()
setup_logging()
MODEL = load_model_or_fallback()


@app.route("/")
def index():
    return render_template("index.html", scan_result=None, ai_response=None, prompt_value="")


@app.route("/scan", methods=["POST"])
def scan():
    prompt = sanitize_prompt(flask_request.form.get("prompt", ""))
    is_valid, message = validate_prompt(prompt)
    if not is_valid:
        flash(message, "danger")
        return render_template("index.html", scan_result=None, ai_response=None, prompt_value=prompt)

    analysis = analyze_prompt(prompt, MODEL)

    if analysis["blocked"]:
        ai_response = None
    else:
        ai_response = call_openai_api(prompt)

    insert_log(prompt, analysis["decision"], analysis["risk_score"])

    return render_template(
        "index.html",
        scan_result=analysis,
        ai_response=ai_response,
        prompt_value=prompt,
    )


@app.route("/dashboard")
def dashboard():
    stats = fetch_dashboard_stats()
    recent_logs = fetch_recent_logs(limit=8)
    return render_template(
        "dashboard.html",
        stats=stats,
        recent_logs=recent_logs,
        risk_distribution=json.dumps(stats["risk_bands"]),
    )


@app.route("/logs")
def logs():
    all_logs = fetch_all_logs()
    return render_template("logs.html", logs=all_logs)


@app.errorhandler(404)
def not_found(_error):
    return render_template("index.html", scan_result=None, ai_response=None, prompt_value=""), 404


@app.errorhandler(500)
def server_error(_error):
    return render_template("index.html", scan_result=None, ai_response=None, prompt_value=""), 500


if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
