"""
routes.py  ── 所有 Flask 路由（純前端主導架構）

後端只做三件事：
  1. 提供首頁 HTML
  2. /get_all_questions  一次吐出所有題目給前端
  3. /leaderboard        排行榜讀寫
遊戲狀態（進度、分數、計時）全部由前端 JavaScript 管理。
"""

from flask import Blueprint, render_template, jsonify, request
from .question_type import get_questions_by_grade
from .db import save_score, get_top
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
    n     = int(request.args.get("n", Config.TOTAL_Q))

    if grade not in ("elementary_low", "elementary_high", "junior"):
        grade = Config.ACTIVE_GRADE

    questions = get_questions_by_grade(
        grade=grade, n=n, typo_ratio=Config.WRONG_RATIO
    )

    # 所有欄位都給前端（含 answer，前端自行判斷對錯）
    keys = ["type", "idiom", "display", "options", "answer",
            "correct_char", "hint", "meaning", "explanation", "difficulty"]
    return jsonify({
        "total": len(questions),
        "questions": [{k: q.get(k) for k in keys} for q in questions],
    })


# ── 排行榜 ─────────────────────────────────────
@main_bp.route("/leaderboard", methods=["GET"])
def leaderboard_get():
    return jsonify(get_top(10))


@main_bp.route("/leaderboard", methods=["POST"])
def leaderboard_post():
    data = request.json or {}
    name     = data.get("name", "").strip() or "匿名"
    score    = int(data.get("score", 0))
    total    = int(data.get("total", 100))
    duration = int(data.get("duration", 0))
    entry = save_score(name, score, total, duration)
    return jsonify({"ok": True, "entry": entry})