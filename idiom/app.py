"""
app.py  ── Flask 主程式入口
"""

import os
from flask import Flask

from .db import init_db
from .extensions import login_manager, bcrypt

template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
static_dir   = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static'))
app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-change-in-production')

login_manager.init_app(app)
bcrypt.init_app(app)

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
