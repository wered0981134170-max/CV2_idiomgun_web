"""
teacher.py  ── 教師端 Blueprint（獨立頁面，前綴 /teacher）

  GET/POST /teacher/register 註冊（白名單：只有 REGISTER_ALLOWED_EMAILS 列出的 Email 能註冊）
  GET/POST /teacher/login   登入
  POST     /teacher/logout  登出
  GET      /teacher/        儀表板（之後各階段的功能入口）
"""

import os
import re
import time

from flask import Blueprint, abort, redirect, render_template, request, session, url_for
from flask_login import current_user, login_user, logout_user

from . import db
from . import teacher_auth as ta
from .extensions import bcrypt

teacher_bp = Blueprint("teacher", __name__, url_prefix="/teacher")


_EMAIL_RE = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")
MIN_PASSWORD = 10


def _allowed_emails() -> set:
    raw = os.environ.get("REGISTER_ALLOWED_EMAILS", "")
    return {e.strip().lower() for e in raw.split(",") if e.strip()}


@teacher_bp.context_processor
def _inject():
    return {"csrf_token": ta.csrf_token, "register_open": bool(_allowed_emails())}


@teacher_bp.after_request
def _no_store(resp):
    resp.headers["Cache-Control"] = "no-store"
    return resp


# ── 註冊（白名單）─────────────────────────────────────────────
def _register_page(error=None, status=200, email=""):
    return render_template("teacher/register.html", error=error, email=email), status


@teacher_bp.route("/register", methods=["GET", "POST"])
def register():
    if not _allowed_emails():
        abort(404)                      # 沒設白名單 = 註冊功能關閉
    if request.method == "GET":
        return _register_page()

    if not ta.check_csrf():
        return _register_page("頁面已逾時，請重新整理後再試", 400)

    email = (request.form.get("email") or "").strip().lower()[:200]
    name = (request.form.get("name") or "").strip()[:20]
    password = request.form.get("password") or ""
    ip = ta.client_ip()

    if ta.is_locked(email, ip):         # 與登入共用「依 Email / 依 IP」的失敗次數限制
        return _register_page("嘗試次數過多，請 15 分鐘後再試", 429, email)

    def fail(msg, status=400):
        ta.record_attempt(email, ip, False)
        return _register_page(msg, status, email)

    if email not in _allowed_emails():
        return fail("此 Email 不開放註冊", 403)
    if not _EMAIL_RE.fullmatch(email):
        return fail("Email 格式不正確")
    if not name:
        return fail("請填寫姓名")
    if len(password) < MIN_PASSWORD:
        return fail(f"密碼至少 {MIN_PASSWORD} 個字元")
    if len(password.encode("utf-8")) > ta.MAX_PASSWORD_BYTES:
        return fail("密碼太長")
    if password != (request.form.get("password2") or ""):
        return fail("兩次輸入的密碼不一致")
    if db.get_teacher_by_email(email):
        return fail("這個 Email 已經註冊過了，請直接登入", 409)

    db.create_teacher(email, bcrypt.generate_password_hash(password).decode(),
                      name, role="admin")
    ta.record_attempt(email, ip, True)
    return render_template("teacher/login.html", notice="註冊完成，請用剛才的密碼登入")


@teacher_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        if current_user.is_authenticated:
            return redirect(url_for("teacher.dashboard"))
        return render_template("teacher/login.html")

    if not ta.check_csrf():
        return render_template("teacher/login.html",
                               error="頁面已逾時，請重新整理後再試"), 400

    email = (request.form.get("email") or "").strip().lower()[:200]
    password = request.form.get("password") or ""
    ip = ta.client_ip()

    if ta.is_locked(email, ip):
        return render_template("teacher/login.html",
                               error="嘗試次數過多，請 15 分鐘後再試"), 429

    row = db.get_teacher_by_email(email)
    ok = ta.verify_password(row, password) and bool(row.get("is_active"))
    ta.record_attempt(email, ip, ok)
    if not ok:
        return render_template("teacher/login.html", error="帳號或密碼錯誤"), 401

    login_user(ta.Teacher(row), remember=False)
    session.permanent = False
    session[ta.LOGIN_TS_KEY] = int(time.time())
    session.pop("csrf", None)       # 登入後換新的 CSRF token
    return redirect(url_for("teacher.dashboard"))


@teacher_bp.route("/logout", methods=["POST"])
@ta.teacher_required
def logout():
    logout_user()
    session.pop(ta.LOGIN_TS_KEY, None)
    session.pop("csrf", None)
    return redirect(url_for("teacher.login"))


@teacher_bp.route("/")
@ta.teacher_required
def dashboard():
    school = db.get_school(current_user.school_id) if current_user.school_id else None
    return render_template("teacher/dashboard.html", school=school)
