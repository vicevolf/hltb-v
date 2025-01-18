from flask import Flask, jsonify, request
from howlongtobeatpy import HowLongToBeat
import os
from functools import wraps
import re
from typing import Dict

app = Flask(__name__)

API_KEY = os.environ['API_KEY']
ALLOWED_DOMAINS = os.environ.get('ALLOWED_DOMAINS', '*').split(',')
SIMILARITY_THRESHOLD = 0.7

# 简化的缓存，只存储响应数据
cache: Dict[str, dict] = {}

def clean_game_name(name: str) -> str:
    """清理并验证游戏名称"""
    if not isinstance(name, str) or not name:
        return ""
    
    cleaned = re.sub(r'[^a-zA-Z0-9\s\-\':]', ' ', name)
    cleaned = ' '.join(cleaned.split())
    
    return cleaned if 2 <= len(cleaned) <= 100 else ""

def build_response(game_name: str, similarity: float, times: dict, is_cache: bool = False) -> dict:
    """构建统一的响应格式"""
    return {
        "game_name": game_name,
        "similarity": round(similarity, 2),
        "times": times,
        "cache": {
            "source": "cache" if is_cache else "api"
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

    # 简单的缓存检查
    if game_name in cache:
        return jsonify(build_response(
            cache[game_name]["game_name"],
            cache[game_name]["similarity"],
            cache[game_name]["times"],
            is_cache=True
        ))

    try:
        results = HowLongToBeat().search(game_name)
        if not results:
            return jsonify({"error": "Game not found"}), 404
        
        best_match = max(results, key=lambda x: x.similarity)
        
        if best_match.similarity < SIMILARITY_THRESHOLD:
            return jsonify({"error": "No close match found"}), 404
            
        response_data = {
            "game_name": best_match.game_name,
            "similarity": best_match.similarity,
            "times": {
                "main_story": best_match.main_story,
                "main_extra": best_match.main_extra,
                "completionist": best_match.completionist
            }
        }
        
        # 存储到缓存
        cache[game_name] = response_data
        
        return jsonify(build_response(
            response_data["game_name"],
            response_data["similarity"],
            response_data["times"]
        ))

    except Exception:
        return jsonify({"error": "Server error"}), 500

app.debug = False