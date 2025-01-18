from flask import Flask, jsonify, request
from howlongtobeatpy import HowLongToBeat

app = Flask(__name__)

def format_game_info(game):
    """格式化游戏信息，只返回确定存在的基本属性"""
    return {
        "game_name": game.game_name,
        "similarity": round(game.similarity, 2),
        "main_story": game.main_story,
        "main_extra": game.main_extra,
        "completionist": game.completionist,
        "profile_url": game.profile_url
    }

@app.route('/')
def home():
    """API首页"""
    return jsonify({
        "status": "ok",
        "message": "Welcome to HLTB API",
        "usage": {
            "search": "/api/search?game=游戏名称",
            "example": "/api/search?game=Elden Ring"
        }
    })

@app.route('/api/search')
def search():
    """搜索游戏"""
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
            
        # 获取最佳匹配和所有匹配（限制前5个）
        all_matches = sorted(results, key=lambda x: x.similarity, reverse=True)[:5]
        
        return jsonify({
            "status": "success",
            "results": [format_game_info(game) for game in all_matches]
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True)