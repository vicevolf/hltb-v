from flask import Flask, jsonify, request
from howlongtobeatpy import HowLongToBeat
import os
from functools import wraps
import re
import time
from typing import Optional

app = Flask(__name__)

API_KEY = os.environ['API_KEY']
SIMILARITY_THRESHOLD = 0.6

# 重试配置
MAX_RETRIES = 3  # 最大重试次数
RETRY_DELAY = 1  # 固定重试延迟（秒）

def remove_brackets(name: str) -> str:
    """移除括号及括号内的内容（包括圆括号、方括号、花括号）"""
    # 移除圆括号及内容
    name = re.sub(r'\([^)]*\)', '', name)
    # 移除方括号及内容
    name = re.sub(r'\[[^\]]*\]', '', name)
    # 移除花括号及内容
    name = re.sub(r'\{[^}]*\}', '', name)
    # 清理多余空格
    return ' '.join(name.split()).strip()

def normalize_game_name(name: str) -> str:
    """清理特殊符号并转换为首字母大写格式"""
    # 移除特殊符号，只保留字母、数字和空格
    cleaned = re.sub(r'[^a-zA-Z0-9\s]', ' ', name)
    # 转换为首字母大写（每个单词首字母大写）
    return cleaned.title().strip()

def remove_subtitle(name: str) -> Optional[str]:
    """移除副标题（通过冒号、长横线等分隔符识别）
    返回主标题，如果没有副标题则返回 None"""
    # 定义副标题分隔符（按优先级）
    separators = ['—', '–', ':', ' - ']
    
    for sep in separators:
        if sep in name:
            main_title = name.split(sep)[0].strip()
            # 确保主标题不为空
            if main_title:
                return main_title
    
    # 没有找到副标题分隔符
    return None

def clean_game_name(name: str) -> str:
    """清理并验证游戏名称"""
    if not isinstance(name, str) or not name:
        return ""
    
    # 移除多余空格
    cleaned = ' '.join(name.split()).strip()
    
    return cleaned if 2 <= len(cleaned) <= 200 else ""

def build_response(matched_name: str, similarity: float, main_story: Optional[float], 
                   main_extra: Optional[float], completionist: Optional[float], 
                   all_styles: Optional[float]) -> dict:
    """构建统一的响应格式（匹配新的JSON结构）"""
    return {
        "matched_name": matched_name,
        "similarity": round(similarity, 2),
        "main_story": main_story,
        "main_extra": main_extra,
        "completionist": completionist,
        "all_styles": all_styles
    }

def search_hltb_with_retry(game_name: str, attempt: int = 1) -> Optional[list]:
    """带智能重试的HLTB搜索（固定延迟策略）
    
    参数:
        game_name: 要搜索的游戏名称
        attempt: 当前尝试次数（从1开始）
    
    返回:
        results: HLTB搜索结果列表，失败返回None
    """
    try:
        results = HowLongToBeat().search(game_name)
        if results:  # 成功找到结果
            return results
        # 未找到结果也视为成功（返回空列表）
        return []
    except Exception as e:
        if attempt < MAX_RETRIES:
            print(f"⚠️ HLTB搜索失败 (尝试{attempt}/{MAX_RETRIES}): {type(e).__name__} - 等待{RETRY_DELAY}秒后重试...")
            time.sleep(RETRY_DELAY)
            return search_hltb_with_retry(game_name, attempt + 1)
        else:
            print(f"❌ HLTB搜索最终失败: {type(e).__name__} - {str(e)}")
            return None

def require_apikey(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.args.get('key') != API_KEY:
            return jsonify({"error": "Unauthorized"}), 401
                
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
@require_apikey
def home():
    return jsonify({
        "message": "HLTB unofficial API - 游戏时长查询服务",
        "example": "/api/search?key=YOUR_API_KEY&game=Elden Ring",
        "response_format": {
            "matched_name": "匹配到的游戏名称",
            "similarity": "相似度（0-1）",
            "main_story": "主线时长（小时）",
            "main_extra": "主线+支线时长（小时）",
            "completionist": "完美主义时长（小时）",
            "all_styles": "全风格平均时长（小时）"
        }
    })

@app.route('/api/search')
@require_apikey
def search():
    game_name = clean_game_name(request.args.get('game', ''))
    if not game_name:
        return jsonify({"error": "Invalid game name"}), 400

    try:
        # 保存原始名称（用于副标题搜索时的相似度匹配）
        original_name = game_name
        
        # 预处理：移除括号及括号内容
        cleaned_name = remove_brackets(game_name)
        if cleaned_name != game_name:
            game_name = cleaned_name
        
        results = None
        search_name = game_name
        is_subtitle_search = False
        
        # 记录已尝试的搜索策略，避免重试时重复无效查询
        tried_strategies = set()
        
        # 步骤1: 按原样搜索（带重试）
        if 'original' not in tried_strategies:
            results = search_hltb_with_retry(game_name)
            tried_strategies.add('original')
            if results is None:  # API错误
                return jsonify({
                    "error": "HLTB service unavailable",
                    "detail": "网络不稳定，请稍后重试"
                }), 503
        
        # 步骤2: 如果无结果，使用标准化名称搜索（带重试）
        if not results and 'normalized' not in tried_strategies:
            normalized_name = normalize_game_name(game_name)
            results = search_hltb_with_retry(normalized_name)
            tried_strategies.add('normalized')
            search_name = normalized_name
            if results is None:  # API错误
                return jsonify({
                    "error": "HLTB service unavailable",
                    "detail": "网络不稳定，请稍后重试"
                }), 503
        
        # 步骤3: 如果仍无结果，尝试移除副标题（带重试）
        if not results and 'subtitle' not in tried_strategies:
            main_title = remove_subtitle(game_name)
            if main_title:
                results = search_hltb_with_retry(main_title)
                tried_strategies.add('subtitle')
                search_name = main_title
                is_subtitle_search = True
                if results is None:  # API错误
                    return jsonify({
                        "error": "HLTB service unavailable",
                        "detail": "网络不稳定，请稍后重试"
                    }), 503
            else:
                tried_strategies.add('subtitle')
        
        # 检查是否找到结果
        if not results:
            return jsonify({"error": "Game not found"}), 404
        
        # 优先筛选game类型的结果
        game_type_results = [r for r in results if r.game_type and r.game_type.lower() == 'game']
        if game_type_results:
            results = game_type_results
        
        # 选择最佳匹配
        if is_subtitle_search:
            # 副标题搜索模式：按原名称计算相似度
            from difflib import SequenceMatcher
            
            def calc_similarity(result_name: str, target_name: str) -> float:
                return SequenceMatcher(None, result_name.lower(), target_name.lower()).ratio()
            
            results_with_sim = [(r, calc_similarity(r.game_name, original_name)) for r in results]
            best_match, best_sim = max(results_with_sim, key=lambda x: x[1])
            final_similarity = best_sim
        else:
            # 使用 HLTB API 自带的相似度排序
            best_match = max(results, key=lambda x: x.similarity)
            final_similarity = best_match.similarity
        
        # 检查相似度阈值
        if final_similarity < SIMILARITY_THRESHOLD:
            return jsonify({"error": "No close match found"}), 404
        
        # 构建并返回响应数据
        return jsonify(build_response(
            best_match.game_name,
            final_similarity,
            best_match.main_story or None,
            best_match.main_extra or None,
            best_match.completionist or None,
            best_match.all_styles or None
        ))

    except Exception as e:
        return jsonify({"error": "Server error", "detail": str(e)}), 500

app.debug = False
