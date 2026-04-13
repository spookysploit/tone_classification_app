import hashlib
import secrets
from .database import get_connection


# ---------------------------------------------------------------------------
# Пароли
# ---------------------------------------------------------------------------

def hash_password(password: str) -> str:
    """SHA-256 хэш пароля."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    return hash_password(password) == hashed


# ---------------------------------------------------------------------------
# Пользователи
# ---------------------------------------------------------------------------

def create_user(username: str, password: str, role: str = "user") -> bool:
    """Создаёт пользователя. Возвращает False, если логин занят."""
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            (username, hash_password(password), role),
        )
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()


def get_user_by_username(username: str):
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_user_by_id(user_id: int):
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Сессии
# ---------------------------------------------------------------------------

def create_session(user_id: int) -> str:
    """Создаёт сессию и возвращает session_id."""
    session_id = secrets.token_hex(32)
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO sessions (session_id, user_id) VALUES (?, ?)",
            (session_id, user_id),
        )
        conn.commit()
        return session_id
    finally:
        conn.close()


def get_user_by_session(session_id: str):
    """Возвращает пользователя по session_id или None."""
    if not session_id:
        return None
    conn = get_connection()
    try:
        row = conn.execute(
            """SELECT u.* FROM users u
               JOIN sessions s ON s.user_id = u.id
               WHERE s.session_id = ?""",
            (session_id,),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def delete_session(session_id: str):
    conn = get_connection()
    try:
        conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Лог анализов
# ---------------------------------------------------------------------------

def log_analysis(user_id: int, message: str, tone: str, confidence: float, security_risk: str):
    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO analysis_log (user_id, message, tone, confidence, security_risk)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, message, tone, confidence, security_risk),
        )
        conn.commit()
    finally:
        conn.close()