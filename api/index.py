from flask import Flask, jsonify, request
from howlongtobeatpy import HowLongToBeat
import os
from functools import wraps
import re
from time import time
from typing import Dict, Tuple

app = Flask(__name__)

API_KEY = os.environ['API_KEY']  # 如果环境变量未设置将直接抛出错误
ALLOWED_DOMAINS = os.environ.get('ALLOWED_DOMAINS', '*').split(',')

# 缓存配置
CACHE_TIMEOUT = 24 * 60 * 60  # 24小时的秒数
cache: Dict[str, Tuple[float, dict]] = {}  # {game_name: (timestamp, data)}

def clean_cache() -> None:
    """清理过期的缓存项"""
    current_time = time()
    expired_keys = [
        k for k, v in cache.items() 
        if current_time - v[0] > CACHE_TIMEOUT
    ]
    for k in expired_keys:
        del cache[k]

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
        "message": "HLTB unofficial API",
        "example": "/api/search?key=YOUR_API_KEY&game=Elden Ring"
    })

@app.route('/api/search')
@require_apikey
def search():
    # 清理和验证游戏名称
    game_name = clean_game_name(request.args.get('game', ''))
    if not game_name:
        return jsonify({"error": "Invalid game name"}), 400

    # 清理过期缓存
    clean_cache()

    # 检查缓存
    cache_entry = cache.get(game_name)
    if cache_entry:
        timestamp, data = cache_entry
        if time() - timestamp <= CACHE_TIMEOUT:
            # 添加缓存信息
            data.update({
                "source": "cache",
                "message": "Data retrieved from cache",
                "cache_expires_in": int(CACHE_TIMEOUT - (time() - timestamp))
            })
            return jsonify(data)

    try:
        results = HowLongToBeat().search(game_name)
        
        if not results:
            return jsonify({"error": "Game not found"}), 404
        
        best_match = max(results, key=lambda x: x.similarity)
        
        response_data = {
            "game_name": best_match.game_name,
            "similarity": round(best_match.similarity, 2),
            "times": {
                "main_story": best_match.main_story,
                "main_extra": best_match.main_extra,
                "completionist": best_match.completionist
            },
            "source": "api",
            "message": "Data freshly fetched from HLTB",
            "cache_expires_in": CACHE_TIMEOUT
        }

        # 存储到缓存
        cache[game_name] = (time(), response_data)

        return jsonify(response_data)

    except Exception:
        return jsonify({"error": "Server error"}), 500

# Vercel部署时使用
app.debug = False