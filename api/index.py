from flask import Flask, jsonify, request
from howlongtobeatpy import HowLongToBeat
import os
from functools import wraps

app = Flask(__name__)

# 从环境变量获取配置
API_KEY = os.environ.get('API_KEY', 'your-default-key-here')
ALLOWED_DOMAINS = os.environ.get('ALLOWED_DOMAINS', '*').split(',')

def require_apikey(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 检查API密钥
        provided_key = request.args.get('key')
        if not provided_key or provided_key != API_KEY:
            return jsonify({"status": "error", "message": "Unauthorized"}), 401
        
        # 检查来源域名 (如果不是'*')
        if ALLOWED_DOMAINS != ['*']:
            origin = request.headers.get('Origin', '')
            if not any(domain in origin for domain in ALLOWED_DOMAINS):
                return jsonify({"status": "error", "message": "Unauthorized"}), 401
                
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
@require_apikey
def home():
    """API首页"""
    return jsonify({
        "status": "ok",
        "message": "Welcome to HLTB API",
        "usage": {
            "search": "/api/search?key=YOUR_API_KEY&game=游戏名称",
            "example": "/api/search?key=YOUR_API_KEY&game=Elden Ring"
        }
    })

@app.route('/api/search')
@require_apikey
def search():
    """搜索游戏"""
    # 原有的搜索逻辑保持不变
    game_name = request.args.get('game')
    
    if not game_name:
        return jsonify({
            "status": "error",
            "message": "Missing game parameter"
        }), 400

    try:
        results = HowLongToBeat().search(game_name)
        
        if results is None or len(results) == 0:
            return jsonify({
                "status": "error",
                "message": "Game not found"
            }), 404
        
        best_match = max(results, key=lambda element: element.similarity)
        
        return jsonify({
            "status": "success",
            "result": {
                "game_name": best_match.game_name,
                "similarity": round(best_match.similarity, 2),
                "times": {
                    "main_story": best_match.main_story,
                    "main_extra": best_match.main_extra,
                    "completionist": best_match.completionist
                }
            }
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": "Internal server error"
        }), 500

if __name__ == '__main__':
    app.run(debug=True)