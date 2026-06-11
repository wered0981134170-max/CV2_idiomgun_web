"""
config.py  ── 全局設定
"""

import os

class Config:
    MODEL_PATH = os.environ.get("MODEL_PATH", "hand_landmarker.task")
    ACTIVE_GRADE = "junior"   # "elementary_low" 或 "elementary_high" 或 "junior"
    WRONG_RATIO = 0.5       # 錯誤選項的比例
    TOTAL_Q = 10            # 總題數
    GRADE_MAX_Q = {
        "elementary_low":  10,
        "elementary_high": 10,
        "junior":          10,
    }
    Q_TIME_LIMIT = 15.0     # 每題的時間限制
    HOVER_TIME = 1.5        # 懸停時間
    SMOOTH = 0.65           # 平滑參數(新位置 = 舊位置 * 0.65 + 本次偵測 * 0.35)
    LOST_TIMEOUT = 0.8      # 失去追蹤的超時時間