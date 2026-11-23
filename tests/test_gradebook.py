"""教師成績頁的資料整理與分批讀取。不連 Supabase。執行：python -m pytest tests -q"""

import pytest

from idiom import db
from idiom.gradebook import build_gradebook, fmt_tw_time


def _row(id, class_name, seat_no, name, created_at, score=10, total=15, duration=90, grade="junior"):
    return dict(id=id, class_name=class_name, seat_no=seat_no, name=name, score=score, total=total,
                duration=duration, grade=grade, created_at=created_at)


def _layout(book):
    return [(c["title"], [(s["raw_class"], s["seat_no"], s["name"], [p["n"] for p in s["plays"]])
                          for s in c["students"]]) for c in book]


def test_same_student_different_class_spelling_is_merged_old_to_new():
    book = build_gradebook([
        _row(2, "1年甲班", 5, "小明", "2026-11-02T08:00:00+00:00", score=12),
        _row(1, "一甲",    5, "小明", "2026-11-01T08:00:00+00:00", score=7),
    ])
    assert len(book) == 1 and book[0]["title"] == "1年01班"
    (student,) = book[0]["students"]
    assert [p["score"] for p in student["plays"]] == ["7/15", "12/15"]        # 不只顯示最高分
    assert [p["n"] for p in student["plays"]] == [1, 2]
    assert [p["time"] for p in student["plays"]] == ["2026-11-01 16:00", "2026-11-02 16:00"]


def test_grouping_and_ordering():
    rows = [
        _row(1, "512",    2, "乙", "2026-11-01T00:00:00Z"),
        _row(2, "三年二班", 10, "丙", "2026-11-01T00:00:00Z"),
        _row(3, "3-2",    2, "丁", "2026-11-01T00:00:00Z"),
        _row(4, "5年1班",  1, "甲", "2026-11-01T00:00:00Z"),
        _row(5, "一甲",    1, "戊", "2026-11-01T00:00:00Z"),
        _row(6, "3年02班", 2, "丁", "2026-10-01T00:00:00Z"),
        _row(7, "302",    2, "己", "2026-11-01T00:00:00Z"),       # 同座號不同姓名 → 不同學生
        _row(8, "國一甲",  1, "庚", "2026-11-01T00:00:00Z"),
    ]
    assert _layout(build_gradebook(rows)) == [
        ("1年01班", [(None, 1, "戊", [1])]),
        ("3年02班", [(None, 2, "丁", [1, 2]), (None, 2, "己", [1]), (None, 10, "丙", [1])]),
        ("5年01班", [(None, 1, "甲", [1])]),
        ("5年12班", [(None, 2, "乙", [1])]),
        ("7年01班", [(None, 1, "庚", [1])]),
    ]


def test_unclassified_kept_at_bottom_with_raw_text():
    rows = [
        _row(1, None,   None, "匿名", "2026-11-01T00:00:00Z"),
        _row(2, "火星班", 3,    "小明", "2026-11-01T00:00:00Z"),
        _row(3, "",     None, "路人", "2026-11-01T00:00:00Z"),
        _row(4, "一甲",  1,    "小華", "2026-11-01T00:00:00Z"),
        _row(5, "火星班", 3,    "小明", "2026-11-02T00:00:00Z"),
        _row(6, "abc",  3,    "小明", "2026-11-01T00:00:00Z"),   # 原始文字不同 → 分開列
    ]
    book = build_gradebook(rows)
    assert [c["title"] for c in book] == ["1年01班", "未分類"]
    assert book[-1]["unclassified"] is True
    assert _layout(book)[-1][1] == [
        ("", None, "匿名", [1]), ("", None, "路人", [1]),
        ("abc", 3, "小明", [1]), ("火星班", 3, "小明", [1, 2]),
    ]
    assert sum(len(s["plays"]) for c in book for s in c["students"]) == len(rows)   # 一筆都沒丟


def test_display_fields():
    (cls,) = build_gradebook([
        _row(1, "一甲", 1, "a", "2026-11-01T15:59:00+00:00", score=8, total=15, duration=125,
             grade="elementary_high"),
        _row(2, "一甲", 1, "a", "2026-11-01T16:00:00.123456+00:00", grade=None),
        _row(3, "一甲", 1, "a", "2026-11-01T17:00:00+00:00", grade="elementary_low"),
    ])
    plays = cls["students"][0]["plays"]
    assert [p["time"] for p in plays] == ["2026-11-01 23:59", "2026-11-02 00:00", "2026-11-02 01:00"]
    assert plays[0]["score"] == "8/15" and plays[0]["duration"] == "02:05"
    assert [p["grade"] for p in plays] == ["國小高年級", "—", "國小低年級"]


def test_fmt_tw_time_bad_values():
    assert fmt_tw_time(None) == "—"
    assert fmt_tw_time("not-a-date") == "not-a-date"
    assert fmt_tw_time("2026-01-01T00:00:00") == "2026-01-01 08:00"      # 沒時區當作 UTC


def test_empty():
    assert build_gradebook([]) == []


# ── 分批讀取 ──────────────────────────────────────────────────
class _FakeQuery:
    """模擬 supabase 查詢鏈；每次最多回傳 server_cap 筆，跟 Supabase 的 max-rows 一樣。"""

    def __init__(self, rows, server_cap, calls):
        self.rows, self.cap, self.calls, self.lo, self.hi = rows, server_cap, calls, 0, None

    def table(self, name):
        assert name == "scores"
        return self

    def select(self, *a, **k):
        return self

    def order(self, col, desc=False):
        self.rows = sorted(self.rows, key=lambda r: r[col], reverse=desc)
        return self

    def range(self, lo, hi):
        self.lo, self.hi = lo, hi
        return self

    def execute(self):
        self.calls.append((self.lo, self.hi))
        data = self.rows[self.lo:self.hi + 1][:self.cap]
        return type("Res", (), {"data": data})()


@pytest.mark.parametrize("n, server_cap", [(2500, 1000), (1000, 1000), (1234, 500), (3, 1000)])
def test_get_all_scores_reads_every_page(monkeypatch, n, server_cap):
    rows = [_row(i, "一甲", 1, "a", "2026-11-01T00:00:00Z") for i in range(1, n + 1)]
    calls = []
    monkeypatch.setattr(db, "_sb", lambda: _FakeQuery(rows, server_cap, calls))
    got = db.get_all_scores()
    assert len(got) == n and [r["id"] for r in got] == list(range(1, n + 1))
    assert len(calls) > 1 or n == 0                       # 最後一次查詢回傳空，確認讀完
    assert all(hi - lo + 1 <= db.SCORES_PAGE_SIZE for lo, hi in calls)


def test_over_1000_rows_end_to_end(monkeypatch):
    rows = [_row(i, "一甲" if i % 2 else "1年甲班", 1, "小明", f"2026-11-01T00:{i // 60 % 60:02d}:{i % 60:02d}Z")
            for i in range(1, 1501)]
    monkeypatch.setattr(db, "_sb", lambda: _FakeQuery(rows, 1000, []))
    book = build_gradebook(db.get_all_scores())
    assert len(book) == 1 and len(book[0]["students"]) == 1
    assert len(book[0]["students"][0]["plays"]) == 1500
