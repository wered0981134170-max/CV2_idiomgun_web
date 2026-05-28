# gesture.py  ── 手勢判斷模組

def is_index_up(landmarks) -> bool:
    """
    食指朝上判斷：
    - 食指尖(8) 高於食指掌骨根(5)
    - 中指尖(12) 低於中指第一關節(10)（確保其他手指彎曲）
    """
    if not landmarks or len(landmarks) < 13:
        return False
    return landmarks[8].y < landmarks[5].y and landmarks[12].y > landmarks[10].y


def index_tip_pos(landmarks, frame_w: int, frame_h: int,
                  safe_l=35, safe_r=None, safe_t=55, safe_b=None) -> tuple[int, int]:
    """取得食指尖在畫面中的像素座標"""
    if safe_r is None:
        safe_r = frame_w - 35
    if safe_b is None:
        safe_b = int(frame_h * 0.82)
    tip = landmarks[8]
    nx  = max(safe_l, min(safe_r, int(tip.x * frame_w)))
    ny  = max(safe_t, min(safe_b, int(tip.y * frame_h)))
    return nx, ny