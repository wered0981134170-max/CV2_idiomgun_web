"""
db.py  ── SQLite 資料層（排行榜 + 使用者帳號）
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "leaderboard.db")


def _conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


# ── 初始化資料表 ──────────────────────────────────────────────
def init_db():
    with _conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                username      TEXT    NOT NULL UNIQUE,
                password_hash TEXT    NOT NULL,
                created_at    DATETIME DEFAULT (datetime('now','localtime'))
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS scores (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id   INTEGER REFERENCES users(id),
                name      TEXT    NOT NULL,
                score     INTEGER NOT NULL,
                total     INTEGER NOT NULL DEFAULT 100,
                duration  INTEGER NOT NULL DEFAULT 0,
                created_at DATETIME DEFAULT (datetime('now','localtime'))
            )
        """)
        c.execute("CREATE INDEX IF NOT EXISTS idx_scores_score ON scores (score DESC, created_at ASC)")

        # 舊資料表缺少欄位時自動補上
        for col, ddl in [
            ("duration", "ALTER TABLE scores ADD COLUMN duration INTEGER NOT NULL DEFAULT 0"),
            ("user_id",  "ALTER TABLE scores ADD COLUMN user_id  INTEGER REFERENCES users(id)"),
        ]:
            try:
                c.execute(ddl)
            except Exception:
                pass
        c.commit()


# ── 使用者 CRUD ───────────────────────────────────────────────
def create_user(username: str, password_hash: str) -> dict:
    with _conn() as c:
        try:
            cur = c.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, password_hash)
            )
            c.commit()
            return {"id": cur.lastrowid, "username": username}
        except sqlite3.IntegrityError:
            raise ValueError("帳號已存在")


def get_user_by_username(username: str):
    with _conn() as c:
        row = c.execute(
            "SELECT id, username, password_hash FROM users WHERE username = ?",
            (username,)
        ).fetchone()
    if row is None:
        return None
    return {"id": row[0], "username": row[1], "password_hash": row[2]}


def get_user_by_id(user_id: int):
    with _conn() as c:
        row = c.execute(
            "SELECT id, username FROM users WHERE id = ?", (user_id,)
        ).fetchone()
    if row is None:
        return None
    return {"id": row[0], "username": row[1]}


def get_user_best(user_id: int):
    with _conn() as c:
        row = c.execute(
            """SELECT score, total, duration, created_at
               FROM scores WHERE user_id = ?
               ORDER BY score DESC, created_at ASC LIMIT 1""",
            (user_id,)
        ).fetchone()
    if row is None:
        return None
    m, s = divmod(max(0, row[2]), 60)
    return {
        "score": row[0], "total": row[1],
        "duration": row[2], "duration_fmt": f"{m:02d}:{s:02d}",
        "time": row[3],
    }


# ── 排行榜 ────────────────────────────────────────────────────
def save_score(name: str, score: int, total: int = 100,
               duration: int = 0, user_id: int = None) -> dict:
    name = name.strip()[:20] or "匿名"
    with _conn() as c:
        cur = c.execute(
            "INSERT INTO scores (user_id, name, score, total, duration) VALUES (?, ?, ?, ?, ?)",
            (user_id, name, score, total, duration)
        )
        c.commit()
        return {"id": cur.lastrowid, "name": name, "score": score, "duration": duration}


def _fmt(sec: int) -> str:
    m, s = divmod(max(0, sec), 60)
    return f"{m:02d}:{s:02d}"


def get_top(limit: int = 10) -> list[dict]:
    with _conn() as c:
        rows = c.execute(
            """SELECT id, name, score, total, duration, created_at
               FROM scores
               ORDER BY score DESC, created_at ASC
               LIMIT ?""",
            (limit,)
        ).fetchall()
    return [
        {"rank": i + 1, "id": r[0], "name": r[1], "score": r[2],
         "total": r[3], "duration": r[4], "duration_fmt": _fmt(r[4]), "time": r[5]}
        for i, r in enumerate(rows)
    ]


def reset_table():
    with _conn() as c:
        c.execute("DELETE FROM scores")
        c.execute("DELETE FROM sqlite_sequence WHERE name='scores'")
        c.commit()
