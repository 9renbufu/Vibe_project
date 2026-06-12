"""
Voice Designer - 主应用入口
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv(Path(__file__).parent.parent / ".env")

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .agent.designer_agent import DesignerAgent
from .modules.llm_client import LLMClientFactory
from .modules.image_gen import ImageGeneratorFactory
from .modules.memory import DesignMemory
from .protocol import (
    create_agent_response,
    create_image_result,
    create_state_update,
    create_error,
    create_status,
)

# 创建 FastAPI 应用
app = FastAPI(
    title="Voice Designer",
    description="AI 驱动的语音设计助手",
    version="2.0.0",
)

# CORS 中间件
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
memory = DesignMemory()


@app.get("/api/health")
async def health():
    """健康检查"""
    return {
        "status": "ok",
        "version": "2.0.0",
        "llm_available": llm_client is not None,
        "image_available": image_generator is not None,
    }


@app.get("/api/state")
async def get_state():
    """获取当前状态"""
    return {
        "memory": memory.to_dict(),
    }


@app.post("/api/reset")
async def reset():
    """重置状态"""
    memory.clear()
    return {"status": "ok"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket 端点"""
    await websocket.accept()
    print("Client connected")

    # 每个连接创建独立的 Agent 实例
    agent = DesignerAgent(
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
                await handle_voice_input(websocket, agent, message)

            elif msg_type == "text_input":
                await handle_text_input(websocket, agent, message)

            elif msg_type == "get_state":
                await send_state(websocket, agent)

            elif msg_type == "reset":
                agent.reset()
                memory.clear()
                await websocket.send_json(create_status("reset", "已重置"))

    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"Error: {e}")
        try:
            await websocket.send_json(create_error(str(e)))
        except:
            pass


async def handle_voice_input(websocket: WebSocket, agent: DesignerAgent, message: dict):
    """处理语音输入"""
    text = message.get("data", {}).get("text", "")
    if not text:
        return

    print(f"Voice input: {text}")

    # 保存到记忆
    memory.conversation.add("user", text)

    # 发送处理状态
    await websocket.send_json(create_status("processing", "正在理解您的需求..."))

    # Agent 处理
    result = await agent.process_input(text)

    # 发送 Agent 回复
    await websocket.send_json(create_agent_response(
        response=result.get("response", ""),
        action=result.get("action", "ask"),
        phase=result.get("phase", "discussion"),
        elements=result.get("elements", []),
        style=result.get("style"),
        color_palette=result.get("color_palette"),
    ))

    # 如果需要生成图像
    if result.get("action") == "generate" and result.get("image_prompt"):
        await generate_and_send_image(websocket, agent, result["image_prompt"])

    # 发送状态更新
    await send_state(websocket, agent)


async def handle_text_input(websocket: WebSocket, agent: DesignerAgent, message: dict):
    """处理文本输入"""
    text = message.get("data", {}).get("text", "")
    if not text:
        return

    print(f"Text input: {text}")

    # 保存到记忆
    memory.conversation.add("user", text)

    # Agent 处理
    result = await agent.process_input(text)

    # 发送回复
    await websocket.send_json(create_agent_response(
        response=result.get("response", ""),
        action=result.get("action", "ask"),
        phase=result.get("phase", "discussion"),
        elements=result.get("elements", []),
        style=result.get("style"),
        color_palette=result.get("color_palette"),
    ))

    # 如果需要生成图像
    if result.get("action") == "generate" and result.get("image_prompt"):
        await generate_and_send_image(websocket, agent, result["image_prompt"])

    # 发送状态更新
    await send_state(websocket, agent)


async def generate_and_send_image(websocket: WebSocket, agent: DesignerAgent, prompt: str):
    """生成并发送图像"""
    if not image_generator:
        await websocket.send_json(create_error("图像生成服务未配置"))
        return

    try:
        await websocket.send_json(create_status("generating", "正在生成设计图..."))

        # 生成图像
        image_data = await image_generator.generate(prompt)

        if image_data:
            # 保存到 Agent 上下文
            agent.context.generated_images.append(image_data)
            agent.context.current_image_prompt = prompt

            # 保存到记忆
            memory.add_design_iteration({
                "prompt": prompt,
                "image_generated": True,
            })

            # 发送图像
            await websocket.send_json(create_image_result(
                image_base64=image_data,
                prompt=prompt,
                design_context=agent.get_state(),
            ))
        else:
            await websocket.send_json(create_error("图像生成失败"))

    except Exception as e:
        print(f"Image generation error: {e}")
        await websocket.send_json(create_error(f"图像生成错误: {str(e)}"))


async def send_state(websocket: WebSocket, agent: DesignerAgent):
    """发送状态更新"""
    state = agent.get_state()
    state["memory"] = memory.to_dict()
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
