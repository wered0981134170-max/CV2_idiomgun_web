"""
teacher_auth.py  ── 教師登入：使用者物件、裝飾器、CSRF、登入失敗限制

教師身分走 flask_login（session 的 _user_id），學生身分仍是 session["student"]，
兩者互不影響。所有教師路由都要掛 @teacher_required（或 @admin_required）。
"""

import hmac
import logging
import random
import secrets
import time
from datetime import datetime, timedelta, timezone
from functools import wraps

from flask import jsonify, redirect, request, session, url_for
from flask_login import UserMixin, current_user

from . import db
from .extensions import bcrypt, login_manager

log = logging.getLogger(__name__)

LOGIN_TS_KEY       = "teacher_login_at"
SESSION_MAX_AGE    = 8 * 3600        # 教師登入最長 8 小時，到期需重新登入
MAX_FAIL_PER_EMAIL = 5
MAX_FAIL_PER_IP    = 20
LOCK_WINDOW        = timedelta(minutes=15)
UNSAFE_METHODS     = {"POST", "PUT", "PATCH", "DELETE"}
MAX_PASSWORD_BYTES = 72              # bcrypt 只看前 72 bytes


class Teacher(UserMixin):
    def __init__(self, row: dict):
        self.id        = row["id"]
        self.email     = row["email"]
        self.name      = row["name"]
        self.role      = row["role"]
        self.school_id = row.get("school_id")
        self._active   = bool(row.get("is_active", True))

    def get_id(self) -> str:
        return str(self.id)

    @property
    def is_active(self) -> bool:
        return self._active

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"


@login_manager.user_loader
def load_teacher(user_id):
    ts = session.get(LOGIN_TS_KEY)
    if not ts or time.time() - ts > SESSION_MAX_AGE:
        return None
    try:
        row = db.get_teacher_by_id(int(user_id))
    except Exception as e:
        log.warning("讀取教師帳號失敗：%s", type(e).__name__)
        return None
    if not row or not row.get("is_active"):
        return None
    return Teacher(row)


@login_manager.unauthorized_handler
def _unauthorized_handler():
    return _unauthorized()


# ── CSRF ──────────────────────────────────────────────────────
def csrf_token() -> str:
    tok = session.get("csrf")
    if not tok:
        tok = session["csrf"] = secrets.token_urlsafe(32)
    return tok


def check_csrf() -> bool:
    expected = session.get("csrf") or ""
    sent = request.headers.get("X-CSRF-Token") or request.form.get("csrf_token") or ""
    return bool(expected) and hmac.compare_digest(sent, expected)


# ── 裝飾器 ────────────────────────────────────────────────────
def _wants_html() -> bool:
    return request.method == "GET" and request.accept_mimetypes.best == "text/html"


def _unauthorized():
    if _wants_html():
        return redirect(url_for("teacher.login"))
    return jsonify({"ok": False, "error": "請先登入"}), 401


def teacher_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            return _unauthorized()
        if request.method in UNSAFE_METHODS and not check_csrf():
            return jsonify({"ok": False, "error": "CSRF 驗證失敗"}), 403
        return f(*args, **kwargs)
    return wrapper


def admin_required(f):
    @teacher_required
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user.is_admin:
            return jsonify({"ok": False, "error": "需要管理員權限"}), 403
        return f(*args, **kwargs)
    return wrapper


# ── 登入驗證與失敗次數限制 ─────────────────────────────────────
_dummy_hash = None


def verify_password(row, password: str) -> bool:
    """帳號不存在時也跑一次 bcrypt，避免用回應時間猜出帳號是否存在。"""
    global _dummy_hash
    if _dummy_hash is None:
        _dummy_hash = bcrypt.generate_password_hash("dummy-password").decode()
    password = password or ""
    if len(password.encode("utf-8")) > MAX_PASSWORD_BYTES:
        bcrypt.check_password_hash(_dummy_hash, "x")
        return False
    ok = bcrypt.check_password_hash(row["password_hash"] if row else _dummy_hash, password)
    return bool(row) and ok


def client_ip() -> str:
    return request.remote_addr or "unknown"


def is_locked(email: str, ip: str) -> bool:
    since = (datetime.now(timezone.utc) - LOCK_WINDOW).isoformat()
    by_email, by_ip = db.count_login_failures(email, ip, since)
    return by_email >= MAX_FAIL_PER_EMAIL or by_ip >= MAX_FAIL_PER_IP


def record_attempt(email: str, ip: str, success: bool) -> None:
    db.record_login_attempt(email, ip, success)
    if random.random() < 0.05:   # 偶爾清掉一週前的舊紀錄
        before = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        try:
            db.purge_old_login_attempts(before)
        except Exception:
            pass
