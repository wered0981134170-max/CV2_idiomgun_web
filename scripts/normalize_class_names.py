"""
normalize_class_names.py  ── 把 scores 裡的舊班級文字統一成「X年YY班」

為什麼要跑：get_best_by_student 用「完全相同的班級文字」比對，舊資料（例如「一甲」）
不轉換的話，學生用新格式（「1年01班」）登入後會查不到自己以前的最高分。

用法（在專案根目錄）：
  python -m scripts.normalize_class_names            # 只預覽，不寫入
  python -m scripts.normalize_class_names --apply    # 實際更新（會要求輸入 yes）

無法辨識的班級文字不更新、也不刪除，只列出來讓老師自行判斷。
"""

import argparse
import os
import sys
from collections import Counter
from urllib.parse import urlparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def plan(rows):
    """回傳 (要轉換的 {舊文字: (新文字, 筆數)}, 無法辨識的 {原文字: 筆數}, 班級空白筆數)。"""
    from idiom.class_name import normalize_class_name

    counts = Counter(r.get("class_name") for r in rows)
    changes, unknown, blank = {}, {}, 0
    for raw, n in counts.items():
        if raw is None or not str(raw).strip():
            blank += n
            continue
        new = normalize_class_name(raw)
        if new is None:
            unknown[raw] = n
        elif new != raw:
            changes[raw] = (new, n)
    return changes, unknown, blank


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="實際寫入資料庫（預設只預覽）")
    args = ap.parse_args()

    url = os.environ.get("SUPABASE_URL", "").strip()
    if not url:
        sys.exit("未設定 SUPABASE_URL（請檢查 .env）")
    print(f"目標資料庫：{urlparse(url).hostname}")

    from idiom import db

    rows = db.get_all_scores()
    changes, unknown, blank = plan(rows)
    print(f"共 {len(rows)} 筆成績紀錄\n")

    if changes:
        print("將轉換：")
        for raw, (new, n) in sorted(changes.items(), key=lambda x: x[1]):
            print(f"  {raw!r} → {new}　（{n} 筆）")
    else:
        print("沒有需要轉換的班級文字。")

    if unknown:
        print("\n無法辨識（不會更新）：")
        for raw, n in sorted(unknown.items()):
            print(f"  {raw!r}　（{n} 筆）")
    if blank:
        print(f"\n班級空白（未確認身分就遊玩）：{blank} 筆，不會更新")

    if not args.apply:
        print("\n這是預覽，沒有寫入任何資料。確認無誤後加上 --apply 執行。")
        return
    if not changes:
        return
    total = sum(n for _, n in changes.values())
    if input(f"\n確定要更新 {total} 筆紀錄？輸入 yes：").strip() != "yes":
        sys.exit("已取消")

    for raw, (new, n) in changes.items():
        db.rename_class_name(raw, new)
        print(f"  已更新 {raw!r} → {new}（{n} 筆）")
    print("完成。")


if __name__ == "__main__":
    main()
