"""
validators.py  ── 成語資料清理與題目驗證（匯入腳本、教師編輯、AI 產生共用）

validate_questions() 回傳錯誤訊息清單，空清單代表通過。
"""

from collections import Counter
from typing import Any, Dict, List


def strip_strings(obj: Any) -> Any:
    """遞迴清除所有字串（含 dict 的 key）前後空白。"""
    if isinstance(obj, str):
        return obj.strip()
    if isinstance(obj, list):
        return [strip_strings(x) for x in obj]
    if isinstance(obj, dict):
        return {strip_strings(k): strip_strings(v) for k, v in obj.items()}
    return obj


def _validate_typo(idiom: str, q: Dict) -> List[str]:
    errs = []
    answer, options, question = q.get("answer"), q.get("options"), q.get("question", "")
    if not isinstance(answer, str) or len(answer) != 1:
        return ["typo：answer 必須是單一個字"]
    if answer not in idiom:
        errs.append(f"typo：正確字「{answer}」不在成語中")
    if question.count("_") != 1:
        errs.append("typo：題目必須恰有一個「_」")
    elif question.replace("_", answer, 1) != idiom:
        errs.append("typo：題目的「_」補回正確字後必須等於成語")
    if not isinstance(options, list) or len(options) != 3:
        errs.append("typo：錯字選項必須剛好 3 個")
    else:
        if len(set(options)) != 3:
            errs.append("typo：錯字選項不可重複")
        for o in options:
            if not isinstance(o, str) or len(o) != 1:
                errs.append(f"typo：錯字「{o}」必須是單一個字")
            elif o in idiom:
                errs.append(f"typo：錯字「{o}」不能是成語中的任何字")
    return errs


def _validate_compose(idiom: str, q: Dict) -> List[str]:
    errs = []
    if q.get("answer") != idiom:
        errs.append("compose：answer 必須等於成語")
    options = q.get("options")
    if not isinstance(options, list) or not all(isinstance(o, str) and len(o) == 1 for o in options):
        return errs + ["compose：options 必須是單字清單"]
    missing = Counter(idiom) - Counter(options)   # 以字數比對，支援重複字
    if missing:
        errs.append("compose：選項缺少成語用字：" + "、".join(missing.elements()))
    return errs


def _validate_application(idiom: str, q: Dict) -> List[str]:
    errs = []
    answer, options = q.get("answer"), q.get("options")
    if "____" not in (q.get("question") or ""):
        errs.append("application：題目必須含有 ____")
    if answer != idiom:
        errs.append("application：answer 必須等於成語")
    if not isinstance(options, list) or len(options) != 4:
        errs.append("application：選項必須剛好 4 個")
    else:
        if len(set(options)) != 4:
            errs.append("application：選項不可重複")
        if answer not in options:
            errs.append("application：answer 必須在選項中")
    return errs


_CHECKS = {
    "typo": _validate_typo,
    "compose": _validate_compose,
    "application": _validate_application,
}


def validate_questions(idiom: str, questions: Dict) -> List[str]:
    """驗證三種題型；缺少任一題型也算錯誤。"""
    errs = []
    for name, check in _CHECKS.items():
        q = (questions or {}).get(name)
        if not isinstance(q, dict):
            errs.append(f"{name}：缺少此題型")
        else:
            errs.extend(check(idiom, q))
    return errs
