import os
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .scene_manager import SceneManager
from .llm_handler import LLMHandler
from .voice_processor import VoiceProcessor
from .models import WebSocketMessage, VoiceCommand

app = FastAPI(title="VoiceSketch AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

scene_manager = SceneManager()
llm_handler = LLMHandler()
voice_processor = VoiceProcessor()


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "message": "VoiceSketch AI is running",
        "llm_provider": llm_handler.get_provider(),
        "image_available": llm_handler.image_generator.is_available(),
    }


@app.get("/api/scene")
async def get_scene():
    return scene_manager.get_state().model_dump()


@app.post("/api/scene/clear")
async def clear_scene():
    scene_manager.clear_scene()
    llm_handler.clear_history()
    return {"status": "cleared"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("WebSocket connected")

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            msg_type = message.get("type", "")

            if msg_type == "voice":
                raw_text = message.get("data", {}).get("text", "")
                processed = voice_processor.process(raw_text)

                if processed["command_type"] == "clear":
                    scene_manager.clear_scene()
                    llm_handler.clear_history()
                    await websocket.send_json({
                        "type": "action",
                        "data": {
                            "actions": [{"action": "clear"}],
                            "explanation": "已清空画布",
                        }
                    })
                    await websocket.send_json({
                        "type": "state",
                        "data": scene_manager.get_state().model_dump(),
                    })
                    continue

                scene_state = scene_manager.get_state().model_dump()
                ai_response = await llm_handler.process_command(
                    processed["corrected"], scene_state
                )

                for action in ai_response.actions:
                    scene_manager.execute_action(action)

                await websocket.send_json({
                    "type": "action",
                    "data": ai_response.model_dump(),
                })

                await websocket.send_json({
                    "type": "state",
                    "data": scene_manager.get_state().model_dump(),
                })

            elif msg_type == "get_state":
                await websocket.send_json({
                    "type": "state",
                    "data": scene_manager.get_state().model_dump(),
                })

    except WebSocketDisconnect:
        print("WebSocket disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "data": {"message": str(e)},
            })
        except:
            pass


frontend_dir = Path(__file__).parent.parent.parent / "frontend" / "dist"
if frontend_dir.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dir / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        file_path = frontend_dir / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(frontend_dir / "index.html"))
