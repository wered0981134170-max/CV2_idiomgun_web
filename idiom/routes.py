"""
routes.py  ── 所有 Flask 路由
"""

from flask import Blueprint, render_template, Response, jsonify, request
import time

from game_state import game_lock, game_state
from question_type import get_questions_by_grade
from db import save_score, get_top
from camera import generate_video_stream, CV2_OK
from config import Config

main_bp = Blueprint('main', __name__)

# 難度級別映射
DIFFICULTY_MAP = {
    "easy": "elementary_low",
    "medium": "elementary_high",
    "hard": "junior"
}

# ── 網頁路由 ─────────────────────────────────────
@main_bp.route("/")
def index():
    return render_template("index.html", total_q=10, q_time=15)


@main_bp.route("/video_feed")
def video_feed():
    if not CV2_OK:
        return Response(status=204)
    return Response(generate_video_stream(),
                    mimetype="multipart/x-mixed-replace; boundary=frame")


@main_bp.route("/state")
def get_state():
    with game_lock:
        gs = game_state
        return jsonify({
            "cursor_x": gs["cursor_x"],
            "cursor_y": gs["cursor_y"],
            "thumb_active": gs["thumb_active"],
            "frame_w": gs["frame_w"],
            "frame_h": gs["frame_h"],
        })


# ── 遊戲 API ─────────────────────────────────────
@main_bp.route("/start_game", methods=["POST"])
def start_game():
    data = request.json or {}
    diff = data.get("difficulty", "easy")
    # 將前端難度值映射到後端年級值
    grade = DIFFICULTY_MAP.get(diff, "elementary_low")
    wrong_r = float(data.get("wrong_ratio", 0.5))
    total = int(data.get("total_q", 10))

    total = Config.GRADE_MAX_Q.get(grade, Config.TOTAL_Q)
    questions = get_questions_by_grade(grade=grade, n=total, typo_ratio=wrong_r)

    with game_lock:
        gs = game_state
        gs["state"] = "play"
        gs["q_index"] = 0
        gs["score"] = 0
        gs["questions"] = questions
        gs["q_start_time"] = time.time()
        gs["ans_result"] = None
        gs["total_q"]      = len(questions)

    return jsonify({"ok": True, "total": len(questions)}) 


@main_bp.route("/question")
def get_question():
    with game_lock:
        gs = game_state
        idx = gs["q_index"]
        qs = gs["questions"]
        total_q = gs.get("total_q", Config.TOTAL_Q)   

        if idx >= len(qs):
            return jsonify({"done": True, "score": gs["score"]})

        q = qs[idx]
        elapsed = time.time() - gs["q_start_time"]
        remain = max(0.0, 15.0 - elapsed)

        return jsonify({
            "done": False,
            "index": idx,
            "total": total_q,
            "score": gs["score"],
            "remain": round(remain, 2),
            "q_time": 15,
            **{k: q.get(k) for k in ["type", "idiom", "display", "template", "options", 
                                    "hint", "difficulty", "explanation", "correct_char"]}
        })


@main_bp.route("/answer", methods=["POST"])
def submit_answer():
    data = request.json or {}
    chosen = data.get("chosen", "")

    with game_lock:
        gs = game_state
        idx = gs["q_index"]
        qs = gs["questions"]
        if idx >= len(qs):
            return jsonify({"error": "no question"})

        q = qs[idx]
        correct = chosen == q["answer"]
        # typo 題用 correct_char（正確字）顯示，其他題用 answer
        correct_str = q.get("correct_char") or q["answer"]

        result = "correct" if correct else "wrong"
        if correct:
            gs["score"] += 10

        gs["ans_result"] = result
        gs["state"] = "result"

        return jsonify({
            "result": result,
            "correct_str": correct_str,
            "idiom": q["idiom"],
            "score": gs["score"],
        })


@main_bp.route("/timeout", methods=["POST"])
def submit_timeout():
    with game_lock:
        gs = game_state
        idx = gs["q_index"]
        qs = gs["questions"]
        if idx >= len(qs):
            return jsonify({"error": "no question"})

        q = qs[idx]
        correct_str = q.get("answer", "")
        gs["ans_result"] = "timeout"
        gs["state"] = "result"

        return jsonify({
            "result": "timeout",
            "correct_str": correct_str,
            "idiom": q["idiom"],
            "score": gs["score"],
        })


@main_bp.route("/next", methods=["POST"])
def next_question():
    with game_lock:
        gs = game_state
        gs["q_index"] += 1

        if gs["q_index"] >= len(gs["questions"]):
            gs["state"] = "final"
            return jsonify({"state": "final", "score": gs["score"],
                            "total": len(gs["questions"])})

        gs["state"] = "play"
        gs["q_start_time"] = time.time()
        gs["ans_result"] = None
        return jsonify({"state": "play", "q_index": gs["q_index"]})


@main_bp.route("/reset", methods=["POST"])
def reset_game():
    with game_lock:
        gs = game_state
        gs["state"] = "start"
        gs["q_index"] = 0
        gs["score"] = 0
        gs["questions"] = []
    return jsonify({"ok": True})


# ── 排行榜 ─────────────────────────────────────
@main_bp.route("/leaderboard", methods=["GET"])
def leaderboard_get():
    return jsonify(get_top(10))


@main_bp.route("/leaderboard", methods=["POST"])
def leaderboard_post():
    data = request.json or {}
    name = data.get("name", "").strip() or "匿名"
    score = int(data.get("score", 0))
    total = int(data.get("total", 100))
    duration = int(data.get("duration", 0))

    entry = save_score(name, score, total, duration)
    return jsonify({"ok": True, "entry": entry})