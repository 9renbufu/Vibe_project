"""
Voice Designer v3 - 使用完整 Agent 流水线
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .agent.pipeline import DesignPipeline
from .modules.llm_client import LLMClientFactory
from .modules.image_gen import ImageGeneratorFactory
from .protocol import (
    create_agent_response,
    create_image_result,
    create_state_update,
    create_error,
    create_status,
)

app = FastAPI(
    title="Voice Designer",
    description="AI 驱动的语音设计助手",
    version="3.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化组件
llm_client = LLMClientFactory.create()
image_generator = ImageGeneratorFactory.create()

print(f"LLM Available: {llm_client is not None}")
print(f"Image Generator Available: {image_generator is not None}")


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "version": "3.0.0",
        "llm_available": llm_client is not None,
        "image_available": image_generator is not None,
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("Client connected")

    # 每个连接创建独立的 Pipeline
    pipeline = DesignPipeline(
        llm_client=llm_client,
        image_generator=image_generator,
    )

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            msg_type = message.get("type", "")

            print(f"Received: {msg_type}")

            if msg_type == "voice_input":
                await handle_input(websocket, pipeline, message, is_voice=True)

            elif msg_type == "text_input":
                await handle_input(websocket, pipeline, message, is_voice=False)

            elif msg_type == "get_state":
                await send_state(websocket, pipeline)

            elif msg_type == "reset":
                pipeline.reset()
                await websocket.send_json(create_status("reset", "已重置"))

    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"Error: {e}")
        try:
            await websocket.send_json(create_error(str(e)))
        except:
            pass


async def handle_input(
    websocket: WebSocket,
    pipeline: DesignPipeline,
    message: dict,
    is_voice: bool = True,
):
    """处理输入"""
    text = message.get("data", {}).get("text", "")
    if not text:
        return

    print(f"{'Voice' if is_voice else 'Text'} input: {text}")

    # 发送处理状态
    await websocket.send_json(create_status("processing", "正在理解您的需求..."))

    # Step 1: Intent Analysis
    await websocket.send_json({
        "type": "step_update",
        "data": {
            "step": "intent",
            "status": "running",
            "name": "Requirement Analysis",
        }
    })

    # 通过 Pipeline 处理
    result = await pipeline.process_voice_input(text)

    # 发送完成的步骤状态
    await websocket.send_json({
        "type": "step_update",
        "data": {
            "step": "intent",
            "status": "completed",
            "name": "Requirement Analysis",
            "output": result.get("intent", {}).get("intent", ""),
        }
    })

    # Step 2: Planning
    await websocket.send_json({
        "type": "step_update",
        "data": {
            "step": "plan",
            "status": "completed",
            "name": "Design Planning",
            "output": result.get("plan", {}).get("name", ""),
        }
    })

    # Step 3: Prompt Generation
    await websocket.send_json({
        "type": "step_update",
        "data": {
            "step": "prompt",
            "status": "completed",
            "name": "Prompt Generation",
        }
    })

    # Step 4: Image Generation - 发送生成中状态
    await websocket.send_json(create_status("generating", "正在生成图像，请稍候..."))
    await websocket.send_json({
        "type": "step_update",
        "data": {
            "step": "generate",
            "status": "running",
            "name": "Image Generation",
        }
    })

    if result.get("image"):
        await websocket.send_json({
            "type": "step_update",
            "data": {
                "step": "generate",
                "status": "completed",
                "name": "Image Generation",
            }
        })

    # 发送 Agent 回复
    await websocket.send_json({
        "type": "agent_response",
        "data": {
            "response": result.get("response", ""),
            "action": result.get("action", "ask"),
            "phase": result.get("phase", "idle"),
            "intent": result.get("intent"),
            "plan": result.get("plan"),
        }
    })

    # 发送图像结果
    if result.get("image"):
        await websocket.send_json(create_image_result(
            image_base64=result["image"],
            prompt=pipeline.state.current_prompt,
            design_context=pipeline.get_state(),
        ))

    # 发送状态更新
    await send_state(websocket, pipeline)


async def send_state(websocket: WebSocket, pipeline: DesignPipeline):
    """发送状态更新"""
    state = pipeline.get_state()
    await websocket.send_json(create_state_update(state))


# 静态文件服务
frontend_dir = Path(__file__).parent.parent.parent / "frontend" / "dist"
if frontend_dir.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dir / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        file_path = frontend_dir / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(frontend_dir / "index.html"))
