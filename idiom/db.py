"""
db.py  ── Supabase 資料層（排行榜 + 學生身分）
"""

import os
from supabase import create_client, Client

_client: Client | None = None


def _sb() -> Client:
    global _client
    if _client is None:
        url = os.environ["SUPABASE_URL"]
        key = os.environ["SUPABASE_KEY"]
        _client = create_client(url, key)
    return _client


def init_db():
    pass  # 資料表由 Supabase 端管理，見下方 SQL 建立腳本


# ── 排行榜 ────────────────────────────────────────────────────
def save_score(name: str, score: int, total: int = 100, duration: int = 0,
               class_name: str = None, seat_no: int = None) -> dict:
    name = name.strip()[:20] or "匿名"
    res = _sb().table("scores").insert({
        "class_name": class_name,
        "seat_no":    seat_no,
        "name":       name,
        "score":      score,
        "total":      total,
        "duration":   duration,
    }).execute()
    row = res.data[0] if res.data else {}
    return {"id": row.get("id"), "name": name, "score": score, "duration": duration}


def _fmt(sec: int) -> str:
    m, s = divmod(max(0, sec), 60)
    return f"{m:02d}:{s:02d}"


def get_top(limit: int = 10) -> list[dict]:
    res = (
        _sb().table("scores")
        .select("id, class_name, seat_no, name, score, total, duration, created_at")
        .order("score", desc=True)
        .order("created_at", desc=False)
        .limit(limit)
        .execute()
    )
    return [
        {
            "rank": i + 1,
            "id":           r["id"],
            "class_name":   r["class_name"],
            "seat_no":      r["seat_no"],
            "name":         r["name"],
            "score":        r["score"],
            "total":        r["total"],
            "duration":     r["duration"],
            "duration_fmt": _fmt(r["duration"]),
            "time":         r["created_at"],
        }
        for i, r in enumerate(res.data or [])
    ]


def get_best_by_student(class_name: str, seat_no: int, name: str):
    res = (
        _sb().table("scores")
        .select("score, total, duration, created_at")
        .eq("class_name", class_name)
        .eq("seat_no",    seat_no)
        .eq("name",       name)
        .order("score", desc=True)
        .order("created_at", desc=False)
        .limit(1)
        .execute()
    )
    if not res.data:
        return None
    r = res.data[0]
    return {
        "score":        r["score"],
        "total":        r["total"],
        "duration":     r["duration"],
        "duration_fmt": _fmt(r["duration"]),
        "time":         r["created_at"],
    }


def reset_table():
    _sb().table("scores").delete().neq("id", 0).execute()
