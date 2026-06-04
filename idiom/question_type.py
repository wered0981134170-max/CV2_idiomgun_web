"""
question_type.py  ── 題目類型管理
"""
 
import random
import json
import pathlib as pl
from typing import List, Dict, Any
import os

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
                print(f"已載入 {grade}: {len(data)} 個成語")
        else:
            print(f"警告：找不到檔案 {path}")
            all_data[grade] = []
    return all_data


# 全域資料
questions_data = load_all_questions()


def get_questions_by_grade(grade: str = "elementary_low", n: int = 10,
                          typo_ratio: float = 0.5) -> List[Dict]:
    """
    從指定年級的 JSON 檔案中抽取題目。

    出題順序：前半段全是 typo（錯字）題，後半段全是 application（應用）題。
    每道成語各出一題 typo + 一題 application，共需 n/2 個成語（n 應為偶數）。
    若 n 為奇數，typo 多一題。
    """
    if grade not in questions_data:
        raise ValueError(f"未知的年級: {grade}")

    idioms_list = questions_data[grade]

    # 需要幾個成語：typo 和 application 各 ceil/floor(n/2) 題
    n_typo = (n + 1) // 2          # 前半段：ceil(n/2)
    n_app  = n // 2                # 後半段：floor(n/2)
    n_idioms = max(n_typo, n_app)  # 每個成語各出兩種，所以只需 n_idioms 個

    if n_idioms > len(idioms_list):
        print(f"警告：要求 {n_idioms} 個成語，但僅有 {len(idioms_list)} 個，將全部取出")
        n_idioms = len(idioms_list)
        n_typo   = n_idioms
        n_app    = n_idioms

    selected_idioms = random.sample(idioms_list, n_idioms)

    typo_questions = []
    app_questions  = []

    for idiom_data in selected_idioms:
        idiom   = idiom_data["idiom"]
        q_types = idiom_data.get("questions", {})
        common  = {
            "idiom":       idiom,
            "meaning":     idiom_data.get("meaning", ""),
            "explanation": idiom_data.get("explanation", ""),
            "grade":       idiom_data.get("grade"),
        }

        # ── typo 題 ──
        if "typo" in q_types:
            q = q_types["typo"]
            correct_char = q["answer"]          # 正確字，如 "俱"
            wrong_opts   = q.get("options", []) # 三個錯字，如 ["具","且","巨"]

            # 隨機選一個錯字填入 _ 位置，變成「兩敗具傷」
            inserted = random.choice(wrong_opts) if wrong_opts else correct_char
            display  = q["question"].replace("_", inserted, 1)

            # 四個選項 = 三個錯字 + 正確字，洗牌
            four_opts = wrong_opts + [correct_char]
            random.shuffle(four_opts)

            typo_questions.append({
                **common,
                "type":         "wrong",
                "display":      display,        # 如 "兩敗具傷"（已填入錯字）
                "answer":       inserted,       # 使用者要選出的就是這個被填入的錯字
                "correct_char": correct_char,   # 正確字（用於結果卡顯示）
                "options":      four_opts,      # 四個選項供使用者選
                "hint":         "找出成語中的錯字",
            })

        # ── application 題 ──
        if "application" in q_types:
            q = q_types["application"]
            app_questions.append({
                **common,
                "type":    "application",
                "display": q["question"],       # 上下文填空句
                "answer":  q["answer"],         # 完整成語
                "options": q.get("options", []),
                "hint":    "選擇正確的成語填入空格",
            })

    # 各自洗牌（同類題內部隨機），但保持「typo 在前、application 在後」的順序
    random.shuffle(typo_questions)
    random.shuffle(app_questions)

    # 截到需要的數量，然後拼接
    return typo_questions[:n_typo] + app_questions[:n_app]

# ==================== 測試 ====================
if __name__ == "__main__":
    print("=== 成語題庫載入測試 ===\n")
    
    # 測試 elementary_low
    qs = get_questions_by_grade(grade="elementary_low", n=8, typo_ratio=0.6)
    
    for i, q in enumerate(qs, 1):
        if q["type"] == "wrong":
            print(f"[{i:2d}] 找錯字：{q['display']:15} → 答案：{q['answer']}")
        else:
            print(f"[{i:2d}] 應用題：{q['display'][:35]:35}... → 答案：{q['answer']}")