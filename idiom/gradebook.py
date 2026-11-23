"""
gradebook.py  ── 教師成績頁的資料整理（純函式，不碰資料庫）

build_gradebook(rows) 把 scores 的原始紀錄整理成：
  [ {"title": "1年01班", "unclassified": False,
     "students": [ {"seat_no", "name", "raw_class",
                    "plays": [ {"n", "time", "score", "grade", "duration"} ... ]} ... ]}
    ...,
    {"title": "未分類", "unclassified": True, ...} ]   ← 班級空白或無法辨識，放最後
"""

from datetime import datetime, timedelta, timezone

from .class_name import normalize_class_name
from .db import _fmt

TW = timezone(timedelta(hours=8))       # 固定 UTC+8，不依賴系統時區資料
UNCLASSIFIED = "未分類"
GRADE_LABELS = {
    "elementary_low":  "國小低年級",
    "elementary_high": "國小高年級",
    "junior":          "國中",
}


def _parse_time(value):
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def fmt_tw_time(value) -> str:
    dt = _parse_time(value)
    return dt.astimezone(TW).strftime("%Y-%m-%d %H:%M") if dt else (value or "—")


def _class_order(title: str):
    grade, rest = title.split("年")
    return int(grade), int(rest.rstrip("班"))


def _play_order(r):
    dt = _parse_time(r.get("created_at"))
    return (dt is None, dt or datetime.min.replace(tzinfo=timezone.utc), r.get("id") or 0)


def _student_order(key):
    raw_class, seat_no, name = key
    return (raw_class or "", seat_no is None, seat_no or 0, name or "")


def build_gradebook(rows) -> list[dict]:
    groups: dict = {}       # 班級標題（或 None = 未分類）→ {學生 key → [紀錄]}
    for r in rows:
        title = normalize_class_name(r.get("class_name"))
        # 未分類的紀錄連原始班級文字一起當作學生識別，避免不同班的同名學生被混在一起
        raw = None if title else (r.get("class_name") or "").strip()
        key = (raw, r.get("seat_no"), r.get("name") or "")
        groups.setdefault(title, {}).setdefault(key, []).append(r)

    titles = sorted((t for t in groups if t), key=_class_order)
    if None in groups:
        titles.append(None)

    result = []
    for title in titles:
        students = []
        for key in sorted(groups[title], key=_student_order):
            raw_class, seat_no, name = key
            plays = sorted(groups[title][key], key=_play_order)
            students.append({
                "seat_no":   seat_no,
                "name":      name,
                "raw_class": raw_class,
                "plays": [
                    {
                        "n":        i,
                        "time":     fmt_tw_time(p.get("created_at")),
                        "score":    f"{p.get('score', 0)}/{p.get('total', 0)}",
                        "grade":    GRADE_LABELS.get(p.get("grade"), p.get("grade") or "—"),
                        "duration": _fmt(p.get("duration") or 0),
                    }
                    for i, p in enumerate(plays, start=1)
                ],
            })
        result.append({
            "title":        title or UNCLASSIFIED,
            "unclassified": title is None,
            "students":     students,
        })
    return result
