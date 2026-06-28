"""
question_type.py  ── 題目類型管理
"""
 
import random
import json
import logging
import pathlib as pl
from typing import List, Dict, Any

log = logging.getLogger(__name__)

# 相對於此文件位置的父目錄中的 data 文件夾
DATA_DIR = pl.Path(__file__).parent.parent / "data"

FILES = {
    "elementary_low": "elementary_a_low.json",
    "elementary_high": "elementary_b_high.json",
    "junior": "junior.json"
}

# 載入所有題目資料
def load_all_questions() -> Dict[str, List[Dict]]:
    all_data = {}
    for grade, filename in FILES.items():
        path = DATA_DIR / filename
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                all_data[grade] = data
                log.info("已載入 %s: %d 個成語", grade, len(data))
        else:
            log.warning("找不到檔案 %s", path)
            all_data[grade] = []
    return all_data


# 全域資料
questions_data = load_all_questions()


def get_questions_by_grade(grade: str = "elementary_low", n: int = 4) -> List[Dict]:
    """
    從指定年級抽取 n 個成語，每個成語依序出 typo → compose → application 共三題。
    回傳順序：全部 typo → 全部 compose → 全部 application，共 n×3 題。
    """
    if grade not in questions_data:
        raise ValueError(f"未知的年級: {grade}")

    idioms_list = questions_data[grade]

    # 只使用同時有三種題型的成語
    full_pool = [d for d in idioms_list
                 if all(t in d.get("questions", {})
                        for t in ("typo", "compose", "application"))]

    if not full_pool:
        log.warning("年級 %s 沒有三種題型齊全的成語", grade)
        return []

    n = min(n, len(full_pool))
    selected = random.sample(full_pool, n)

    typo_qs    = []
    compose_qs = []
    app_qs     = []

    for idiom_data in selected:
        idiom   = idiom_data["idiom"]
        q_types = idiom_data["questions"]
        common  = {
            "idiom":       idiom,
            "meaning":     idiom_data.get("meaning", ""),
            "explanation": idiom_data.get("explanation", ""),
        }

        # ── typo 題 ──
        q            = q_types["typo"]
        correct_char = q["answer"]
        wrong_opts   = q.get("options", [])
        inserted     = random.choice(wrong_opts) if wrong_opts else correct_char
        display      = q["question"].replace("_", inserted, 1)
        four_opts    = wrong_opts + [correct_char]
        random.shuffle(four_opts)
        typo_qs.append({
            **common,
            "type":         "wrong",
            "display":      display,
            "answer":       inserted,
            "correct_char": correct_char,
            "options":      four_opts,
            "hint":         "找出成語中的錯字",
        })

        # ── compose 題 ──
        q    = q_types["compose"]
        opts = list(q.get("options", []))
        random.shuffle(opts)
        compose_qs.append({
            **common,
            "type":    "compose",
            "display": q["question"],
            "answer":  q["answer"],
            "options": opts,
            "hint":    "將字拼成正確的成語",
        })

        # ── application 題 ──
        q = q_types["application"]
        app_qs.append({
            **common,
            "type":    "application",
            "display": q["question"],
            "answer":  q["answer"],
            "options": q.get("options", []),
            "hint":    "選擇正確的成語填入空格",
        })

    return typo_qs + compose_qs + app_qs

# ==================== 測試 ====================
if __name__ == "__main__":
    print("=== 成語題庫載入測試 ===\n")
    qs = get_questions_by_grade(grade="elementary_high", n=4)
    for i, q in enumerate(qs, 1):
        label = {"wrong": "找錯字", "compose": "組字", "application": "應用"}[q["type"]]
        print(f"[{i:2d}] {label}：{q['display'][:30]:30} → 答案：{q['answer']}")