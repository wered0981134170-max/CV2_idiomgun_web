"""
question_type.py  ── 題目類型管理
"""
 
import random
import json
import pathlib as pl
from typing import List, Dict, Any

DATA_DIR = pl.Path("data")

FILES = {
    "elementary_low": "elementary_a_low.json",
    "elementary_high": "elementary_a_high.json",
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
    從指定年級的 JSON 檔案中隨機抽取題目
    """
    if grade not in questions_data:
        raise ValueError(f"未知的年級: {grade}")
    
    idioms_list = questions_data[grade]
    if n > len(idioms_list):
        print(f"警告：要求 {n} 題，但僅有 {len(idioms_list)} 個成語，將全部取出")
        n = len(idioms_list)

    selected_idioms = random.sample(idioms_list, n)

    questions = []

    for idiom_data in selected_idioms:
        idiom = idiom_data["idiom"]
        q_types = idiom_data.get("questions", {})

        # 決定出題型態
        if random.random() < typo_ratio and "typo" in q_types:
            q = q_types["typo"]
            question_dict = {
                "type": "wrong",
                "idiom": idiom,
                "display": q["question"],           # 如 "兩敗__傷"
                "answer": q["answer"],              # 正確字
                "options": q.get("options"),        # 若有提供選項
                "hint": "找出錯字並秒準 1.5 秒",
                "meaning": idiom_data.get("meaning", ""),
                "explanation": idiom_data.get("explanation", ""),
                "grade": idiom_data.get("grade")
            }
        elif "application" in q_types:
            q = q_types["application"]
            question_dict = {
                "type": "application",
                "idiom": idiom,
                "display": q["question"],           # 上下文填空題
                "answer": q["answer"],              # 完整成語
                "options": q.get("options", []),
                "hint": "選擇正確的成語 1.5 秒",
                "meaning": idiom_data.get("meaning", ""),
                "explanation": idiom_data.get("explanation", ""),
                "grade": idiom_data.get("grade")
            }
        else:
            # 備用：如果都沒有就跳過
            continue

        questions.append(question_dict)

    random.shuffle(questions)
    return questions


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