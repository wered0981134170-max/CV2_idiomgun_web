"""
app.py  ── Flask 主程式入口
"""
import os
from flask import Flask

from db import init_db
from camera import CV2_OK, MEDIAPIPE_OK

app = Flask(__name__)

# 註冊路由
from routes import main_bp
app.register_blueprint(main_bp)

# 啟動時建立資料表
init_db()

print(f"[INFO] CV2_OK = {CV2_OK}, MEDIAPIPE_OK = {MEDIAPIPE_OK}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    
    app.run(host="0.0.0.0", port=port, debug=debug, threaded=True)