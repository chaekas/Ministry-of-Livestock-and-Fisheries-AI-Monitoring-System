"""SQLite persistence for users, inspections, and audit events."""
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

DATABASE_PATH = Path(os.getenv("DATABASE_PATH", "data/ministry.db"))


@contextmanager
def get_connection():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(DATABASE_PATH), timeout=30)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize_database():
    """Create required tables if they do not exist."""
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK (
                    role IN ('admin', 'officer', 'supervisor')
                ),
                active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1)),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        connection.execute("""
            CREATE TABLE IF NOT EXISTS inspections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                module TEXT NOT NULL,
                location TEXT NOT NULL,
                subject_type TEXT,
                result_summary TEXT NOT NULL,
                officer_username TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        connection.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                action TEXT NOT NULL,
                details TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)


def count_users():
    with get_connection() as connection:
        return connection.execute(
            "SELECT COUNT(*) AS total FROM users"
        ).fetchone()["total"]


def record_audit(username, action, details=""):
    with get_connection() as connection:
        connection.execute(
            "INSERT INTO audit_logs (username, action, details) VALUES (?, ?, ?)",
            (username, action, details),
        )


def create_inspection(module, location, subject_type, result_summary, officer_username):
    with get_connection() as connection:
        cursor = connection.execute("""
            INSERT INTO inspections
                (module, location, subject_type, result_summary, officer_username)
            VALUES (?, ?, ?, ?, ?)
        """, (module, location, subject_type, result_summary, officer_username))
        return cursor.lastrowid


def get_dashboard_summary():
    with get_connection() as connection:
        inspection_count = connection.execute(
            "SELECT COUNT(*) AS total FROM inspections"
        ).fetchone()["total"]
        active_users = connection.execute(
            "SELECT COUNT(*) AS total FROM users WHERE active = 1"
        ).fetchone()["total"]
        module_counts = connection.execute("""
            SELECT module, COUNT(*) AS total
            FROM inspections
            GROUP BY module
            ORDER BY total DESC, module ASC
        """).fetchall()
        return {
            "inspections": inspection_count,
            "active_users": active_users,
            "module_counts": [dict(row) for row in module_counts],
        }


def list_inspections(limit=500):
    safe_limit = max(1, min(int(limit), 5000))
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT id, module, location, subject_type, result_summary, "
            "officer_username, created_at FROM inspections "
            "ORDER BY id DESC LIMIT ?",
            (safe_limit,),
        ).fetchall()
        return [dict(row) for row in rows]
