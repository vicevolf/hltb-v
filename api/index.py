from flask import Flask, jsonify, request
from howlongtobeatpy import HowLongToBeat

app = Flask(__name__)

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
        # 搜索游戏
        results = HowLongToBeat().search(game_name)
        
        # 检查是否有结果
        if results is None or len(results) == 0:
            return jsonify({
                "status": "error",
                "message": "Game not found"
            }), 404
        
        # 获取最佳匹配
        best_match = max(results, key=lambda element: element.similarity)
        
        # 返回结果
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
            "message": str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True)