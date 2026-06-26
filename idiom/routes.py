"""
routes.py  ── 所有 Flask 路由（純前端主導架構）

後端只做三件事：
  1. 提供首頁 HTML
  2. /get_all_questions  一次吐出所有題目給前端
  3. /leaderboard        排行榜讀寫（登入時自動綁定帳號）
遊戲狀態（進度、分數、計時）全部由前端 JavaScript 管理。
"""

from flask import Blueprint, render_template, jsonify, request
from flask_login import current_user

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
    """
    回傳一整局的題目清單。
    前端拿到後自行洗牌、計時、判斷對錯，後端不再介入。

    Query params（均可省略，使用 config 預設值）：
      grade  : elementary_low | elementary_high | junior
      n      : 題數（整數）
    """
    grade = request.args.get("grade", Config.ACTIVE_GRADE)
    if grade not in ("elementary_low", "elementary_high", "junior"):
        grade = Config.ACTIVE_GRADE

    try:
        n = int(request.args.get("n", Config.TOTAL_Q))
    except (TypeError, ValueError):
        n = Config.TOTAL_Q
    n = max(1, min(n, Config.GRADE_MAX_Q.get(grade, Config.TOTAL_Q)))

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
    data = request.json or {}

    # 已登入：使用帳號名稱並記錄 user_id，忽略前端送來的 name
    if current_user.is_authenticated:
        name = current_user.username
        uid  = int(current_user.id)
    else:
        name = (data.get("name") or "").strip()[:20] or "匿名"
        uid  = None

    try:
        score    = max(0, min(int(data.get("score",    0)),  10000))
        total    = max(1, min(int(data.get("total",  100)),  10000))
        duration = max(0, min(int(data.get("duration", 0)), 86400))
    except (TypeError, ValueError):
        return jsonify({"ok": False, "error": "invalid payload"}), 400

    entry = save_score(name, score, total, duration, uid)
    return jsonify({"ok": True, "entry": entry})


@main_bp.route("/leaderboard/reset", methods=["POST"])
def leaderboard_reset():
    reset_table()
    return jsonify({"ok": True})
# 清除資料，在瀏覽器 Console 執行：
# fetch('/leaderboard/reset', {method:'POST'}).then(r=>r.json()).then(console.log)
