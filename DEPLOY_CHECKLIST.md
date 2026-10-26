# 上線檢查清單（比賽結束後才執行）

> 開發期間所有工作只在本機 `feature/teacher` 分支，指向 Supabase **dev** 專案。
> 本清單的每一項都要等比賽結束後，才對正式環境操作。

## 0. 上線前確認
- [ ] 比賽已結束，確認可以停機/更新
- [ ] 備份正式 Supabase（至少匯出 `scores` 表）
- [ ] 在 dev 環境完整測試過所有階段

## 1. Supabase（正式專案）執行 SQL
依階段順序執行（各階段完成後補上 SQL 檔名）：
- [ ] 階段 0：無
- [ ] 階段 1：`sql/001_stage1_idioms.sql`（建 `idioms`、對 `idioms` 與 `scores` 開 RLS）
  - ⚠️ 順序：**必須先把 Render 的 `SUPABASE_KEY` 換成 service_role key，再對 `scores` 開 RLS**，否則排行榜（目前用 anon key）會全部失效
- [ ] 階段 2：`teachers` 表、RLS（SQL 待補）
- [ ] 階段 3：`scores` 表 RLS／必要欄位檢查（SQL 待補）
- [ ] 階段 3.5：`answers` 表、RLS（SQL 待補）

所有表開啟 RLS 且不設 policy（後端使用 service_role key）。

## 2. Render 環境變數
- [ ] `SECRET_KEY`：更換（舊金鑰曾進入 git 歷史，視為外洩）。上線後學生 session 會失效，需重新輸入班級座號姓名
- [ ] `SUPABASE_KEY`：改為 **service_role key**（只放後端環境變數）
- [ ] 新增（階段 5 之後）：`ANTHROPIC_API_KEY`、`ANTHROPIC_MODEL`
- [ ] 其他隨階段新增的變數（見 render.yaml，`sync: false` 者需手動填）
- [ ] 確認未設定 `RENDER` 以外的本機專用變數（如 `FLASK_DEBUG` 應為 false）

## 3. 資料匯入
- [ ] 先 `python -m scripts.import_idioms --dry-run` 看驗證報告
- [ ] 本機 `.env` 暫時指向**正式** Supabase 後執行 `python -m scripts.import_idioms`（會顯示目標主機並要求輸入 yes；已存在的成語會跳過，不會蓋掉教師編輯；**不要**用 `--overwrite`）
- [ ] 匯入完立刻把 `.env` 改回 dev 專案
- [ ] 檢查匯入報告（驗證不符合規則的成語）

## 4. 建立教師帳號
- [ ] 對正式資料庫執行 `scripts/create_teacher.py`（階段 2 完成後補上用法）

## 5. 部署
- [ ] 合併 `feature/teacher` → `master`、push、Render 部署
- [ ] 確認 requirements.txt 新套件安裝成功

## 6. 部署後測試
- [ ] 學生遊戲首頁、登入、三種難度出題正常
- [ ] 排行榜讀寫正常
- [ ] `POST /leaderboard/reset` 未登入時回 403/401
- [ ] 教師登入、成績查看（僅限負責班級）
- [ ] 成語管理、發布後遊戲可見

## 備註：容錯設計
程式在 `idioms` 表不存在、為空或 Supabase 連不上時會退回讀 `data/*.json`，因此「先部署程式、後建表／匯入」不會讓遊戲壞掉（匯入前遊戲用 JSON 題目）。
注意：`idioms` 某年級已發布成語為 0 筆時，也會退回 JSON，所以教師不可能把某年級全部下架。
