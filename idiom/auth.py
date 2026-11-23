"""
auth.py  ── 學生身分識別（班級 + 座號 + 姓名，無密碼）

路由：
  POST /auth/login   — 設定身分
  POST /auth/logout  — 清除身分
  GET  /auth/me      — 目前身分 + 個人最高分
"""

from flask import Blueprint, request, jsonify, session
from .db import get_best_by_student
from .class_name import normalize_class_name

auth_bp = Blueprint("auth", __name__)


def _validate(class_name, seat_no, name):
    class_name = (class_name or "").strip()[:20]
    name       = (name       or "").strip()[:10]
    if not class_name:
        return None, None, None, "請填寫班級"
    class_name = normalize_class_name(class_name)
    if not class_name:
        return None, None, None, "班級格式無法辨識，請填寫如：三年二班、3甲"
    try:
        seat_no = int(seat_no)
        if not (1 <= seat_no <= 99):
            raise ValueError
    except (TypeError, ValueError):
        return None, None, None, "座號必須是 1–99 的整數"
    if not name:
        return None, None, None, "請填寫姓名"
    return class_name, seat_no, name, None


@auth_bp.route("/auth/login", methods=["POST"])
def login():
    data = request.json or {}
    class_name, seat_no, name, err = _validate(
        data.get("class_name"), data.get("seat_no"), data.get("name")
    )
    if err:
        return jsonify({"ok": False, "error": err}), 400

    session.permanent = True
    session["student"] = {"class_name": class_name, "seat_no": seat_no, "name": name}

    best = get_best_by_student(class_name, seat_no, name)
    return jsonify({"ok": True, "class_name": class_name,
                    "seat_no": seat_no, "name": name, "best": best})


@auth_bp.route("/auth/logout", methods=["POST"])
def logout():
    session.pop("student", None)
    return jsonify({"ok": True})


@auth_bp.route("/auth/me", methods=["GET"])
def me():
    student = session.get("student")
    if not student:
        return jsonify({"logged_in": False})
    # 舊 session 可能還是轉換前的班級文字；無法辨識時保留原文字
    student = {**student,
               "class_name": normalize_class_name(student["class_name"]) or student["class_name"]}
    best = get_best_by_student(
        student["class_name"], student["seat_no"], student["name"]
    )
    return jsonify({"logged_in": True, **student, "best": best})
