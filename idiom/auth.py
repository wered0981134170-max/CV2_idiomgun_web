"""
auth.py  ── 登入系統（Flask-Login + bcrypt）

路由：
  POST /auth/register  — 註冊
  POST /auth/login     — 登入
  POST /auth/logout    — 登出
  GET  /auth/me        — 目前登入狀態 + 個人最高分
"""

import re
from flask import Blueprint, request, jsonify
from flask_login import UserMixin, login_user, logout_user, current_user

from .extensions import login_manager, bcrypt
from .db import create_user, get_user_by_username, get_user_by_id, get_user_best

auth_bp = Blueprint("auth", __name__)

USERNAME_RE = re.compile(r'^[\w一-鿿]{2,20}$')


# ── Flask-Login User 類 ───────────────────────────────────────
class User(UserMixin):
    def __init__(self, row: dict):
        self.id       = str(row["id"])
        self.username = row["username"]


@login_manager.user_loader
def load_user(user_id: str):
    row = get_user_by_id(int(user_id))
    return User(row) if row else None


@login_manager.unauthorized_handler
def unauthorized():
    return jsonify({"ok": False, "error": "請先登入"}), 401


# ── 驗證輸入 ──────────────────────────────────────────────────
def _validate(username, password):
    username = (username or "").strip()
    password = password or ""
    if not USERNAME_RE.match(username):
        return None, None, "帳號僅允許中英文、數字、底線（2-20字）"
    if len(password) < 6:
        return None, None, "密碼至少需要 6 個字元"
    return username, password, None


# ── 路由 ─────────────────────────────────────────────────────
@auth_bp.route("/auth/register", methods=["POST"])
def register():
    data = request.json or {}
    username, password, err = _validate(data.get("username"), data.get("password"))
    if err:
        return jsonify({"ok": False, "error": err}), 400

    pw_hash = bcrypt.generate_password_hash(password).decode("utf-8")
    try:
        user_row = create_user(username, pw_hash)
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)}), 409

    login_user(User(user_row), remember=True)
    return jsonify({"ok": True, "username": username})


@auth_bp.route("/auth/login", methods=["POST"])
def login():
    data = request.json or {}
    username, password, err = _validate(data.get("username"), data.get("password"))
    if err:
        return jsonify({"ok": False, "error": err}), 400

    row = get_user_by_username(username)
    if not row or not bcrypt.check_password_hash(row["password_hash"], password):
        return jsonify({"ok": False, "error": "帳號或密碼錯誤"}), 401

    login_user(User(row), remember=True)
    return jsonify({"ok": True, "username": username})


@auth_bp.route("/auth/logout", methods=["POST"])
def logout():
    logout_user()
    return jsonify({"ok": True})


@auth_bp.route("/auth/me", methods=["GET"])
def me():
    if not current_user.is_authenticated:
        return jsonify({"logged_in": False})
    best = get_user_best(int(current_user.id))
    return jsonify({
        "logged_in": True,
        "username":  current_user.username,
        "best":      best,
    })
