"""
db.py  ── Supabase 資料層（排行榜 + 學生身分）
"""

import os
from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions

_client: Client | None = None


def _sb() -> Client:
    global _client
    if _client is None:
        url = os.environ["SUPABASE_URL"].strip() 
        key = os.environ["SUPABASE_KEY"].strip()  
        # 逾時設短一點：Supabase 連不上時，遊戲才能快速退回讀 JSON
        _client = create_client(url, key, options=ClientOptions(postgrest_client_timeout=8))
    return _client


def init_db():
    pass  # 資料表由 Supabase 端管理，見下方 SQL 建立腳本


# ── 排行榜 ────────────────────────────────────────────────────
def save_score(name: str, score: int, total: int = 100, duration: int = 0,
               class_name: str = None, seat_no: int = None,
               grade: str = None) -> dict:
    name = name.strip()[:20] or "匿名"
    res = _sb().table("scores").insert({
        "class_name": class_name,
        "seat_no":    seat_no,
        "name":       name,
        "score":      score,
        "total":      total,
        "duration":   duration,
        "grade":      grade,
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


# ── 成語題庫 ──────────────────────────────────────────────────
def get_published_idioms(grade: str) -> list[dict]:
    """取得某年級已發布的成語，格式與 data/*.json 的單筆成語相同。
    資料表不存在或連線失敗時會丟出例外，由呼叫端決定如何退回。"""
    res = (
        _sb().table("idioms")
        .select("id, grade, idiom, meaning, explanation, questions")
        .eq("grade", grade)
        .eq("status", "published")
        .is_("school_id", "null")     # 目前只出共用題庫；校內成語在階段 2c 加入
        .order("id")
        .execute()
    )
    return res.data or []


# ── 教師帳號 ──────────────────────────────────────────────────
_TEACHER_COLS = "id, email, password_hash, name, role, school_id, is_active"


def get_teacher_by_email(email: str):
    res = (_sb().table("teachers").select(_TEACHER_COLS)
           .eq("email", (email or "").strip().lower()).limit(1).execute())
    return res.data[0] if res.data else None


def get_teacher_by_id(teacher_id: int):
    res = (_sb().table("teachers").select(_TEACHER_COLS)
           .eq("id", teacher_id).limit(1).execute())
    return res.data[0] if res.data else None


def get_school(school_id: int):
    res = (_sb().table("schools").select("id, name")
           .eq("id", school_id).limit(1).execute())
    return res.data[0] if res.data else None


def count_admins() -> int:
    res = (_sb().table("teachers").select("id", count="exact")
           .eq("role", "admin").limit(1).execute())
    return res.count or 0


def create_teacher(email: str, password_hash: str, name: str,
                   role: str = "teacher", school_id: int = None) -> dict:
    res = _sb().table("teachers").insert({
        "email": email.strip().lower(), "password_hash": password_hash,
        "name": name.strip(), "role": role, "school_id": school_id,
    }).execute()
    return res.data[0]


# ── 登入失敗限制 ──────────────────────────────────────────────
def count_login_failures(email: str, ip: str, since_iso: str) -> tuple[int, int]:
    """回傳 (此 email 的失敗次數, 此 IP 的失敗次數)；只算 since_iso 之後。"""
    t = _sb().table("login_attempts")
    by_email = (t.select("id", count="exact").eq("email", email).eq("success", False)
                .gte("created_at", since_iso).limit(1).execute()).count or 0
    by_ip = (_sb().table("login_attempts").select("id", count="exact").eq("ip", ip)
             .eq("success", False).gte("created_at", since_iso).limit(1).execute()).count or 0
    return by_email, by_ip


def record_login_attempt(email: str, ip: str, success: bool) -> None:
    _sb().table("login_attempts").insert(
        {"email": email, "ip": ip, "success": success}).execute()


def purge_old_login_attempts(before_iso: str) -> None:
    _sb().table("login_attempts").delete().lt("created_at", before_iso).execute()


def reset_table():
    _sb().table("scores").delete().neq("id", 0).execute()
