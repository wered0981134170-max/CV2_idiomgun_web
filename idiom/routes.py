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
    # ★ 修改 1：只回傳前 5 名（原本是10）
    return jsonify(get_top(5))


@main_bp.route("/leaderboard", methods=["POST"])
def leaderboard_post():
    data = request.json or {}
    name     = data.get("name", "").strip() or "匿名"
    score    = int(data.get("score", 0))
    total    = int(data.get("total", 100))
    duration = int(data.get("duration", 0))

    # ── 未來登入系統：可在此接收 user_id，綁定到已登入帳號 ──
    # user_id = data.get("user_id")  # 預留：登入後由前端帶入
    # if user_id:
    #     name = get_username_by_id(user_id)  # 預留：從 users 資料表查名稱

    entry = save_score(name, score, total, duration)
    return jsonify({"ok": True, "entry": entry})

@main_bp.route("/leaderboard/reset", methods=["POST"])
def leaderboard_reset():
    from .db import _conn
    with _conn() as c:
        c.execute("DELETE FROM scores")
        c.execute("DELETE FROM sqlite_sequence WHERE name='scores'")
        c.commit()
    return jsonify({"ok": True})
#清除資料，在瀏覽器 Console 執行
# fetch('/leaderboard/reset', {method:'POST'}).then(r=>r.json()).then(console.log)


# ══════════════════════════════════════════════════════════
# ── 預留：登入系統路由 ─────────────────────────────────
# 未來實作登入功能時，在此區塊新增路由。
# 建議搭配 Flask-Login 或 JWT，並在 db.py 新增 users 資料表。
#
# @main_bp.route("/auth/register", methods=["POST"])
# def register():
#     data = request.json or {}
#     username = data.get("username", "").strip()
#     password = data.get("password", "")
#     # TODO: 驗證、雜湊密碼、寫入 users 資料表
#     return jsonify({"ok": True, "user_id": new_user_id})
#
# @main_bp.route("/auth/login", methods=["POST"])
# def login():
#     data = request.json or {}
#     username = data.get("username", "").strip()
#     password = data.get("password", "")
#     # TODO: 驗證帳密、回傳 session token 或 JWT
#     return jsonify({"ok": True, "token": token, "user_id": user_id, "name": username})
#
# @main_bp.route("/auth/logout", methods=["POST"])
# def logout():
#     # TODO: 清除 session / 廢止 token
#     return jsonify({"ok": True})
#
# @main_bp.route("/auth/me", methods=["GET"])
# def me():
#     # TODO: 從 Authorization header 驗證 token，回傳使用者資訊
#     return jsonify({"user_id": ..., "name": ..., "best_score": ...})
# ══════════════════════════════════════════════════════════
