from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from howlongtobeatpy import HowLongToBeat
from typing import Optional, List
from pydantic import BaseModel

app = FastAPI()

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class GameTime(BaseModel):
    game_name: str
    similarity: float
    main_story: float
    main_extra: float
    completionist: float
    image_url: Optional[str]

@app.get("/")
async def read_root():
    return {"message": "Welcome to HowLongToBeat API"}

@app.get("/search/{game_name}", response_model=List[GameTime])
async def search_game(game_name: str):
    try:
        results = await HowLongToBeat().async_search(game_name)
        
        if results is None or len(results) == 0:
            raise HTTPException(status_code=404, detail="Game not found")
        
        # 转换结果为我们定义的模型
        game_times = []
        for game in results:
            game_times.append(
                GameTime(
                    game_name=game.game_name,
                    similarity=game.similarity,
                    main_story=game.main_story,
                    main_extra=game.main_extra,
                    completionist=game.completionist,
                    image_url=game.image_url if hasattr(game, 'image_url') else None
                )
            )
        
        # 按相似度排序
        game_times.sort(key=lambda x: x.similarity, reverse=True)
        
        return game_times[:5]  # 只返回相似度最高的5个结果
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 用于Vercel的处理
from mangum import Mangum
handler = Mangum(app)