"""
app.py  ── Flask 主程式入口
"""

import os
import secrets
from flask import Flask

from .db import init_db

template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
static_dir   = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static'))

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)

# Flask session 必須設定 secret_key
# 正式部署時請用環境變數傳入固定金鑰，避免重啟後 session 失效
app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(32))

from .routes import main_bp
app.register_blueprint(main_bp)

init_db()

if __name__ == "__main__":
    port  = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug, threaded=True)


# python -m idiom.app  