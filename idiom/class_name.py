"""
class_name.py  ── 班級名稱統一成「X年YY班」（純函式，不碰資料庫）

  normalize_class_name("三年二班") -> "3年02班"
  normalize_class_name("國一甲")   -> "7年01班"
  normalize_class_name("abc")      -> None
"""

import re

_CN_DIGIT = {c: i for i, c in enumerate("一二三四五六七八九", start=1)}
_STEMS = {c: i for i, c in enumerate("甲乙丙丁戊己庚辛壬癸", start=1)}
_FULLWIDTH = str.maketrans("０１２３４５６７８９－", "0123456789-")

_G = "1-9一二三四五六七八九"
_RE = re.compile(
    r"^(?:"
    r"國中?(?P<jh>[1-3一二三])(?:年級|年)?"          # 國一、國中一年 → 7–9 年級
    rf"|(?P<g>[{_G}])(?P<mark>年級|年|-)?"            # 3、三年、3年級、3-
    r")(?P<cls>.+?)班?$"
)


def _digit(c: str) -> int:
    return int(c) if c.isdigit() else _CN_DIGIT[c]


def _cn_number(s: str):
    """一 到 九十九；不符合回傳 None。"""
    if len(s) == 1 and s in _CN_DIGIT:
        return _CN_DIGIT[s]
    m = re.fullmatch(r"([一二三四五六七八九])?十([一二三四五六七八九])?", s)
    if not m:
        return None
    tens, ones = m.groups()
    return (_CN_DIGIT[tens] if tens else 1) * 10 + (_CN_DIGIT[ones] if ones else 0)


def _class_no(s: str, marked: bool):
    if s in _STEMS:
        return _STEMS[s]
    if s.isascii() and s.isdigit():
        # 沒有「年」「-」分隔時只接受 302、512 這種三碼寫法，避免把 12 誤判成 1 年 2 班
        if not marked and len(s) != 2:
            return None
        return int(s) if len(s) <= 2 else None
    if marked:
        return _cn_number(s)
    return None


def normalize_class_name(raw) -> str | None:
    if raw is None:
        return None
    s = "".join(str(raw).split()).translate(_FULLWIDTH)
    m = _RE.match(s)
    if not m:
        return None
    if m["jh"]:
        grade, marked = 6 + _digit(m["jh"]), True
    else:
        grade, marked = _digit(m["g"]), bool(m["mark"])
    no = _class_no(m["cls"], marked)
    if not no or not (1 <= no <= 99):
        return None
    return f"{grade}年{no:02d}班"
