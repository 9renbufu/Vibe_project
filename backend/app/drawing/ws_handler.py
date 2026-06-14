"""
绘图 WebSocket 处理器
"""

import asyncio
from uuid import uuid4
from dataclasses import asdict
from typing import Dict, List, Optional

from .parser import parse_command, CommandType
from .engine import DrawingEngine


class DrawingSession:
    def __init__(self, width: int = 1200, height: int = 800):
        self.session_id = str(uuid4())
        self.engine = DrawingEngine(width, height)
        self.command_history: List[Dict] = []


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
                    # 在线程中运行 CPU 密集型生成
                    instructions = await asyncio.to_thread(engine_method, {"color": parsed.color})
                    art_names = {
                        "flow_field": "流场", "fractal_tree": "分形树", "watercolor": "水彩",
                        "mandala": "曼陀罗", "spirograph": "螺线", "voronoi": "沃罗诺伊",
                        "particle": "粒子", "wave": "波浪", "stripe": "条纹", "gradient": "渐变",
                    }
                    response_text = f"已生成 {art_names.get(art_type, art_type)} 艺术"
                else:
                    response_text = f"暂不支持 {art_type} 类型"

            elif parsed.command_type == CommandType.DRAW_SCENE:
                scene_type = parsed.scene_type or "sunset"
                instructions = await asyncio.to_thread(
                    session.engine.generate_landscape, scene_type, {"color": parsed.color}
                )
                scene_names = {
                    "sunset": "日落", "ocean": "海洋", "mountain": "山脉",
                    "starry_sky": "星空", "forest": "森林", "grassland": "草原",
                    "desert": "沙漠", "snow": "雪景", "spring": "春天花海",
                }
                response_text = f"已绘制 {scene_names.get(scene_type, scene_type)} 风景"

            elif parsed.command_type == CommandType.SET_COLOR:
                session.engine.current_color = parsed.color or (50, 50, 50)
                response_text = f"颜色已更改"

            elif parsed.command_type == CommandType.SET_SIZE:
                session.engine.current_size = parsed.size or 80
                response_text = f"大小已更改"

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

            elif parsed.command_type == CommandType.DELETE:
                response_text = "删除功能开发中"

            elif parsed.command_type == CommandType.FILL:
                response_text = "填充功能开发中"

            else:
                response_text = f"未识别指令: {text}"

        except Exception as e:
            response_text = f"执行出错: {str(e)}"

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
                },
                "response": response_text,
                "command_history": session.command_history[-20:],
            },
        }
