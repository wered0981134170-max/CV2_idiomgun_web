"""
extensions.py  ── Flask 擴充套件單例
在 app.py 以 init_app() 初始化，避免循環 import。
"""

from flask_login import LoginManager
from flask_bcrypt import Bcrypt

login_manager = LoginManager()
bcrypt = Bcrypt()
