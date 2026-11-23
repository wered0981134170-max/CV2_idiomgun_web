"""
teacher.py  ── 教師端 Blueprint（獨立頁面，前綴 /teacher）

  GET/POST /teacher/login   登入
  POST     /teacher/logout  登出
  GET      /teacher/        成績頁（各班學生的歷次成績）
  GET      /teacher/idioms  成語頁（依難度列出所有成語，右側抽屜看內容與題目）

不開放註冊：教師帳號只用 `python -m scripts.create_admin` 建立，teachers 表就是白名單。
"""

import time

from flask import Blueprint, redirect, render_template, request, session, url_for
from flask_login import current_user, login_user, logout_user

from . import db
from . import question_type
from . import teacher_auth as ta
from .gradebook import build_gradebook
from .idiom_bank import GRADES, build_idiom_bank

teacher_bp = Blueprint("teacher", __name__, url_prefix="/teacher")


@teacher_bp.context_processor
def _inject():
    return {"csrf_token": ta.csrf_token}


@teacher_bp.after_request
def _no_store(resp):
    resp.headers["Cache-Control"] = "no-store"
    return resp


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
    try:
        classes, error = build_gradebook(db.get_all_scores()), None
    except Exception:
        classes, error = [], "成績讀取失敗，請稍後重新整理"
    return render_template("teacher/dashboard.html", classes=classes, error=error)


@teacher_bp.route("/idioms")
@ta.teacher_required
def idioms():
    by_grade = {grade: question_type.get_idioms(grade) for grade, _ in GRADES}
    return render_template("teacher/idioms.html", bank=build_idiom_bank(by_grade))
