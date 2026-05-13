"""
camera.py  ── MediaPipe + OpenCV 影像處理
"""

import os
import time
import threading
import cv2
import numpy as np

from game_state import game_lock, game_state

# 設定
MODEL_PATH = os.environ.get("MODEL_PATH", "hand_landmarker.task")
SMOOTH = 0.65
LOST_TIMEOUT = 0.8

# 嘗試引入 cv2 & mediapipe
try:
    import mediapipe as mp
    from mediapipe.tasks import python as mp_python
    from mediapipe.tasks.python import vision

    CV2_OK = True
except ImportError:
    CV2_OK = False

MEDIAPIPE_OK = False
landmarker = None
cap = None
cap_lock = threading.Lock()

if CV2_OK:
    try:
        BaseOptions = mp_python.BaseOptions
        HandLandmarker = vision.HandLandmarker
        HandLandmarkerOptions = vision.HandLandmarkerOptions
        VisionRunningMode = vision.RunningMode

        options = HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=MODEL_PATH),
            running_mode=VisionRunningMode.VIDEO,
            num_hands=1,
        )
        landmarker = HandLandmarker.create_from_options(options)
        MEDIAPIPE_OK = True
        print("[OK] MediaPipe 初始化成功")
    except Exception as e:
        print(f"[警告] MediaPipe 初始化失敗: {e}")


def get_cap():
    """取得攝影機物件"""
    global cap
    if not CV2_OK:
        return None
    with cap_lock:
        if cap is None or not cap.isOpened():
            cap = cv2.VideoCapture(0)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    return cap


def process_frame():
    """處理單一幀並更新遊戲狀態"""
    camera = get_cap()
    if camera is None:
        return None

    ret, frame = camera.read()
    if not ret:
        return None

    frame = cv2.flip(frame, 1)
    W = int(camera.get(cv2.CAP_PROP_FRAME_WIDTH))
    H = int(camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
    thumb_mode = False

    if MEDIAPIPE_OK and landmarker:
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        ts = int(time.time() * 1000)
        res = landmarker.detect_for_video(mp_img, ts)

        with game_lock:
            gs = game_state
            if res.hand_landmarks:
                lm = res.hand_landmarks[0]
                gs["last_seen"] = time.time()

                # 食指朝上手勢判斷
                if lm[8].y < lm[5].y and lm[12].y > lm[10].y:
                    thumb_mode = True
                    nx = max(35, min(W - 35, int(lm[8].x * W)))
                    ny = max(55, min(int(H * 0.82), int(lm[8].y * H)))

                    gs["cursor_x"] = int(SMOOTH * gs["cursor_x"] + (1 - SMOOTH) * nx)
                    gs["cursor_y"] = int(SMOOTH * gs["cursor_y"] + (1 - SMOOTH) * ny)
                    gs["last_valid_x"] = gs["cursor_x"]
                    gs["last_valid_y"] = gs["cursor_y"]
            else:
                if time.time() - gs["last_seen"] < LOST_TIMEOUT:
                    thumb_mode = True
                    gs["cursor_x"] = gs["last_valid_x"]
                    gs["cursor_y"] = gs["last_valid_y"]

            gs["thumb_active"] = thumb_mode
            gs["frame_w"] = W
            gs["frame_h"] = H

    return frame


def generate_video_stream():
    """生成 MJPEG 串流"""
    while True:
        frame = process_frame()
        if frame is None:
            time.sleep(0.05)
            continue

        _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n\r\n" 
               + buf.tobytes() + b"\r\n")
        time.sleep(0.033)