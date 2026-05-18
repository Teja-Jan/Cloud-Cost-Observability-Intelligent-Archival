import sqlite3
import os
from datetime import datetime
from pathlib import Path

# Connect to ci_metadata.db instead of dq_metadata.db
DB_FILE = os.path.join(os.path.dirname(__file__), "ci_metadata.db")

def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS governance_requests (
            request_id       INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_name       TEXT    NOT NULL,
            platform         TEXT    NOT NULL,
            action_type      TEXT    NOT NULL DEFAULT 'ARCHIVE',
            projected_savings REAL,
            status           TEXT    NOT NULL DEFAULT 'PENDING',
            requested_at     TEXT    NOT NULL,
            updated_at       TEXT,
            notes            TEXT
        );
    """)
    conn.commit()
    conn.close()

def create_governance_request(asset_name: str, platform: str, action_type: str,
                              projected_savings: float, notes: str = None) -> int:
    conn = get_connection()
    now = datetime.now().isoformat()
    cursor = conn.execute(
        """INSERT INTO governance_requests 
           (asset_name, platform, action_type, projected_savings, status, requested_at, notes)
           VALUES (?, ?, ?, ?, 'PENDING', ?, ?)""",
        (asset_name, platform, action_type, projected_savings, now, notes)
    )
    req_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return req_id

def update_governance_request_status(request_id: int, status: str, notes: str = None):
    conn = get_connection()
    now = datetime.now().isoformat()
    if notes:
        conn.execute(
            "UPDATE governance_requests SET status=?, updated_at=?, notes=? WHERE request_id=?",
            (status, now, notes, request_id)
        )
    else:
        conn.execute(
            "UPDATE governance_requests SET status=?, updated_at=? WHERE request_id=?",
            (status, now, request_id)
        )
    conn.commit()
    conn.close()

def get_governance_requests(status: str = None) -> list:
    conn = get_connection()
    if status:
        rows = conn.execute("SELECT * FROM governance_requests WHERE status=? ORDER BY request_id DESC", (status,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM governance_requests ORDER BY request_id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

init_db()
