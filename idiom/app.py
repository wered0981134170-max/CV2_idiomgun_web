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

_debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    # 正式環境一律 Secure；本機 http 開發預設關閉（FLASK_DEBUG=true），
    # 也可用 SESSION_COOKIE_SECURE=true/false 明確指定
    SESSION_COOKIE_SECURE=os.environ.get(
        "SESSION_COOKIE_SECURE", "false" if _debug else "true").lower() == "true",
)

if os.environ.get("RENDER"):
    # Render 在反向代理後面：信任一層 X-Forwarded-*，request.remote_addr 才是真實 IP
    from werkzeug.middleware.proxy_fix import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)

from .extensions import login_manager, bcrypt
login_manager.init_app(app)
bcrypt.init_app(app)

from .routes import main_bp
from .auth   import auth_bp
from .teacher import teacher_bp
app.register_blueprint(main_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(teacher_bp)

init_db()

if __name__ == "__main__":
    port  = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug, threaded=True)


# python -m idiom.app
