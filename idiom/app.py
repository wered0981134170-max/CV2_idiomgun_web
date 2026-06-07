"""
app.py  ── Flask 主程式入口
"""

import os
from flask import Flask

from db import init_db      # 初始化資料庫

# 設定模板和靜態文件的路徑
template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static'))
app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)

# 註冊路由
from routes import main_bp
app.register_blueprint(main_bp)

# 啟動時建立資料表
init_db()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    
    app.run(host="0.0.0.0", port=port, debug=debug, threaded=True)