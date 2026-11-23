"""教師成語頁：資料整理與頁面。不連 Supabase。執行：python -m pytest tests -q"""

import json
import re

from idiom import question_type
from idiom.idiom_bank import build_idiom_bank
from test_teacher_auth import _login, client, fake_db      # noqa: F401（共用 fixture）


def _q(kind):
    return {"question": f"{kind}題", "answer": "甲", "options": ["乙", "丙"]}


def _row(idiom, meaning="", teaching=None, kinds=("typo", "compose", "application")):
    qs = {k: _q(k) for k in kinds}
    if teaching:
        qs["teaching"] = teaching
    return {"idiom": idiom, "meaning": meaning, "questions": qs}


def test_columns_keep_duplicates_in_order():
    bank = build_idiom_bank({
        "elementary_low":  [_row("甲乙丙丁"), _row("惱羞成怒")],
        "elementary_high": [_row("惱羞成怒"), _row("雪上加霜 ")],
    })
    assert [(c["label"], c["idioms"]) for c in bank["columns"]] == [
        ("簡單", ["甲乙丙丁", "惱羞成怒"]),
        ("中等", ["惱羞成怒", "雪上加霜"]),         # 重複的照樣列出，前後空白去掉
        ("困難", []),
    ]


def test_learning_is_one_copy_per_idiom_questions_are_per_grade():
    teaching = {"example": "例句", "breakdown": [{"char": "惱", "meaning": "生氣"}]}
    bank = build_idiom_bank({
        "elementary_low":  [_row("惱羞成怒", meaning="", teaching=teaching)],
        "elementary_high": [_row("惱羞成怒", meaning="因羞愧而發怒", kinds=("typo",))],
    })
    assert bank["learning"] == {"惱羞成怒": {
        "meaning": "因羞愧而發怒", "example": "例句",
        "breakdown": [{"char": "惱", "meaning": "生氣"}]}}
    assert set(bank["questions"]["elementary_low"]["惱羞成怒"]) == {"typo", "compose", "application"}
    assert set(bank["questions"]["elementary_high"]["惱羞成怒"]) == {"typo"}


def test_meaning_falls_back_to_teaching_plain():
    bank = build_idiom_bank({"junior": [_row("前倨後恭", teaching={"plain": "白話"})]})
    assert bank["learning"]["前倨後恭"]["meaning"] == "白話"


def test_real_json_data_builds():
    bank = build_idiom_bank(question_type.questions_data)
    assert all(c["idioms"] for c in bank["columns"])
    assert bank["learning"]["兩敗俱傷"]["example"]


# ── 頁面 ──────────────────────────────────────────────────────
def test_idioms_page_requires_login(client):
    r = client.get("/teacher/idioms", headers={"Accept": "text/html"})
    assert r.status_code == 302 and "/teacher/login" in r.headers["Location"]


def test_idioms_page_lists_columns_and_embeds_safe_json(client, monkeypatch):
    data = {"elementary_low": [_row("惱羞成怒", meaning="</script><b>x</b>")],
            "elementary_high": [_row("惱羞成怒")], "junior": []}
    monkeypatch.setattr(question_type, "get_idioms", lambda g: data[g])
    _login(client, "admin@x.tw")
    html = client.get("/teacher/idioms").get_data(as_text=True)
    assert html.count('class="idiom-item"') == 2                      # 簡單、中等各一個
    assert "</script><b>x</b>" not in html                             # tojson 會跳脫
    raw = re.search(r'<script id="idiom-data" type="application/json">(.*?)</script>', html, re.S).group(1)
    assert json.loads(raw)["learning"]["惱羞成怒"]["meaning"] == "</script><b>x</b>"
    assert 'class="active" aria-current="page">新增成語' in html


def test_nav_marks_scores_page_active(client):
    _login(client, "admin@x.tw")
    html = client.get("/teacher/").get_data(as_text=True)
    assert 'class="active" aria-current="page">學生成績' in html
    assert 'href="/teacher/idioms"' in html
