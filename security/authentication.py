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
    return f"${salt.hex()}${digest.hex()}"


def verify_password(password, stored_hash):
    """Verify a password against the stored $salt_hex$digest_hex format."""
    if not isinstance(password, str) or not isinstance(stored_hash, str):
        return False

    try:
        parts = stored_hash.split("$")
        # The format begins with '$' and contains exactly salt and digest.
        if len(parts) != 3 or parts[0] != "":
            return False

        salt = bytes.fromhex(parts[1])
        expected = bytes.fromhex(parts[2])
        if len(salt) != 16 or len(expected) != hashlib.sha256().digest_size:
            return False

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
