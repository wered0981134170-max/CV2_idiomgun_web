"""
routes.py  ── 所有 Flask 路由（Session-based 多人版）
每個玩家透過 Flask session 維護各自獨立的遊戲狀態，互不干擾
"""

from flask import Blueprint, render_template, jsonify, request, session
import time
import uuid

from .game_state import get_state, delete_state
from .question_type import get_questions_by_grade
from .db import save_score, get_top
from .config import Config

main_bp = Blueprint('main', __name__)


def _sid() -> str:
    """取得（或建立）本次請求的 session id"""
    if "sid" not in session:
        session["sid"] = uuid.uuid4().hex
    return session["sid"]


# ── 網頁路由 ─────────────────────────────────────
@main_bp.route("/")
def index():
    return render_template("index.html")


# ── 遊戲 API ─────────────────────────────────────
@main_bp.route("/start_game", methods=["POST"])
def start_game():
    # 年級由後端 Config.ACTIVE_GRADE 控制
    # 未來支援前端選難度：
    #   diff  = (request.json or {}).get("difficulty", "easy")
    #   grade = Config.DIFFICULTY_MAP.get(diff, Config.ACTIVE_GRADE)
    grade   = Config.ACTIVE_GRADE
    total   = Config.GRADE_MAX_Q.get(grade, Config.TOTAL_Q)
    wrong_r = Config.WRONG_RATIO

    questions = get_questions_by_grade(grade=grade, n=total, typo_ratio=wrong_r)

    gs = get_state(_sid())
    gs["state"]        = "play"
    gs["q_index"]      = 0
    gs["score"]        = 0
    gs["questions"]    = questions
    gs["total_q"]      = len(questions)
    gs["q_start_time"] = time.time()
    gs["ans_result"]   = None

    return jsonify({
        "ok":    True,
        "total": len(questions),
        "grade": grade,
        "label": cfg.get("label", grade),
    })


@main_bp.route("/question")
def get_question():
    gs  = get_state(_sid())
    idx = gs["q_index"]
    qs  = gs["questions"]

    if idx >= len(qs):
        return jsonify({"done": True, "score": gs["score"]})

    q       = qs[idx]
    elapsed = time.time() - gs["q_start_time"]
    remain  = max(0.0, Config.Q_TIME_LIMIT - elapsed)

    return jsonify({
        "done":   False,
        "index":  idx,
        "total":  gs["total_q"],
        "score":  gs["score"],
        "remain": round(remain, 2),
        "q_time": Config.Q_TIME_LIMIT,
        **{k: q.get(k) for k in ["type", "idiom", "display", "options",
                                  "hint", "explanation", "correct_char"]}
    })


@main_bp.route("/answer", methods=["POST"])
def submit_answer():
    chosen = (request.json or {}).get("chosen", "")

    gs  = get_state(_sid())
    idx = gs["q_index"]
    qs  = gs["questions"]

    if idx >= len(qs):
        return jsonify({"error": "no question"})

    q           = qs[idx]
    correct     = (chosen == q["answer"])
    correct_str = q.get("correct_char") or q["answer"]
    result      = "correct" if correct else "wrong"

    if correct:
        gs["score"] += 10
    gs["ans_result"] = result
    gs["state"]      = "result"

    return jsonify({
        "result":      result,
        "correct_str": correct_str,
        "idiom":       q["idiom"],
        "score":       gs["score"],
    })


@main_bp.route("/timeout", methods=["POST"])
def submit_timeout():
    gs  = get_state(_sid())
    idx = gs["q_index"]
    qs  = gs["questions"]

    if idx >= len(qs):
        return jsonify({"error": "no question"})

    q           = qs[idx]
    correct_str = q.get("correct_char") or q.get("answer", "")
    gs["ans_result"] = "timeout"
    gs["state"]      = "result"

    return jsonify({
        "result":      "timeout",
        "correct_str": correct_str,
        "idiom":       q["idiom"],
        "score":       gs["score"],
    })


@main_bp.route("/next", methods=["POST"])
def next_question():
    gs = get_state(_sid())
    gs["q_index"] += 1

    if gs["q_index"] >= len(gs["questions"]):
        gs["state"] = "final"
        return jsonify({"state": "final", "score": gs["score"],
                        "total": len(gs["questions"])})

    gs["state"]        = "play"
    gs["q_start_time"] = time.time()
    gs["ans_result"]   = None
    return jsonify({"state": "play", "q_index": gs["q_index"]})


@main_bp.route("/reset", methods=["POST"])
def reset_game():
    delete_state(_sid())
    return jsonify({"ok": True})


# ── 排行榜 ─────────────────────────────────────
@main_bp.route("/leaderboard", methods=["GET"])
def leaderboard_get():
    return jsonify(get_top(10))


@main_bp.route("/leaderboard", methods=["POST"])
def leaderboard_post():
    data     = request.json or {}
    name     = data.get("name", "").strip() or "匿名"
    score    = int(data.get("score", 0))
    total    = int(data.get("total", 100))
    duration = int(data.get("duration", 0))

    entry = save_score(name, score, total, duration)
    return jsonify({"ok": True, "entry": entry})