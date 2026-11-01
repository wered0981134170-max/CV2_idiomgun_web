"""
import_idioms.py  ── 一次性：把 data/*.json 匯入 Supabase 的 idioms 表

用法（在專案根目錄）：
  python -m scripts.import_idioms --dry-run        # 只驗證、列報告，不連線寫入
  python -m scripts.import_idioms                  # 匯入（已存在的成語會跳過）
  python -m scripts.import_idioms --overwrite      # 已存在的成語也覆蓋（會蓋掉教師的編輯！）
  python -m scripts.import_idioms --yes            # 不詢問確認

年級以 question_type.FILES 的檔案對應為準，不讀 JSON 內的 grade 欄位。
不符合驗證規則的成語仍會匯入，只在報告中列出。
匯入的資料一律是 status=published，--source 預設 teacher。
"""

import argparse
import json
import os
import sys
from urllib.parse import urlparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from idiom.question_type import DATA_DIR, FILES          # noqa: E402
from idiom.validators import strip_strings, validate_questions  # noqa: E402


def build_rows(source: str):
    rows, report = [], []
    for grade, filename in FILES.items():
        path = DATA_DIR / filename
        if not path.exists():
            print(f"[略過] 找不到 {path}")
            continue
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        for item in raw:
            item = strip_strings(item)
            idiom = item["idiom"]
            questions = item.get("questions", {})
            for msg in validate_questions(idiom, questions):
                report.append((grade, idiom, msg))
            rows.append({
                "school_id": None,                    # 共用題庫
                "grade": grade,                       # 以檔案對應為準
                "idiom": idiom,
                "meaning": item.get("meaning", ""),
                "explanation": item.get("explanation", ""),
                "questions": questions,
                "status": "published",
                "source": source,
            })
    return rows, report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--yes", action="store_true")
    ap.add_argument("--source", default="teacher", choices=["moe", "ai", "teacher"])
    args = ap.parse_args()

    rows, report = build_rows(args.source)
    print(f"讀到 {len(rows)} 個成語")
    seen = {}
    for r in rows:
        key = (r["grade"], r["idiom"])
        if key in seen:
            print(f"[警告] 重複成語：{key}，同年級重複者只會保留最後一筆")
        seen[key] = r
    rows = list(seen.values())

    print(f"\n── 驗證報告：{len(report)} 項不符合規則（仍會匯入）──")
    for grade, idiom, msg in report:
        print(f"  [{grade}] {idiom}：{msg}")

    if args.dry_run:
        print("\n(dry-run，未寫入)")
        return

    url = os.environ.get("SUPABASE_URL", "").strip()
    if not url:
        sys.exit("未設定 SUPABASE_URL（請檢查 .env）")
    host = urlparse(url).hostname
    print(f"\n目標資料庫：{host}")
    if not args.yes and input("確認這是 dev 專案並要寫入？輸入 yes：").strip() != "yes":
        sys.exit("已取消")

    from idiom.db import _sb
    res = (
        _sb().table("idioms")
        .upsert(rows, on_conflict="school_id,grade,idiom", ignore_duplicates=not args.overwrite)
        .execute()
    )
    written = len(res.data or [])
    mode = "新增或覆蓋" if args.overwrite else "新增"
    print(f"完成：{mode} {written} 筆，跳過 {len(rows) - written} 筆（已存在）")


if __name__ == "__main__":
    main()
