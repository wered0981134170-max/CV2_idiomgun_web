"""
app.py  ── Flask 主程式入口
"""

import os

# 只在本機開發時載入 .env；Render 會自動設定 RENDER 環境變數，不載入
if not os.environ.get("RENDER"):
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

from flask import Flask
from .db import init_db

template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
static_dir   = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static'))
app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)

_secret_key = os.environ.get('SECRET_KEY', '').strip()
if not _secret_key:
    raise RuntimeError("未設定環境變數 SECRET_KEY（本機請先 set / export 後再啟動）")
app.config['SECRET_KEY'] = _secret_key

from .routes import main_bp
from .auth   import auth_bp
app.register_blueprint(main_bp)
app.register_blueprint(auth_bp)

init_db()

if __name__ == "__main__":
    port  = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug, threaded=True)


# python -m idiom.app
