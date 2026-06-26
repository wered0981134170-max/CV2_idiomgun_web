"""
db.py  ── SQLite 資料層（排行榜 + 學生身分）
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
            CREATE TABLE IF NOT EXISTS scores (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                class_name TEXT,
                seat_no    INTEGER,
                name       TEXT    NOT NULL,
                score      INTEGER NOT NULL,
                total      INTEGER NOT NULL DEFAULT 100,
                duration   INTEGER NOT NULL DEFAULT 0,
                created_at DATETIME DEFAULT (datetime('now','localtime'))
            )
        """)
        c.execute("CREATE INDEX IF NOT EXISTS idx_scores_score ON scores (score DESC, created_at ASC)")

        # 舊資料表缺少欄位時自動補上
        for ddl in [
            "ALTER TABLE scores ADD COLUMN duration   INTEGER NOT NULL DEFAULT 0",
            "ALTER TABLE scores ADD COLUMN class_name TEXT",
            "ALTER TABLE scores ADD COLUMN seat_no    INTEGER",
        ]:
            try:
                c.execute(ddl)
            except Exception:
                pass
        c.commit()


# ── 排行榜 ────────────────────────────────────────────────────
def save_score(name: str, score: int, total: int = 100, duration: int = 0,
               class_name: str = None, seat_no: int = None) -> dict:
    name = name.strip()[:20] or "匿名"
    with _conn() as c:
        cur = c.execute(
            "INSERT INTO scores (class_name, seat_no, name, score, total, duration) VALUES (?, ?, ?, ?, ?, ?)",
            (class_name, seat_no, name, score, total, duration)
        )
        c.commit()
        return {"id": cur.lastrowid, "name": name, "score": score, "duration": duration}


def _fmt(sec: int) -> str:
    m, s = divmod(max(0, sec), 60)
    return f"{m:02d}:{s:02d}"


def get_top(limit: int = 10) -> list[dict]:
    with _conn() as c:
        rows = c.execute(
            """SELECT id, class_name, seat_no, name, score, total, duration, created_at
               FROM scores
               ORDER BY score DESC, created_at ASC
               LIMIT ?""",
            (limit,)
        ).fetchall()
    return [
        {
            "rank": i + 1, "id": r[0],
            "class_name": r[1], "seat_no": r[2], "name": r[3],
            "score": r[4], "total": r[5],
            "duration": r[6], "duration_fmt": _fmt(r[6]), "time": r[7],
        }
        for i, r in enumerate(rows)
    ]


def get_best_by_student(class_name: str, seat_no: int, name: str):
    with _conn() as c:
        row = c.execute(
            """SELECT score, total, duration, created_at FROM scores
               WHERE class_name = ? AND seat_no = ? AND name = ?
               ORDER BY score DESC, created_at ASC LIMIT 1""",
            (class_name, seat_no, name)
        ).fetchone()
    if row is None:
        return None
    return {
        "score": row[0], "total": row[1],
        "duration": row[2], "duration_fmt": _fmt(row[2]), "time": row[3],
    }


def reset_table():
    with _conn() as c:
        c.execute("DELETE FROM scores")
        c.execute("DELETE FROM sqlite_sequence WHERE name='scores'")
        c.commit()
