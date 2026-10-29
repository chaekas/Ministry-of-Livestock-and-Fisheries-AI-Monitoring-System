"""Basic authentication helpers for the local Phase 1 prototype."""
import hashlib
import hmac
import secrets

from database.db import get_connection

ROLES = ("admin", "officer", "supervisor")
PBKDF2_ITERATIONS = 600_000


def hash_password(password):
    if not isinstance(password, str) or len(password) < 12:
        raise ValueError("Password must contain at least 12 characters.")
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS
    )
    return f"\u0024{salt.hex()}\u0024{digest.hex()}"


def verify_password(password, stored_hash):
    try:
        salt_hex, digest_hex = stored_hash.split("$", 1)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(digest_hex)
        actual = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS
        )
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError, AttributeError):
        return False


def create_user(username, password, role):
    username = (username or "").strip()
    if not username:
        raise ValueError("Username is required.")
    if len(username) > 80:
        raise ValueError("Username must be 80 characters or fewer.")
    if role not in ROLES:
        raise ValueError("Invalid user role.")
    password_hash = hash_password(password)
    with get_connection() as connection:
        connection.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
            (username, password_hash, role),
        )


def authenticate_user(username, password):
    if not isinstance(username, str) or not isinstance(password, str):
        return None
    with get_connection() as connection:
        user = connection.execute(
            "SELECT id, username, password_hash, role FROM users "
            "WHERE username = ? AND active = 1",
            (username.strip(),),
        ).fetchone()
    if user is None or not verify_password(password, user["password_hash"]):
        return None
    return {"id": user["id"], "username": user["username"], "role": user["role"]}


def list_users():
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT id, username, role, active, created_at FROM users ORDER BY username"
        ).fetchall()
        return [dict(row) for row in rows]
