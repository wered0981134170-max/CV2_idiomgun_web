"""
db.py  ── SQLite 排行榜資料層
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "leaderboard.db")


def _conn():
    return sqlite3.connect(DB_PATH)

#建立資料表
def init_db():
    with _conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS scores (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                name      TEXT    NOT NULL,
                score     INTEGER NOT NULL,
                total     INTEGER NOT NULL DEFAULT 100,
                duration  INTEGER NOT NULL DEFAULT 0,
                created_at DATETIME DEFAULT (datetime('now','localtime'))
            )
        """)
        # 舊資料表若缺少 duration 欄位，自動補上
        try:
            c.execute("ALTER TABLE scores ADD COLUMN duration INTEGER NOT NULL DEFAULT 0")
        except Exception:
            pass
        c.commit()

#儲存一筆分數，回傳插入的資料
def save_score(name: str, score: int, total: int = 100, duration: int = 0) -> dict:
    name = name.strip()[:20] or "匿名"
    with _conn() as c:
        cur = c.execute(
            "INSERT INTO scores (name, score, total, duration) VALUES (?, ?, ?, ?)",
            (name, score, total, duration)
        )
        c.commit()
        return {"id": cur.lastrowid, "name": name, "score": score, "duration": duration}

#秒數轉 mm:ss 字串
def _fmt(sec: int) -> str:
    m, s = divmod(max(0, sec), 60)
    return f"{m:02d}:{s:02d}"

#取得前 N 名（分數高→低，同分依時間早→晚)
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

# # 重置排行榜
# def reset_table():
#     with _conn() as c:
#         c.execute("DELETE FROM scores")

#         # 重置 AUTOINCREMENT 計數器
#         c.execute(
#             "DELETE FROM sqlite_sequence WHERE name='scores'"
#         )

#         c.commit()


# # 測試
# if __name__ == "__main__":
#     init_db()

#     print("重置前：")
#     print(get_top())

#     reset_table()

#     print("重置後：")
#     print(get_top())