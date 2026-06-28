"""
routes.py  ── 所有 Flask 路由（純前端主導架構）

後端只做三件事：
  1. 提供首頁 HTML
  2. /get_all_questions  一次吐出所有題目給前端
  3. /leaderboard        排行榜讀寫（已識別學生自動帶入班級座號姓名）
遊戲狀態（進度、分數、計時）全部由前端 JavaScript 管理。
"""

from flask import Blueprint, render_template, jsonify, request, session

from .question_type import get_questions_by_grade
from .db import save_score, get_top, reset_table
from .config import Config

main_bp = Blueprint('main', __name__)


# ── 網頁路由 ─────────────────────────────────────
@main_bp.route("/")
def index():
    return render_template("index.html")


# ── 題目 API（一次全給） ─────────────────────────
@main_bp.route("/get_all_questions", methods=["GET"])
def get_all_questions():
    grade = request.args.get("grade", Config.ACTIVE_GRADE)
    if grade not in ("elementary_low", "elementary_high", "junior"):
        grade = Config.ACTIVE_GRADE

    try:
        n = int(request.args.get("n", 5))
    except (TypeError, ValueError):
        n = 5
    n = max(1, min(n, 10))

    questions = get_questions_by_grade(grade=grade, n=n)

    keys = ["type", "idiom", "display", "options", "answer",
            "correct_char", "hint", "meaning", "explanation", "difficulty"]
    return jsonify({
        "total": len(questions),
        "questions": [{k: q.get(k) for k in keys} for q in questions],
    })


# ── 排行榜 ─────────────────────────────────────
@main_bp.route("/leaderboard", methods=["GET"])
def leaderboard_get():
    return jsonify(get_top(5))


@main_bp.route("/leaderboard", methods=["POST"])
def leaderboard_post():
    data    = request.json or {}
    student = session.get("student")

    # 已識別學生：從 session 取班級、座號、姓名
    if student:
        class_name = student["class_name"]
        seat_no    = student["seat_no"]
        name       = student["name"]
    else:
        class_name = None
        seat_no    = None
        name       = (data.get("name") or "").strip()[:20] or "匿名"

    try:
        score    = max(0, min(int(data.get("score",    0)),  10000))
        total    = max(1, min(int(data.get("total",  100)),  10000))
        duration = max(0, min(int(data.get("duration", 0)), 86400))
    except (TypeError, ValueError):
        return jsonify({"ok": False, "error": "invalid payload"}), 400

    entry = save_score(name, score, total, duration, class_name, seat_no)
    return jsonify({"ok": True, "entry": entry})


@main_bp.route("/leaderboard/reset", methods=["POST"])
def leaderboard_reset():
    reset_table()
    return jsonify({"ok": True})
# 清除資料，在瀏覽器 Console 執行：
# fetch('/leaderboard/reset', {method:'POST'}).then(r=>r.json()).then(console.log)
