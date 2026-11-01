"""
create_admin.py  ── 用 CLI 建立「第一個」admin 帳號（其餘帳號之後在網頁上建立）

用法（在專案根目錄）：
  python -m scripts.create_admin

已經有 admin 時會拒絕執行（加 --force 才能再建一個）。密碼用輸入的，不會出現在
命令列或 shell 歷史。
"""

import argparse
import getpass
import os
import re
import sys
from urllib.parse import urlparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

MIN_PASSWORD = 10
MAX_PASSWORD_BYTES = 72          # bcrypt 上限


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="已有 admin 時仍建立")
    args = ap.parse_args()

    url = os.environ.get("SUPABASE_URL", "").strip()
    if not url:
        sys.exit("未設定 SUPABASE_URL（請檢查 .env）")
    print(f"目標資料庫：{urlparse(url).hostname}")

    from flask_bcrypt import generate_password_hash
    from idiom import db

    if db.count_admins() > 0 and not args.force:
        sys.exit("已經有 admin 帳號了。其餘帳號請在網頁上建立（或加 --force）。")

    email = input("Email：").strip().lower()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        sys.exit("Email 格式不正確")
    if db.get_teacher_by_email(email):
        sys.exit("這個 Email 已經存在")
    name = input("姓名：").strip()
    if not name:
        sys.exit("請輸入姓名")

    pw = getpass.getpass(f"密碼（至少 {MIN_PASSWORD} 字元）：")
    if len(pw) < MIN_PASSWORD:
        sys.exit(f"密碼至少 {MIN_PASSWORD} 字元")
    if len(pw.encode("utf-8")) > MAX_PASSWORD_BYTES:
        sys.exit(f"密碼不可超過 {MAX_PASSWORD_BYTES} bytes")
    if getpass.getpass("再輸入一次密碼：") != pw:
        sys.exit("兩次密碼不一致")

    row = db.create_teacher(email, generate_password_hash(pw).decode(), name, role="admin")
    print(f"已建立 admin：{row['email']}（id={row['id']}）")


if __name__ == "__main__":
    main()
