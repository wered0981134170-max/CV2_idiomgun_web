"""
game_state.py  ── Session-based 遊戲狀態管理
每個玩家透過 Flask session id 各自維護一份獨立的遊戲狀態
"""

import time
import threading

# 全域字典：sid → game_state dict
_sessions: dict = {}
_sessions_lock = threading.Lock()


def make_state() -> dict:
    """建立一份全新的遊戲狀態"""
    return {
        "state":        "start",
        "q_index":      0,
        "score":        0,
        "q_start_time": 0.0,
        "ans_result":   None,
        "questions":    [],
        "total_q":      10,
    }


def get_state(sid: str) -> dict:
    """取得（或建立）指定 session 的遊戲狀態"""
    with _sessions_lock:
        if sid not in _sessions:
            _sessions[sid] = make_state()
        return _sessions[sid]


def delete_state(sid: str) -> None:
    """刪除指定 session 的遊戲狀態（reset 時呼叫）"""
    with _sessions_lock:
        _sessions.pop(sid, None)


# ── 向下相容：舊程式碼若直接 import game_lock / game_state 仍可運作 ──
# （routes.py 改完後可移除）
import threading
game_lock  = threading.Lock()
game_state = make_state()