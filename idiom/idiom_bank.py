"""
idiom_bank.py  ── 教師成語頁的資料整理（純函式，不碰資料庫）

build_idiom_bank({grade: [成語列]}) 回傳：
  columns    [{"grade", "label", "idioms": [成語, ...]}]       ← 簡單 / 中等 / 困難三欄，重複的成語各欄都列
  learning   {成語: {"meaning", "breakdown", "example"}}       ← 學習內容：綁定成語本身，同一個成語只有一份
  questions  {grade: {成語: {"typo", "compose", "application"}}} ← 遊戲題目：綁定成語＋難度
"""

GRADES = [
    ("elementary_low",  "簡單"),
    ("elementary_high", "中等"),
    ("junior",          "困難"),
]
QUESTION_TYPES = ("typo", "compose", "application")


def _learning(row: dict) -> dict:
    teaching = (row.get("questions") or {}).get("teaching") or {}
    return {
        "meaning":   row.get("meaning") or teaching.get("plain") or "",
        "breakdown": [{"char": b.get("char", ""), "meaning": b.get("meaning", "")}
                      for b in teaching.get("breakdown") or [] if isinstance(b, dict)],
        "example":   teaching.get("example") or "",
    }


def build_idiom_bank(by_grade: dict) -> dict:
    columns, learning, questions = [], {}, {}
    for grade, label in GRADES:
        names = []
        questions[grade] = {}
        for row in by_grade.get(grade) or []:
            name = (row.get("idiom") or "").strip()
            if not name:
                continue
            names.append(name)
            qs = row.get("questions") or {}
            questions[grade][name] = {t: qs[t] for t in QUESTION_TYPES if qs.get(t)}
            # 目前資料是每個難度各存一份；合併時每個欄位取第一個有內容的（簡單 → 中等 → 困難）
            merged = learning.setdefault(name, {"meaning": "", "breakdown": [], "example": ""})
            for key, value in _learning(row).items():
                if not merged[key] and value:
                    merged[key] = value
        columns.append({"grade": grade, "label": label, "idioms": names})
    return {"columns": columns, "learning": learning, "questions": questions}
