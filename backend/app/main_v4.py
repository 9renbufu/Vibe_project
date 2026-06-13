"""
Voice Designer v4 - 完整 Agent 系统
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

from .agents import AgentOrchestrator, DesignStage
from .modules.llm_client import LLMClientFactory
from .modules.image_gen import ImageGeneratorFactory

app = FastAPI(
    title="Voice Designer Agent",
    description="AI 驱动的智能设计助手 - Agent 系统",
    version="4.0.0",
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
shared_memory_agent = None  # 延迟初始化，与 WebSocket 会话共享

print(f"LLM Available: {llm_client is not None}")
print(f"Image Generator Available: {image_generator is not None}")


def _get_memory_agent():
    """获取共享的记忆 Agent 单例"""
    global shared_memory_agent
    if shared_memory_agent is None:
        from .agents.memory import DesignMemoryAgent
        shared_memory_agent = DesignMemoryAgent(llm_client)
    return shared_memory_agent


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "version": "4.0.0",
        "llm_available": llm_client is not None,
        "image_available": image_generator is not None,
    }


@app.get("/api/memory/preferences")
async def get_preferences():
    """获取用户设计偏好"""
    memory_agent = _get_memory_agent()
    result = await memory_agent.execute(None, action="query", query_type="preferences")
    return result.data


@app.get("/api/memory/history")
async def get_history(limit: int = 50):
    """获取设计历史"""
    memory_agent = _get_memory_agent()
    result = await memory_agent.execute(None, action="query", query_type="history")
    history = result.data.get("history", [])
    return {"history": history[-limit:]}


@app.get("/api/memory/stats")
async def get_stats():
    """获取记忆统计"""
    memory_agent = _get_memory_agent()
    result = await memory_agent.execute(None, action="analyze")
    return result.data


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("Client connected")

    # 每个连接创建独立的 Orchestrator，共享记忆模块
    memory_agent = _get_memory_agent()
    orchestrator = AgentOrchestrator(
        llm_client=llm_client,
        image_generator=image_generator,
    )
    orchestrator.memory_agent = memory_agent

    # 设置回调函数
    async def on_stage_change(stage: str, data: dict):
        """阶段变化回调"""
        await websocket.send_json({
            "type": "stage_update",
            "data": {
                "stage": stage,
                "detail": data,
            }
        })

    async def on_agent_result(agent_name: str, result):
        """Agent 执行结果回调"""
        await websocket.send_json({
            "type": "agent_update",
            "data": {
                "agent": agent_name,
                "success": result.success,
                "message": result.message,
                "data": result.data,
            }
        })

    async def on_thinking(agent_name: str, thinking: str):
        """思考过程回调"""
        await websocket.send_json({
            "type": "thinking",
            "data": {
                "agent": agent_name,
                "content": thinking,
            }
        })

    orchestrator.set_callbacks(
        on_stage_change=on_stage_change,
        on_agent_result=on_agent_result,
        on_thinking=on_thinking,
    )

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            msg_type = message.get("type", "")

            print(f"Received: {msg_type}")

            if msg_type in ("voice_input", "text_input"):
                await handle_input(websocket, orchestrator, message)

            elif msg_type == "select_plan":
                plan_id = message.get("data", {}).get("plan_id", "")
                if plan_id:
                    orchestrator.state.select_plan(plan_id)
                    await websocket.send_json({
                        "type": "plan_selected",
                        "data": {"plan_id": plan_id}
                    })

            elif msg_type == "get_state":
                await send_state(websocket, orchestrator)

            elif msg_type == "reset":
                orchestrator.reset()
                await websocket.send_json({
                    "type": "status",
                    "data": {"status": "reset", "message": "已重置"}
                })

    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"Error: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "data": {"message": str(e)}
            })
        except:
            pass


async def handle_input(
    websocket: WebSocket,
    orchestrator: AgentOrchestrator,
    message: dict,
):
    """处理输入"""
    text = message.get("data", {}).get("text", "")
    if not text:
        return

    print(f"Input: {text}")

    # 发送处理状态
    await websocket.send_json({
        "type": "status",
        "data": {"status": "processing", "message": "正在处理..."}
    })

    # 通过 Orchestrator 处理
    result = await orchestrator.process_input(text)

    # 发送 Agent 回复
    await websocket.send_json({
        "type": "agent_response",
        "data": {
            "response": result.get("response", ""),
            "stage": result.get("stage", ""),
            "data": result.get("data", {}),
        }
    })

    # 发送图像结果
    image_data = result.get("data", {}).get("image")
    if image_data:
        await websocket.send_json({
            "type": "image_result",
            "data": {
                "image": image_data,
                "prompt": result.get("data", {}).get("prompt", ""),
                "version": result.get("data", {}).get("version", 1),
            }
        })

    # 发送评估结果
    evaluation = result.get("data", {}).get("evaluation")
    if evaluation:
        await websocket.send_json({
            "type": "evaluation_result",
            "data": evaluation
        })

    # 发送设计方案
    plans = result.get("data", {}).get("plans")
    if plans:
        await websocket.send_json({
            "type": "plans_result",
            "data": {"plans": plans}
        })

    # 发送最终状态
    await send_state(websocket, orchestrator)


async def send_state(websocket: WebSocket, orchestrator: AgentOrchestrator):
    """发送状态更新"""
    state = orchestrator.get_state()
    await websocket.send_json({
        "type": "state_update",
        "data": state
    })


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
