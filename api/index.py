from flask import Flask, jsonify, request
from howlongtobeatpy import HowLongToBeat
import os
from functools import wraps
import re

app = Flask(__name__)

# 配置
API_KEY = os.environ.get('API_KEY', 'your-default-key-here')
ALLOWED_DOMAINS = os.environ.get('ALLOWED_DOMAINS', '*').split(',')

def clean_game_name(name: str) -> str:
    """清理并验证游戏名称"""
    if not isinstance(name, str) or not name:
        return ""
    
    # 只保留字母、数字、空格、连字符、撇号、冒号
    cleaned = re.sub(r'[^a-zA-Z0-9\s\-\':]', ' ', name)
    # 合并多个空格为单个空格并去除首尾空格
    cleaned = ' '.join(cleaned.split())
    
    # 检查长度（2-100字符）
    if len(cleaned) < 2 or len(cleaned) > 100:
        return ""
        
    return cleaned

def require_apikey(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 验证API密钥
        if request.args.get('key') != API_KEY:
            return jsonify({"error": "Unauthorized"}), 401
        
        # 验证域名
        if ALLOWED_DOMAINS != ['*']:
            origin = request.headers.get('Origin', '')
            if not any(domain in origin for domain in ALLOWED_DOMAINS):
                return jsonify({"error": "Unauthorized"}), 401
                
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
@require_apikey
def home():
    return jsonify({
        "message": "HLTB API",
        "example": "/api/search?key=YOUR_API_KEY&game=Elden Ring"
    })

@app.route('/api/search')
@require_apikey
def search():
    # 清理和验证游戏名称
    game_name = clean_game_name(request.args.get('game', ''))
    if not game_name:
        return jsonify({"error": "Invalid game name"}), 400

    try:
        results = HowLongToBeat().search(game_name)
        
        if not results:
            return jsonify({"error": "Game not found"}), 404
        
        best_match = max(results, key=lambda x: x.similarity)
        
        return jsonify({
            "game_name": best_match.game_name,
            "similarity": round(best_match.similarity, 2),
            "times": {
                "main_story": best_match.main_story,
                "main_extra": best_match.main_extra,
                "completionist": best_match.completionist
            }
        })

    except Exception:
        return jsonify({"error": "Server error"}), 500

if __name__ == '__main__':
    app.run(
        debug=False,
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000))
    )