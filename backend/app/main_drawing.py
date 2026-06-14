"""
语音绘图工具 - FastAPI 入口
纯语音控制绘图工具 + LLM Agent 增强
"""

import os
import asyncio
from pathlib import Path

from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv(Path(__file__).parent.parent / ".env")

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .drawing.ws_handler import DrawingWSHandler
from .modules.llm_client import LLMClientFactory

app = FastAPI(title="Voice Drawing Tool", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化 LLM 客户端（用于 Agent 智能增强）
llm_client = LLMClientFactory.create()
vision_client = LLMClientFactory.create_vision()
if llm_client:
    print(f"[DrawingAgent] LLM 已启用: {type(llm_client).__name__}")
else:
    print("[DrawingAgent] LLM 未配置，Agent 增强功能不可用")

handler = DrawingWSHandler(llm_client=llm_client, vision_client=vision_client)


@app.get("/api/drawing/health")
async def health():
    return {
        "status": "ok",
        "version": "1.0.0",
        "mode": "drawing",
        "features": [
            "flow_field", "fractal_tree", "watercolor", "mandala",
            "spirograph", "voronoi", "landscape", "particle",
        ],
    }


@app.get("/api/drawing/presets")
async def presets():
    return {
        "art_types": [
            {"id": "flow_field", "name": "流场", "desc": "Perlin noise 驱动的粒子流场"},
            {"id": "fractal_tree", "name": "分形树", "desc": "递归 L-system 自然树木"},
            {"id": "watercolor", "name": "水彩", "desc": "半透明叠层水彩晕染"},
            {"id": "mandala", "name": "曼陀罗", "desc": "径向对称万花筒图案"},
            {"id": "spirograph", "name": "螺线", "desc": "数学外旋轮线"},
            {"id": "voronoi", "name": "沃罗诺伊", "desc": "随机种子点区域划分"},
        ],
        "scene_types": [
            {"id": "sunset", "name": "日落", "desc": "夕阳西下海天一色"},
            {"id": "ocean", "name": "海洋", "desc": "碧海蓝天波浪起伏"},
            {"id": "mountain", "name": "山脉", "desc": "层峦叠嶂远山如黛"},
            {"id": "starry_sky", "name": "星空", "desc": "繁星点点月光如水"},
            {"id": "forest", "name": "森林", "desc": "郁郁葱葱绿意盎然"},
            {"id": "snow", "name": "雪景", "desc": "银装素裹冰天雪地"},
            {"id": "spring", "name": "春天", "desc": "花海盛开春意盎然"},
        ],
        "shapes": [
            "circle", "rectangle", "square", "triangle", "star",
            "heart", "ellipse", "line", "polygon",
        ],
    }


@app.websocket("/ws/draw")
async def websocket_draw(websocket: WebSocket):
    await websocket.accept()
    session = handler.create_session()

    # 设置 Agent 评估完成后的回调（通过 WebSocket 推送结果）
    async def send_callback(message: dict):
        try:
            await websocket.send_json(message)
        except Exception:
            pass

    handler._ws_send_callback = send_callback

    # 发送初始状态
    await websocket.send_json({
        "type": "canvas_state",
        "data": session.engine.get_state(),
    })

    try:
        while True:
            data = await websocket.receive_json()
            # 流式处理：分批发送绘图指令
            async for batch in handler.process_message_stream(session, data):
                await websocket.send_json(batch)
    except WebSocketDisconnect:
        handler.remove_session(session.session_id)
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "data": {"message": str(e)},
        })
        handler.remove_session(session.session_id)


# 静态文件服务
frontend_dist = Path(__file__).parent.parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = frontend_dist / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(frontend_dist / "index.html"))
