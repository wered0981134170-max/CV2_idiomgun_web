"""
階段 2a 測試：教師登入、權限、CSRF、失敗次數限制。
不連 Supabase：用記憶體假資料取代 idiom.db 的教師相關函式。
執行：python -m pytest tests -q
"""

import os
import re

import pytest

os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("SUPABASE_URL", "http://localhost:1")
os.environ.setdefault("SUPABASE_KEY", "test")
os.environ["SESSION_COOKIE_SECURE"] = "false"
os.environ["RENDER"] = "1"      # 測試不載入 .env，避免誤連真實資料庫

from idiom.app import app                         # noqa: E402
from idiom import db, teacher_auth                # noqa: E402
from idiom.extensions import bcrypt               # noqa: E402


@pytest.fixture
def fake_db(monkeypatch):
    state = {"attempts": [], "reset_called": 0}
    pw = bcrypt.generate_password_hash("correct-horse-1").decode()
    teachers = {
        1: dict(id=1, email="admin@x.tw", password_hash=pw, name="管理員", role="admin",
                school_id=None, is_active=True),
        2: dict(id=2, email="t@x.tw", password_hash=pw, name="王老師", role="teacher",
                school_id=10, is_active=True),
        3: dict(id=3, email="off@x.tw", password_hash=pw, name="停用", role="teacher",
                school_id=10, is_active=False),
    }
    by_email = {t["email"]: t for t in teachers.values()}
    monkeypatch.setattr(db, "get_teacher_by_email", lambda e: by_email.get(e))
    monkeypatch.setattr(db, "get_teacher_by_id", lambda i: teachers.get(i))
    state["scores"] = []
    monkeypatch.setattr(db, "get_all_scores", lambda: list(state["scores"]))
    monkeypatch.setattr(db, "record_login_attempt",
                        lambda e, ip, ok: state["attempts"].append((e, ip, ok)))
    monkeypatch.setattr(db, "purge_old_login_attempts", lambda before: None)

    def count(email, ip, since):
        fails = [a for a in state["attempts"] if not a[2]]
        return (sum(a[0] == email for a in fails), sum(a[1] == ip for a in fails))
    monkeypatch.setattr(db, "count_login_failures", count)
    monkeypatch.setattr("idiom.auth.get_best_by_student", lambda *a: None)
    monkeypatch.setattr("idiom.routes.reset_table",
                        lambda: state.__setitem__("reset_called", state["reset_called"] + 1))
    return state


@pytest.fixture
def client(fake_db):
    app.config["TESTING"] = True
    return app.test_client()


def _csrf(client, path="/teacher/login"):
    html = client.get(path).get_data(as_text=True)
    return re.search(r'name="csrf_token" value="([^"]+)"', html).group(1)


def _login(client, email, password="correct-horse-1"):
    return client.post("/teacher/login", data={
        "email": email, "password": password, "csrf_token": _csrf(client)})


def _api_headers(client):
    return {"X-CSRF-Token": _csrf(client, "/teacher/")}


# ── 未登入 ────────────────────────────────────────────────────
def test_dashboard_redirects_when_logged_out(client):
    r = client.get("/teacher/", headers={"Accept": "text/html"})
    assert r.status_code == 302 and "/teacher/login" in r.headers["Location"]


def test_api_returns_401_when_logged_out(client):
    assert client.post("/leaderboard/reset").status_code == 401


def test_student_session_is_not_a_teacher(client):
    client.post("/auth/login", json={"class_name": "501", "seat_no": 1, "name": "測試"})
    assert client.post("/leaderboard/reset").status_code == 401


# ── 登入 ──────────────────────────────────────────────────────
def test_login_success_and_dashboard(client):
    r = _login(client, "t@x.tw")
    assert r.status_code == 302
    html = client.get("/teacher/").get_data(as_text=True)
    assert "王老師" in html and "目前還沒有成績紀錄" in html


def test_login_wrong_password_and_unknown_email_look_the_same(client):
    a = _login(client, "t@x.tw", "wrong-password-1")
    b = _login(client, "nobody@x.tw", "whatever-1234")
    assert a.status_code == b.status_code == 401
    assert "帳號或密碼錯誤" in a.get_data(as_text=True)
    assert "帳號或密碼錯誤" in b.get_data(as_text=True)


def test_inactive_teacher_cannot_login(client):
    assert _login(client, "off@x.tw").status_code == 401


def test_login_requires_csrf(client):
    r = client.post("/teacher/login", data={"email": "t@x.tw", "password": "correct-horse-1"})
    assert r.status_code == 400


def test_overlong_password_rejected(client):
    assert _login(client, "t@x.tw", "a" * 100).status_code == 401


# ── 失敗次數限制 ──────────────────────────────────────────────
def test_lockout_after_repeated_failures_even_with_correct_password(client):
    for _ in range(teacher_auth.MAX_FAIL_PER_EMAIL):
        assert _login(client, "t@x.tw", "bad-password-1").status_code == 401
    assert _login(client, "t@x.tw", "correct-horse-1").status_code == 429


def test_lockout_is_per_email(client):
    for _ in range(teacher_auth.MAX_FAIL_PER_EMAIL):
        _login(client, "t@x.tw", "bad-password-1")
    assert _login(client, "admin@x.tw").status_code == 302


# ── 角色與 CSRF ───────────────────────────────────────────────
def test_teacher_cannot_reset_leaderboard(client, fake_db):
    _login(client, "t@x.tw")
    r = client.post("/leaderboard/reset", headers=_api_headers(client))
    assert r.status_code == 403 and fake_db["reset_called"] == 0


def test_admin_can_reset_with_csrf_only(client, fake_db):
    _login(client, "admin@x.tw")
    assert client.post("/leaderboard/reset").status_code == 403       # 沒帶 CSRF
    assert fake_db["reset_called"] == 0
    r = client.post("/leaderboard/reset", headers=_api_headers(client))
    assert r.status_code == 200 and fake_db["reset_called"] == 1


def test_logout_clears_teacher_but_keeps_student(client):
    client.post("/auth/login", json={"class_name": "501", "seat_no": 1, "name": "測試"})
    _login(client, "t@x.tw")
    r = client.post("/teacher/logout", data={"csrf_token": _csrf(client, "/teacher/")})
    assert r.status_code == 302
    assert client.post("/leaderboard/reset").status_code == 401
    assert client.get("/auth/me").get_json()["logged_in"] is True   # 學生身分不受影響


def test_session_expires(client, monkeypatch):
    _login(client, "t@x.tw")
    monkeypatch.setattr(teacher_auth, "SESSION_MAX_AGE", -1)
    assert client.post("/leaderboard/reset").status_code == 401


def test_teacher_pages_not_cached(client):
    assert client.get("/teacher/login").headers["Cache-Control"] == "no-store"


def test_session_cookie_flags():
    assert app.config["SESSION_COOKIE_SAMESITE"] == "Lax"
    assert app.config["SESSION_COOKIE_HTTPONLY"] is True


# ── 註冊已移除 ────────────────────────────────────────────────
def test_register_route_is_gone(client, monkeypatch):
    monkeypatch.setenv("REGISTER_ALLOWED_EMAILS", "me@x.tw")     # 舊環境變數殘留也不會打開註冊
    assert client.get("/teacher/register").status_code == 404
    assert client.post("/teacher/register", data={"email": "me@x.tw"}).status_code == 404
    assert "註冊" not in client.get("/teacher/login").get_data(as_text=True)


# ── 學生班級格式 ──────────────────────────────────────────────
def test_student_login_normalizes_class(client):
    r = client.post("/auth/login", json={"class_name": "三年二班", "seat_no": 5, "name": "小明"})
    assert r.status_code == 200 and r.get_json()["class_name"] == "3年02班"
    assert client.get("/auth/me").get_json()["class_name"] == "3年02班"


def test_student_login_rejects_unknown_class(client):
    r = client.post("/auth/login", json={"class_name": "abc", "seat_no": 5, "name": "小明"})
    assert r.status_code == 400
    assert r.get_json()["error"] == "班級格式無法辨識，請填寫如：三年二班、3甲"


def test_old_session_class_is_normalized_on_read(client, monkeypatch):
    saved = []
    monkeypatch.setattr("idiom.routes.save_score", lambda *a: saved.append(a) or {})
    for raw, expected in (("一甲", "1年01班"), ("火星班", "火星班")):
        with client.session_transaction() as sess:
            sess["student"] = {"class_name": raw, "seat_no": 3, "name": "小華"}
        assert client.get("/auth/me").get_json()["class_name"] == expected
        r = client.post("/leaderboard", json={"score": 8, "total": 15, "duration": 60})
        assert r.status_code == 200 and saved[-1][4] == expected


# ── 教師成績頁 ────────────────────────────────────────────────
def test_gradebook_requires_login(client, fake_db):
    fake_db["scores"] = [dict(id=1, class_name="一甲", seat_no=1, name="小明", score=9, total=15,
                              duration=30, grade="junior", created_at="2026-11-01T00:00:00+00:00")]
    r = client.get("/teacher/", headers={"Accept": "text/html"})
    assert r.status_code == 302 and "小明" not in r.get_data(as_text=True)


def test_gradebook_page_shows_history_and_escapes_input(client, fake_db):
    fake_db["scores"] = [
        dict(id=1, class_name="一甲", seat_no=3, name="<b>小明</b>", score=9, total=15, duration=75,
             grade="elementary_low", created_at="2026-11-01T02:05:00+00:00"),
        dict(id=2, class_name="1年甲班", seat_no=3, name="<b>小明</b>", score=12, total=15, duration=61,
             grade=None, created_at="2026-11-02T16:30:00Z"),
        dict(id=3, class_name="火星", seat_no=1, name="外星人", score=1, total=15, duration=5,
             grade="junior", created_at="2026-11-01T00:00:00+00:00"),
    ]
    _login(client, "admin@x.tw")
    html = client.get("/teacher/").get_data(as_text=True)
    assert "&lt;b&gt;小明&lt;/b&gt;" in html and "<b>小明</b>" not in html
    assert html.count("&lt;b&gt;小明&lt;/b&gt;") == 1                # 同一位學生只顯示一次姓名
    assert html.index("2026-11-01 10:05") < html.index("2026-11-03 00:30")   # UTC+8、由舊到新
    assert "9/15" in html and "01:15" in html and "國小低年級" in html and "—" in html
    assert html.index("1年01班") < html.index("未分類") < html.index("火星")


def test_gradebook_page_handles_db_error(client, monkeypatch):
    def boom():
        raise RuntimeError("down")
    monkeypatch.setattr(db, "get_all_scores", boom)
    _login(client, "admin@x.tw")
    r = client.get("/teacher/")
    assert r.status_code == 200 and "成績讀取失敗" in r.get_data(as_text=True)
