import sqlite3
from contextlib import contextmanager
from datetime import datetime

from config import Config


@contextmanager
def get_connection():
    connection = sqlite3.connect(Config.DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def init_db():
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prompt TEXT NOT NULL,
                prediction TEXT NOT NULL,
                risk_score INTEGER NOT NULL,
                timestamp TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def insert_log(prompt, prediction, risk_score):
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO logs (prompt, prediction, risk_score, timestamp)
            VALUES (?, ?, ?, ?)
            """,
            (prompt, prediction, int(risk_score), datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")),
        )


def fetch_all_logs():
    with get_connection() as connection:
        rows = connection.execute("SELECT * FROM logs ORDER BY id DESC").fetchall()
    return [dict(row) for row in rows]


def fetch_recent_logs(limit=5):
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM logs ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def fetch_dashboard_stats():
    with get_connection() as connection:
        total_prompts = connection.execute("SELECT COUNT(*) AS total FROM logs").fetchone()["total"]
        blocked_prompts = connection.execute(
            "SELECT COUNT(*) AS total FROM logs WHERE prediction = 'Blocked'"
        ).fetchone()["total"]
        review_prompts = connection.execute(
            "SELECT COUNT(*) AS total FROM logs WHERE prediction = 'Review'"
        ).fetchone()["total"]
        safe_prompts = connection.execute(
            "SELECT COUNT(*) AS total FROM logs WHERE prediction = 'Allowed'"
        ).fetchone()["total"]
        rows = connection.execute("SELECT risk_score FROM logs").fetchall()

    risk_bands = {"Safe": 0, "Medium Risk": 0, "High Risk": 0}
    for row in rows:
        risk_score = row["risk_score"]
        if risk_score >= 70:
            risk_bands["High Risk"] += 1
        elif risk_score >= 35:
            risk_bands["Medium Risk"] += 1
        else:
            risk_bands["Safe"] += 1

    threat_rows = {"Blocked": blocked_prompts, "Review": review_prompts, "Allowed": safe_prompts}

    return {
        "total_prompts": total_prompts,
        "blocked_prompts": blocked_prompts,
        "review_prompts": review_prompts,
        "safe_prompts": safe_prompts,
        "risk_bands": risk_bands,
        "threat_rows": threat_rows,
    }
