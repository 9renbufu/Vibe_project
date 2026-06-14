"""
绘图 WebSocket 处理器 - 多画布记录系统
"""

import asyncio
import json
import os
from uuid import uuid4
from dataclasses import asdict
from datetime import datetime
from typing import Dict, List, Optional, AsyncGenerator
from pathlib import Path

from .parser import parse_command, CommandType
from .engine import DrawingEngine

DATA_DIR = Path(__file__).parent.parent.parent / "data" / "drawing"
PREFS_FILE = DATA_DIR / "preferences.json"
HISTORY_FILE = DATA_DIR / "history.json"

STREAM_BATCH_SIZE = 8  # 流式输出每批指令数
STREAM_DELAY = 0.05    # 批次间延迟(秒)，模拟真人绘画节奏


class DrawingSession:
    def __init__(self, width: int = 1200, height: int = 800):
        self.session_id = str(uuid4())
        self.width = width
        self.height = height
        # 多画布记录：每个记录一个独立引擎
        self.engines: Dict[str, DrawingEngine] = {}
        self.active_record_id: Optional[str] = None
        self.records_meta: Dict[str, Dict] = {}
        # 全局状态
        self.command_history: List[Dict] = []
        self.preferences = self._load_preferences()
        self.drawing_history = self._load_history()
        # 兼容旧代码的属性
        self._engine = DrawingEngine(width, height)

    @property
    def engine(self) -> DrawingEngine:
        """兼容旧代码，返回活跃引擎"""
        return self.get_active_engine()

    def create_record(self, title: str = "") -> str:
        """创建新画布记录，返回 record_id"""
        record_id = str(uuid4())[:8]
        self.engines[record_id] = DrawingEngine(self.width, self.height)
        self.records_meta[record_id] = {
            "id": record_id,
            "title": title or f"作品 {len(self.engines)}",
            "created_at": datetime.now().isoformat(),
            "command_count": 0,
            "shape_count": 0,
        }
        self.active_record_id = record_id
        return record_id

    def switch_record(self, record_id: str) -> Optional[DrawingEngine]:
        """切换到指定记录"""
        if record_id in self.engines:
            self.active_record_id = record_id
            return self.engines[record_id]
        return None

    def get_active_engine(self) -> DrawingEngine:
        """获取当前活跃引擎，无则自动创建"""
        if not self.active_record_id or self.active_record_id not in self.engines:
            self.create_record()
        return self.engines[self.active_record_id]

    def get_active_record_id(self) -> str:
        """获取当前活跃记录 ID"""
        if not self.active_record_id or self.active_record_id not in self.engines:
            self.create_record()
        return self.active_record_id

    def list_records(self) -> List[Dict]:
        """列出所有记录的元数据"""
        result = []
        for rid, meta in self.records_meta.items():
            # 实时更新 shape_count
            if rid in self.engines:
                meta["shape_count"] = len(self.engines[rid].shapes)
            result.append(meta)
        return result

    def update_active_meta(self):
        """更新活跃记录的元数据"""
        rid = self.active_record_id
        if rid and rid in self.engines and rid in self.records_meta:
            self.records_meta[rid]["shape_count"] = len(self.engines[rid].shapes)
            self.records_meta[rid]["command_count"] = self.records_meta[rid].get("command_count", 0) + 1

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
        engine = self.get_active_engine()
        self.drawing_history.append({
            "command": command,
            "response": response,
            "shape_count": len(engine.shapes),
            "background": str(engine.background),
            "record_id": self.active_record_id,
            "timestamp": datetime.now().isoformat(),
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

    async def process_message_stream(self, session: DrawingSession, message: dict) -> AsyncGenerator[dict, None]:
        """流式处理消息，分批返回绘图指令"""
        msg_type = message.get("type", "")
        data = message.get("data", {})

        if msg_type in ("voice_input", "text_input"):
            text = data.get("text", "")
            async for batch in self._handle_command_stream(session, text):
                yield batch
        else:
            result = await self.process_message(session, message)
            yield result

    async def _handle_command_stream(self, session: DrawingSession, text: str) -> AsyncGenerator[dict, None]:
        """流式处理绘图指令，分批返回"""
        # 确保有活跃记录
        record_id = session.get_active_record_id()
        engine = session.get_active_engine()

        parsed = parse_command(text)

        session.command_history.append({
            "text": text,
            "type": parsed.command_type.value,
            "confidence": parsed.confidence,
        })

        response_text = ""
        all_instructions = []
        error = False

        try:
            if parsed.command_type == CommandType.DRAW_SHAPE:
                all_instructions = engine.draw_shape(
                    shape_type=parsed.shape_type or "circle",
                    color=parsed.color,
                    size=parsed.size,
                    position=parsed.position,
                )
                response_text = f"已绘制 {parsed.shape_type or '圆形'}"

            elif parsed.command_type == CommandType.DRAW_ART:
                art_type = parsed.art_type or "flow_field"
                engine_method = getattr(engine, f"generate_{art_type}", None)
                if engine_method:
                    all_instructions = await asyncio.to_thread(engine_method, {"color": parsed.color, "append": True})
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
                all_instructions = await asyncio.to_thread(
                    engine.generate_landscape, scene_type, {"color": parsed.color, "append": True}
                )
                scene_names = {
                    "sunset": "日落", "ocean": "海洋", "mountain": "山脉",
                    "starry_sky": "星空", "forest": "森林", "grassland": "草原",
                    "desert": "沙漠", "snow": "雪景", "spring": "春天花海",
                }
                response_text = f"已绘制 {scene_names.get(scene_type, scene_type)} 风景"

            elif parsed.command_type == CommandType.SET_COLOR:
                engine.current_color = parsed.color or (50, 50, 50)
                response_text = f"颜色已更改为 RGB{parsed.color or (50, 50, 50)}"

            elif parsed.command_type == CommandType.SET_SIZE:
                engine.current_size = parsed.size or 80
                response_text = f"大小已更改为 {parsed.size or 80}"

            elif parsed.command_type == CommandType.UNDO:
                all_instructions = engine.undo()
                response_text = "已撤销"

            elif parsed.command_type == CommandType.REDO:
                all_instructions = engine.redo()
                response_text = "已重做"

            elif parsed.command_type == CommandType.CLEAR:
                all_instructions = engine.clear()
                response_text = "画布已清空"

            else:
                response_text = f"未识别指令: {text}，请重试"
                error = True

        except Exception as e:
            response_text = f"执行出错: {str(e)}"
            error = True

        if not error:
            session.update_preferences(parsed)
            session.save_drawing_snapshot(text, response_text)
            session.update_active_meta()

        state = engine.get_state()
        state["record_id"] = record_id
        parsed_info = {
            "type": parsed.command_type.value,
            "shape": parsed.shape_type,
            "art": parsed.art_type,
            "scene": parsed.scene_type,
            "confidence": parsed.confidence,
            "raw": text,
        }
        meta = {
            "state": state,
            "parsed": parsed_info,
            "response": response_text,
            "error": error,
            "record_id": record_id,
            "records": session.list_records(),
            "command_history": session.command_history[-20:],
            "preferences": session.preferences,
            "drawing_history": session.drawing_history[-10:],
        }

        # 流式输出：分批发送指令
        inst_dicts = [asdict(i) for i in all_instructions]

        if len(inst_dicts) <= STREAM_BATCH_SIZE:
            yield {
                "type": "drawing_update",
                "data": {
                    "instructions": inst_dicts,
                    **meta,
                },
            }
        else:
            first_batch = inst_dicts[:STREAM_BATCH_SIZE]
            yield {
                "type": "drawing_update",
                "data": {
                    "instructions": first_batch,
                    "streaming": True,
                    "total_count": len(inst_dicts),
                    **meta,
                },
            }

            for i in range(STREAM_BATCH_SIZE, len(inst_dicts), STREAM_BATCH_SIZE):
                await asyncio.sleep(STREAM_DELAY)
                batch = inst_dicts[i:i + STREAM_BATCH_SIZE]
                yield {
                    "type": "drawing_batch",
                    "data": {
                        "instructions": batch,
                        "progress": min(i + STREAM_BATCH_SIZE, len(inst_dicts)),
                        "total": len(inst_dicts),
                    },
                }

            yield {
                "type": "drawing_complete",
                "data": {"total": len(inst_dicts)},
            }

    async def process_message(self, session: DrawingSession, message: dict) -> dict:
        msg_type = message.get("type", "")
        data = message.get("data", {})
        engine = session.get_active_engine()

        if msg_type == "voice_input" or msg_type == "text_input":
            text = data.get("text", "")
            return await self._handle_command(session, text)

        elif msg_type == "create_record":
            title = data.get("title", "")
            record_id = session.create_record(title)
            new_engine = session.engines[record_id]
            return {
                "type": "record_created",
                "data": {
                    "record_id": record_id,
                    "records": session.list_records(),
                    "state": new_engine.get_state(),
                    "instructions": [],
                },
            }

        elif msg_type == "switch_record":
            record_id = data.get("record_id", "")
            target_engine = session.switch_record(record_id)
            if target_engine:
                # 返回该记录的完整画布状态（全量重绘）
                instructions = [asdict(i) for i in target_engine._full_redraw()]
                return {
                    "type": "record_switched",
                    "data": {
                        "record_id": record_id,
                        "records": session.list_records(),
                        "state": target_engine.get_state(),
                        "instructions": instructions,
                    },
                }
            else:
                return {"type": "error", "data": {"message": f"记录不存在: {record_id}"}}

        elif msg_type == "list_records":
            return {
                "type": "records_list",
                "data": {
                    "records": session.list_records(),
                    "active_record_id": session.active_record_id,
                },
            }

        elif msg_type == "get_state":
            return {
                "type": "canvas_state",
                "data": engine.get_state(),
            }

        elif msg_type == "reset":
            instructions = engine.clear()
            return {
                "type": "drawing_update",
                "data": {
                    "instructions": [asdict(i) for i in instructions],
                    "state": engine.get_state(),
                    "response": "画布已清空",
                    "record_id": session.active_record_id,
                    "records": session.list_records(),
                },
            }

        elif msg_type == "undo":
            instructions = engine.undo()
            return {
                "type": "drawing_update",
                "data": {
                    "instructions": [asdict(i) for i in instructions],
                    "state": engine.get_state(),
                    "response": "已撤销",
                    "record_id": session.active_record_id,
                    "records": session.list_records(),
                },
            }

        elif msg_type == "redo":
            instructions = engine.redo()
            return {
                "type": "drawing_update",
                "data": {
                    "instructions": [asdict(i) for i in instructions],
                    "state": engine.get_state(),
                    "response": "已重做",
                    "record_id": session.active_record_id,
                    "records": session.list_records(),
                },
            }

        return {"type": "error", "data": {"message": f"未知消息类型: {msg_type}"}}

    async def _handle_command(self, session: DrawingSession, text: str) -> dict:
        """非流式处理（备用）"""
        record_id = session.get_active_record_id()
        engine = session.get_active_engine()
        parsed = parse_command(text)

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
                instructions = engine.draw_shape(
                    shape_type=parsed.shape_type or "circle",
                    color=parsed.color,
                    size=parsed.size,
                    position=parsed.position,
                )
                response_text = f"已绘制 {parsed.shape_type or '圆形'}"

            elif parsed.command_type == CommandType.DRAW_ART:
                art_type = parsed.art_type or "flow_field"
                engine_method = getattr(engine, f"generate_{art_type}", None)
                if engine_method:
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
                    engine.generate_landscape, scene_type, {"color": parsed.color, "append": True}
                )
                scene_names = {
                    "sunset": "日落", "ocean": "海洋", "mountain": "山脉",
                    "starry_sky": "星空", "forest": "森林", "grassland": "草原",
                    "desert": "沙漠", "snow": "雪景", "spring": "春天花海",
                }
                response_text = f"已绘制 {scene_names.get(scene_type, scene_type)} 风景"

            elif parsed.command_type == CommandType.SET_COLOR:
                engine.current_color = parsed.color or (50, 50, 50)
                response_text = f"颜色已更改为 RGB{parsed.color or (50, 50, 50)}"

            elif parsed.command_type == CommandType.SET_SIZE:
                engine.current_size = parsed.size or 80
                response_text = f"大小已更改为 {parsed.size or 80}"

            elif parsed.command_type == CommandType.UNDO:
                instructions = engine.undo()
                response_text = "已撤销"

            elif parsed.command_type == CommandType.REDO:
                instructions = engine.redo()
                response_text = "已重做"

            elif parsed.command_type == CommandType.CLEAR:
                instructions = engine.clear()
                response_text = "画布已清空"

            else:
                response_text = f"未识别指令: {text}，请重试"
                error = True

        except Exception as e:
            response_text = f"执行出错: {str(e)}"
            error = True

        if not error:
            session.update_preferences(parsed)
            session.save_drawing_snapshot(text, response_text)
            session.update_active_meta()

        state = engine.get_state()
        state["record_id"] = record_id
        return {
            "type": "drawing_update",
            "data": {
                "instructions": [asdict(i) for i in instructions],
                "state": state,
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
                "record_id": record_id,
                "records": session.list_records(),
                "command_history": session.command_history[-20:],
                "preferences": session.preferences,
                "drawing_history": session.drawing_history[-10:],
            },
        }
