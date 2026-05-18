"""
aim_system.py  ── 秒準（Hover-to-Select）判定模組
"""

import time

class AimSystem:
    def __init__(self, hover_time: float = 1.5):
        self.hover_time     = hover_time
        self.current_target = None
        self.hover_start    = None
        self.progress       = 0.0       # 0.0 ~ 1.0
        self.fired          = False     # 本幀是否觸發

    def update(self, target_id, thumb_active: bool):

        self.fired = False

        if not thumb_active or target_id is None:
            self._reset()
            return False

        if target_id != self.current_target:
            self.current_target = target_id
            self.hover_start    = time.time()
            self.progress       = 0.0
            return False

        elapsed       = time.time() - self.hover_start
        self.progress = min(elapsed / self.hover_time, 1.0)

        if self.progress >= 1.0:
            self.fired = True
            self._reset()
            return True

        return False

    def _reset(self):
        self.current_target = None
        self.hover_start    = None
        self.progress       = 0.0

    def get_progress(self, target_id) -> float:
        if target_id != self.current_target:
            return 0.0
        return self.progress
