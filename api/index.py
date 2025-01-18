from flask import Flask, jsonify, request
from howlongtobeatpy import HowLongToBeat
import os
from functools import wraps
import re
from time import time
from typing import Dict, Tuple, Optional

app = Flask(__name__)

API_KEY = os.environ['API_KEY']
ALLOWED_DOMAINS = os.environ.get('ALLOWED_DOMAINS', '*').split(',')
CACHE_TIMEOUT = 24 * 60 * 60  # 24小时缓存
cache: Dict[str, Tuple[float, dict]] = {}

def clean_game_name(name: str) -> str:
    """清理并验证游戏名称"""
    if not isinstance(name, str) or not name:
        return ""
    
    cleaned = re.sub(r'[^a-zA-Z0-9\s\-\':]', ' ', name)
    cleaned = ' '.join(cleaned.split())
    
    return cleaned if 2 <= len(cleaned) <= 100 else ""

def get_cache(game_name: str) -> Optional[dict]:
    """获取缓存数据"""
    # 清理过期缓存
    current_time = time()
    expired_keys = [k for k, v in cache.items() if current_time - v[0] > CACHE_TIMEOUT]
    for k in expired_keys:
        del cache[k]
    
    # 检查缓存
    if game_name in cache:
        timestamp, data = cache[game_name]
        if current_time - timestamp <= CACHE_TIMEOUT:
            return build_response(
                data["game_name"],
                data["similarity"],
                data["times"],
                is_cache=True,
                cache_age=current_time - timestamp
            )
    return None

def build_response(game_name: str, similarity: float, times: dict, is_cache: bool = False, cache_age: float = 0) -> dict:
    """构建统一的响应格式"""
    return {
        "game_name": game_name,
        "similarity": round(similarity, 2),
        "times": times,
        "cache": {
            "source": "cache" if is_cache else "api",
            "message": "Data retrieved from cache" if is_cache else "Data freshly fetched from HLTB",
            "expires_in": int(CACHE_TIMEOUT - cache_age) if is_cache else CACHE_TIMEOUT
        }
    }

def require_apikey(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.args.get('key') != API_KEY:
            return jsonify({"error": "Unauthorized"}), 401
        
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
        "message": "HLTB unofficial API",
        "example": "/api/search?key=YOUR_API_KEY&game=Elden Ring"
    })

@app.route('/api/search')
@require_apikey
def search():
    game_name = clean_game_name(request.args.get('game', ''))
    if not game_name:
        return jsonify({"error": "Invalid game name"}), 400

    # 检查缓存
    if cached_data := get_cache(game_name):
        return jsonify(cached_data)

    try:
        results = HowLongToBeat().search(game_name)
        if not results:
            return jsonify({"error": "Game not found"}), 404
        
        best_match = max(results, key=lambda x: x.similarity)
        response_data = build_response(
            best_match.game_name,
            best_match.similarity,
            {
                "main_story": best_match.main_story,
                "main_extra": best_match.main_extra,
                "completionist": best_match.completionist
            }
        )
        
        # 存储到缓存
        cache[game_name] = (time(), response_data)
        return jsonify(response_data)

    except Exception:
        return jsonify({"error": "Server error"}), 500

app.debug = False