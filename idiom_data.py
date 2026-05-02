# idiom_data.py
import random

# =====================
# 成語資料
# =====================
idioms = {

"畫蛇添足":{
    0:["劃","晝","書"],
    1:["它"],
    2:["填","婖"]
},

"一鼓作氣":{
    1:["股"],
    2:["做"],
    3:["汽","棄"]
},

"破釜沉舟":{
    0:["坡","波","披"],
    1:["斧"],
    2:["沈"]
},

"一目了然":{
    1:["自","且","日"],
    2:["瞭"],
    3:["燃","染"]
},

"一箭雙鵰":{
    1:["剪","劍"],
    2:["爽"],
    3:["雕","凋","鯛"]
},

"虎視眈眈":{
    1:["式","士","示"],
    2:["耽"],
    3:["耽"]
},

"青出於藍":{
    0:["清"],
    2:["于"],
    3:["籃"]
},

"當機立斷":{
    0:["檔","擋"],
    1:["基","奇"],
    3:["段","鍛"]
},

"半途而廢":{
    0:["牛","丰"],
    1:["圖","徒","徙"],
    3:["費"]
},

"如魚得水":{
    0:["奴"],
    1:["漁"],
    2:["德"]
},

}

# 選項池
options_pool = list("家國山水風雲花草人口手足心肝腦頭耳目鼻天地日月星空海河湖江田土木火金石")

# 成語解析
explanations = {
    "畫蛇添足": "「畫」一條「蛇」，又「添」上腳",
    "一鼓作氣": "打一次「鼓」，「作」出「氣勢」",
    "破釜沉舟": "「打破」「鍋釜」，「沉」掉「船」",
    "一目了然": "「一眼」看去，「了解」「然後」全懂",
    "一箭雙鵰": "「一箭」射出，「中」兩隻「鳥」",
    "虎視眈眈": "虎在「看」，「眈眈」地盯著",
    "青出於藍": "「青色」「出自於」「藍色」之調配",
    "當機立斷": "「當下的」「機會」立刻「判斷」要不要",
    "半途而廢": "都到了「一半的路途」，就「作廢」掉了",
    "如魚得水": "「就如」一條「魚」「得到了」水",
}

# 錯字題
def make_wrong_question(idiom: str) -> dict | None:
    pos_data = idioms.get(idiom, {})
    if not pos_data:
        return None

    pos = random.choice(list(pos_data.keys()))
    wrong_char = random.choice(pos_data[pos])

    correct_char = idiom[pos]

    display = list(idiom)
    display[pos] = wrong_char

    return {
        "type": "wrong",
        "idiom": idiom,
        "display": "".join(display),
        "wrong_idx": pos,
        "wrong_char": wrong_char,
        "correct_char": correct_char,
        "hint": "找出錯字並秒準 1.5 秒",
        "explanation": explanations.get(idiom, ""),
    }

# 填空題
def make_fill_question(idiom: str) -> dict | None:
    pos_data = idioms.get(idiom, {})

    if pos_data:
        pos = random.choice(list(pos_data.keys()))
        distractors = pos_data[pos][:]
    else:
        pos = random.randint(0, len(idiom)-1)
        distractors = []

    correct_char = idiom[pos]

    options = [correct_char]

    for c in distractors:
        if c != correct_char and c not in options:
            options.append(c)
        if len(options) == 4:
            break

    while len(options) < 4:
        c = random.choice(options_pool)
        if c not in options:
            options.append(c)

    random.shuffle(options)

    template = list(idiom)
    template[pos] = "＿"

    return {
        "type": "fill",
        "idiom": idiom,
        "template": "".join(template),
        "blank_idx": pos,
        "answer": correct_char,
        "options": options,
        "hint": "秒準正確的字 1.5 秒",
        "explanation": explanations.get(idiom, ""),
    }

# 題目生成
def generate_questions(n=10, wrong_ratio=0.5, difficulty="mixed"):
    all_idioms = list(idioms.keys())

    if n > len(all_idioms):
        raise ValueError("成語數量不足，無法產生不重複題目")

    selected = random.sample(all_idioms, n)  # ⭐關鍵

    questions = []

    for idiom in selected:
        if random.random() < wrong_ratio:
            q = make_wrong_question(idiom)
        else:
            q = make_fill_question(idiom)

        if q:
            questions.append(q)

    random.shuffle(questions)
    return questions

# 測試
# if __name__ == "__main__":
#     qs = generate_questions(10)

#     for i, q in enumerate(qs, 1):
#         if q["type"] == "wrong":
#             print(f"[{i}] 找錯字：{q['display']} → 答案：{q['correct_char']}")
#         else:
#             print(f"[{i}] 填空：{q['template']} → {q['options']} 答案：{q['answer']}")