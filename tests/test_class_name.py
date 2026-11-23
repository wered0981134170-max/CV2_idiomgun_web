"""班級名稱統一成「X年YY班」。執行：python -m pytest tests -q"""

import pytest

from idiom.class_name import normalize_class_name


@pytest.mark.parametrize("raw, expected", [
    *[(r, "1年01班") for r in ("一甲", "1甲", "一年甲班", "1年甲班", "１甲")],
    *[(r, "3年02班") for r in ("三年二班", "3年2班", "3-2", "302", "三年級二班")],
    ("五年十二班", "5年12班"), ("512", "5年12班"),
    ("501", "5年01班"),
    ("國一甲", "7年01班"), ("七年甲班", "7年01班"), ("國中一年甲班", "7年01班"),
    ("國二3班", "8年03班"),
    ("1年01班", "1年01班"),
    # 額外：空白、全形、天干上限、中文數字十位
    (" 3 年　2 班 ", "3年02班"), ("３－２", "3年02班"), ("6癸", "6年10班"),
    ("四年二十一班", "4年21班"), ("九年九十九班", "9年99班"),
])
def test_normalize(raw, expected):
    assert normalize_class_name(raw) == expected


@pytest.mark.parametrize("raw", [
    "", "甲", "3", "12", "300", "1000", "三年", "0甲", "十年一班", "abc",
    None, "12班", "國四甲", "3年100班", "3年0班",
])
def test_unrecognized_returns_none(raw):
    assert normalize_class_name(raw) is None


@pytest.mark.parametrize("raw", ["一甲", "三年二班", "512", "國二3班", "1年01班", "9年99班"])
def test_idempotent(raw):
    once = normalize_class_name(raw)
    assert normalize_class_name(once) == once
