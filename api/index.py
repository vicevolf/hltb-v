from flask import Flask, jsonify, request
from howlongtobeatpy import HowLongToBeat
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
from flask_caching import Cache
import os
from functools import wraps
import re

# 基础配置
app = Flask(__name__)

API_KEY = os.environ['API_KEY']
ALLOWED_DOMAINS = os.environ.get('ALLOWED_DOMAINS', '*').split(',')
SIMILARITY_THRESHOLD = float(os.environ.get('SIMILARITY_THRESHOLD', '0.7'))

# 初始化扩展
limiter = Limiter(app, key_func=get_remote_address)
cors = CORS(app, resources={r"/api/*": {"origins": ALLOWED_DOMAINS if ALLOWED_DOMAINS != ['*'] else "*"}})
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

def error_response(status_code=400):
    """统一错误响应，只返回状态码对应的标准信息"""
    messages = {
        400: "Bad Request",
        401: "Unauthorized",
        404: "Not Found",
        429: "Too Many Requests",
        500: "Internal Server Error"
    }
    return jsonify({"status": "error", "message": messages.get(status_code, "Error")}), status_code

def clean_game_name(name: str) -> str:
    """清理并验证游戏名称"""
    if not isinstance(name, str) or not name:
        return ""
    
    cleaned = re.sub(r'[^a-zA-Z0-9\s\-\':]', ' ', name)
    cleaned = ' '.join(cleaned.split())
    
    return cleaned if 2 <= len(cleaned) <= 100 else ""

def require_apikey(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.args.get('key') != API_KEY:
            return error_response(401)
        
        if ALLOWED_DOMAINS != ['*']:
            origin = request.headers.get('Origin', '')
            if not any(domain in origin for domain in ALLOWED_DOMAINS):
                return error_response(401)
                
        return f(*args, **kwargs)
    return decorated_function

@cache.memoize(timeout=3600)
def fetch_game_data(game_name: str):
    """获取游戏数据并缓存结果"""
    try:
        results = HowLongToBeat().search(game_name)
        if not results:
            return None
        
        best_match = max(results, key=lambda x: x.similarity)
        
        if best_match.similarity < SIMILARITY_THRESHOLD:
            return None
            
        return {
            "game_name": best_match.game_name,
            "similarity": round(best_match.similarity, 2),
            "times": {
                "main_story": best_match.main_story,
                "main_extra": best_match.main_extra,
                "completionist": best_match.completionist
            }
        }
    except Exception:
        return None

@app.route('/')
@require_apikey
@limiter.limit("20/minute")
def home():
    return jsonify({
        "status": "ok",
        "message": "HLTB API"
    })

@app.route('/api/search')
@require_apikey
@limiter.limit("30/minute")
def search():
    game_name = clean_game_name(request.args.get('game', ''))
    if not game_name:
        return error_response(400)

    result = fetch_game_data(game_name)
    if result is None:
        return error_response(404)
    
    return jsonify({"status": "ok", "data": result})

@app.errorhandler(Exception)
def handle_error(error):
    """统一错误处理"""
    if isinstance(error, Limiter.RateLimitExceeded):
        return error_response(429)
    
    return error_response(500)

app.debug = False

if __name__ == '__main__':
    app.run()