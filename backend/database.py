import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "app.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Таблица пользователей
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT    NOT NULL UNIQUE,
            password    TEXT    NOT NULL,
            role        TEXT    NOT NULL DEFAULT 'user',
            created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
        )
    """)

    # Таблица сессий
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id  TEXT    PRIMARY KEY,
            user_id     INTEGER NOT NULL,
            created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Таблица истории анализов (расширенная)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analysis_log (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id       INTEGER NOT NULL,
            username      TEXT    NOT NULL DEFAULT '',
            message       TEXT    NOT NULL,
            tone          TEXT,
            confidence    REAL,
            security_risk TEXT,
            analyzed_at   TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Добавляем колонку username если её нет (миграция для существующих БД)
    try:
        cursor.execute("ALTER TABLE analysis_log ADD COLUMN username TEXT NOT NULL DEFAULT ''")
    except Exception:
        pass  # Колонка уже существует

    conn.commit()
    conn.close()


def get_user_history(user_id: int, limit: int = 50) -> list:
    """Возвращает историю анализов пользователя, отсортированную по убыванию времени."""
    conn = get_connection()
    try:
        rows = conn.execute(
            """SELECT id, username, message, tone, confidence, security_risk, analyzed_at
               FROM analysis_log
               WHERE user_id = ?
               ORDER BY analyzed_at DESC
               LIMIT ?""",
            (user_id, limit),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_all_history(limit: int = 200) -> list:
    """Возвращает всю историю анализов (для администратора)."""
    conn = get_connection()
    try:
        rows = conn.execute(
            """SELECT al.id, u.username, al.message, al.tone,
                      al.confidence, al.security_risk, al.analyzed_at
               FROM analysis_log al
               JOIN users u ON u.id = al.user_id
               ORDER BY al.analyzed_at DESC
               LIMIT ?""",
            (limit,),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()