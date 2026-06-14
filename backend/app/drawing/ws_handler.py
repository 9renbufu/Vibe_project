"""
绘图 WebSocket 处理器
"""

import asyncio
import json
import os
from uuid import uuid4
from dataclasses import asdict
from typing import Dict, List, Optional
from pathlib import Path

from .parser import parse_command, CommandType
from .engine import DrawingEngine

DATA_DIR = Path(__file__).parent.parent.parent / "data" / "drawing"
PREFS_FILE = DATA_DIR / "preferences.json"
HISTORY_FILE = DATA_DIR / "history.json"


class DrawingSession:
    def __init__(self, width: int = 1200, height: int = 800):
        self.session_id = str(uuid4())
        self.engine = DrawingEngine(width, height)
        self.command_history: List[Dict] = []
        self.preferences = self._load_preferences()
        self.drawing_history = self._load_history()

    def _load_preferences(self) -> Dict:
        if PREFS_FILE.exists():
            try:
                return json.loads(PREFS_FILE.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {
            "favorite_colors": [],
            "favorite_styles": [],
            "favorite_shapes": [],
            "total_commands": 0,
        }

    def _save_preferences(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        PREFS_FILE.write_text(json.dumps(self.preferences, ensure_ascii=False, indent=2), encoding="utf-8")

    def _load_history(self) -> List[Dict]:
        if HISTORY_FILE.exists():
            try:
                return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
            except Exception:
                pass
        return []

    def _save_history(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        # 只保留最近 50 条
        self.drawing_history = self.drawing_history[-50:]
        HISTORY_FILE.write_text(json.dumps(self.drawing_history, ensure_ascii=False, indent=2), encoding="utf-8")

    def update_preferences(self, parsed):
        """根据用户指令更新偏好"""
        self.preferences["total_commands"] = self.preferences.get("total_commands", 0) + 1

        if parsed.color:
            colors = self.preferences.get("favorite_colors", [])
            color_str = f"rgb{parsed.color}"
            if color_str not in colors:
                colors.append(color_str)
                self.preferences["favorite_colors"] = colors[-10:]

        if parsed.shape_type:
            shapes = self.preferences.get("favorite_shapes", [])
            if parsed.shape_type not in shapes:
                shapes.append(parsed.shape_type)
                self.preferences["favorite_shapes"] = shapes[-10:]

        if parsed.art_type:
            styles = self.preferences.get("favorite_styles", [])
            if parsed.art_type not in styles:
                styles.append(parsed.art_type)
                self.preferences["favorite_styles"] = styles[-10:]

        self._save_preferences()

    def save_drawing_snapshot(self, command: str, response: str):
        """保存绘图快照到历史"""
        self.drawing_history.append({
            "command": command,
            "response": response,
            "shape_count": len(self.engine.shapes),
            "background": str(self.engine.background),
            "timestamp": __import__("datetime").datetime.now().isoformat(),
        })
        self._save_history()


class DrawingWSHandler:
    def __init__(self):
        self.sessions: Dict[str, DrawingSession] = {}

    def create_session(self, width: int = 1200, height: int = 800) -> DrawingSession:
        session = DrawingSession(width, height)
        self.sessions[session.session_id] = session
        return session

    def remove_session(self, session_id: str):
        self.sessions.pop(session_id, None)

    async def process_message(self, session: DrawingSession, message: dict) -> dict:
        msg_type = message.get("type", "")
        data = message.get("data", {})

        if msg_type == "voice_input" or msg_type == "text_input":
            text = data.get("text", "")
            return await self._handle_command(session, text)

        elif msg_type == "get_state":
            return {
                "type": "canvas_state",
                "data": session.engine.get_state(),
            }

        elif msg_type == "reset":
            instructions = session.engine.clear()
            return {
                "type": "drawing_update",
                "data": {
                    "instructions": [asdict(i) for i in instructions],
                    "state": session.engine.get_state(),
                    "response": "画布已清空",
                },
            }

        elif msg_type == "undo":
            instructions = session.engine.undo()
            return {
                "type": "drawing_update",
                "data": {
                    "instructions": [asdict(i) for i in instructions],
                    "state": session.engine.get_state(),
                    "response": "已撤销",
                },
            }

        elif msg_type == "redo":
            instructions = session.engine.redo()
            return {
                "type": "drawing_update",
                "data": {
                    "instructions": [asdict(i) for i in instructions],
                    "state": session.engine.get_state(),
                    "response": "已重做",
                },
            }

        return {"type": "error", "data": {"message": f"未知消息类型: {msg_type}"}}

    async def _handle_command(self, session: DrawingSession, text: str) -> dict:
        parsed = parse_command(text)

        # 记录历史
        session.command_history.append({
            "text": text,
            "type": parsed.command_type.value,
            "confidence": parsed.confidence,
        })

        response_text = ""
        instructions = []
        error = False

        try:
            if parsed.command_type == CommandType.DRAW_SHAPE:
                instructions = session.engine.draw_shape(
                    shape_type=parsed.shape_type or "circle",
                    color=parsed.color,
                    size=parsed.size,
                    position=parsed.position,
                )
                response_text = f"已绘制 {parsed.shape_type or '圆形'}"

            elif parsed.command_type == CommandType.DRAW_ART:
                art_type = parsed.art_type or "flow_field"
                engine_method = getattr(session.engine, f"generate_{art_type}", None)
                if engine_method:
                    # 增量模式：在现有画布上叠加
                    instructions = await asyncio.to_thread(engine_method, {"color": parsed.color, "append": True})
                    art_names = {
                        "flow_field": "流场", "fractal_tree": "分形树", "watercolor": "水彩",
                        "mandala": "曼陀罗", "spirograph": "螺线", "voronoi": "沃罗诺伊",
                        "particle": "粒子", "wave": "波浪", "stripe": "条纹", "gradient": "渐变",
                    }
                    response_text = f"已生成 {art_names.get(art_type, art_type)} 艺术"
                else:
                    response_text = f"暂不支持 {art_type} 类型"
                    error = True

            elif parsed.command_type == CommandType.DRAW_SCENE:
                scene_type = parsed.scene_type or "sunset"
                instructions = await asyncio.to_thread(
                    session.engine.generate_landscape, scene_type, {"color": parsed.color, "append": True}
                )
                scene_names = {
                    "sunset": "日落", "ocean": "海洋", "mountain": "山脉",
                    "starry_sky": "星空", "forest": "森林", "grassland": "草原",
                    "desert": "沙漠", "snow": "雪景", "spring": "春天花海",
                }
                response_text = f"已绘制 {scene_names.get(scene_type, scene_type)} 风景"

            elif parsed.command_type == CommandType.SET_COLOR:
                session.engine.current_color = parsed.color or (50, 50, 50)
                response_text = f"颜色已更改为 RGB{parsed.color or (50, 50, 50)}"

            elif parsed.command_type == CommandType.SET_SIZE:
                session.engine.current_size = parsed.size or 80
                response_text = f"大小已更改为 {parsed.size or 80}"

            elif parsed.command_type == CommandType.UNDO:
                instructions = session.engine.undo()
                response_text = "已撤销"

            elif parsed.command_type == CommandType.REDO:
                instructions = session.engine.redo()
                response_text = "已重做"

            elif parsed.command_type == CommandType.CLEAR:
                instructions = session.engine.clear()
                response_text = "画布已清空"

            elif parsed.command_type == CommandType.MOVE:
                response_text = "移动功能开发中"
                error = True

            elif parsed.command_type == CommandType.DELETE:
                response_text = "删除功能开发中"
                error = True

            elif parsed.command_type == CommandType.FILL:
                response_text = "填充功能开发中"
                error = True

            else:
                response_text = f"未识别指令: {text}，请重试"
                error = True

        except Exception as e:
            response_text = f"执行出错: {str(e)}"
            error = True

        # 更新偏好和历史
        if not error:
            session.update_preferences(parsed)
            session.save_drawing_snapshot(text, response_text)

        # 未知指令：返回空指令但保留当前画布状态
        return {
            "type": "drawing_update",
            "data": {
                "instructions": [asdict(i) for i in instructions],
                "state": session.engine.get_state(),
                "parsed": {
                    "type": parsed.command_type.value,
                    "shape": parsed.shape_type,
                    "art": parsed.art_type,
                    "scene": parsed.scene_type,
                    "confidence": parsed.confidence,
                    "raw": text,
                },
                "response": response_text,
                "error": error,
                "command_history": session.command_history[-20:],
                "preferences": session.preferences,
                "drawing_history": session.drawing_history[-10:],
            },
        }
