import time
import threading

game_lock = threading.Lock()

game_state = {
    "state": "start",
    "q_index": 0,
    "score": 0,
    "q_start_time": 0.0,
    "ans_result": None,
    "questions": [],
    "cursor_x": 640,
    "cursor_y": 360,
    "thumb_active": False,
    "hover_target": None,
    "hover_start": None,
    "hover_progress": 0.0,
    "last_seen": time.time(),
    "last_valid_x": 640,
    "last_valid_y": 360,
    "frame_w": 1280,
    "frame_h": 720,
}