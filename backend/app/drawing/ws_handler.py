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
from .agent import DrawingAgent

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
        # Agent 评估结果
        self.last_evaluation: Optional[Dict] = None
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
    def __init__(self, llm_client=None, vision_client=None):
        self.sessions: Dict[str, DrawingSession] = {}
        self.agent = DrawingAgent(llm_client, vision_client) if llm_client else None

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
        """流式处理绘图指令，分批返回，支持复合指令"""
        record_id = session.get_active_record_id()
        engine = session.get_active_engine()

        parsed = parse_command(text)

        # 低置信度时用 LLM 纠错
        llm_corrected = False
        corrected_text = ""
        if self.agent and (parsed.confidence < 0.7 or parsed.command_type == CommandType.UNKNOWN):
            try:
                corrected_text = await self.agent.correct_command(text, parsed.confidence)
                if corrected_text and corrected_text != text:
                    reparsed = parse_command(corrected_text)
                    if reparsed.command_type != CommandType.UNKNOWN and reparsed.confidence > parsed.confidence:
                        parsed = reparsed
                        llm_corrected = True
            except Exception:
                pass

        session.command_history.append({
            "text": text,
            "type": parsed.command_type.value,
            "confidence": parsed.confidence,
            "llm_corrected": llm_corrected,
        })

        response_text = f"理解为: {corrected_text}" if llm_corrected else ""
        all_instructions = []
        error = False

        # 复合指令：收集所有子指令的结果
        compound_parts = parsed.params.get("compound_parts", [])

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

        # 执行复合指令的后续部分
        if not error and compound_parts:
            for part in compound_parts:
                try:
                    sub_parsed = parse_command(part)
                    sub_insts = await self._execute_single(engine, sub_parsed)
                    all_instructions.extend(sub_insts)
                    if sub_parsed.command_type != CommandType.UNKNOWN:
                        response_text += f"，然后{self._describe_command(sub_parsed)}"
                except Exception:
                    pass

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

        # 绘制完成后自动评估（不阻塞响应）
        if self.agent and not error and len(all_instructions) > 0:
            send_cb = self._ws_send_callback if hasattr(self, '_ws_send_callback') else None
            asyncio.create_task(self._evaluate_async(session, engine, send_cb))

    async def _evaluate_async(self, session: DrawingSession, engine: DrawingEngine,
                               send_callback=None):
        """异步评估画作，完成后通过回调发送结果"""
        try:
            state = engine.get_state()
            evaluation = await self.agent.evaluate_drawing(
                state, session.command_history[-10:]
            )
            session.last_evaluation = evaluation
            if send_callback:
                await send_callback({
                    "type": "evaluation_result",
                    "data": {
                        "evaluation": evaluation,
                        "record_id": session.active_record_id,
                    },
                })
        except Exception as e:
            print(f"[DrawingAgent] Evaluation error: {e}")

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

        elif msg_type == "evaluate":
            # 手动触发评估
            if self.agent:
                state = engine.get_state()
                evaluation = await self.agent.evaluate_drawing(
                    state, session.command_history[-10:]
                )
                session.last_evaluation = evaluation
                return {
                    "type": "evaluation_result",
                    "data": {
                        "evaluation": evaluation,
                        "record_id": session.active_record_id,
                    },
                }
            else:
                return {"type": "error", "data": {"message": "LLM Agent 未配置，无法评估"}}

        elif msg_type == "accept_suggestion":
            # 接受修改建议
            evaluation = session.last_evaluation
            if not evaluation:
                return {"type": "error", "data": {"message": "没有待处理的建议"}}

            idx = data.get("index", -1)
            suggestions = evaluation.get("suggestions", [])

            if idx >= 0 and idx < len(suggestions):
                cmd = suggestions[idx].get("command", "")
                if cmd:
                    session.last_evaluation = None
                    return await self._handle_single_command(session, cmd)
            elif suggestions:
                cmd = suggestions[0].get("command", "")
                if cmd:
                    session.last_evaluation = None
                    return await self._handle_single_command(session, cmd)
            return {"type": "suggestion_applied", "data": {"index": -1}}

        elif msg_type == "reject_suggestion":
            session.last_evaluation = None
            return {"type": "suggestion_rejected", "data": {}}

        elif msg_type == "apply_feedback":
            # 用户语音反馈
            feedback_text = data.get("text", "")
            if not feedback_text:
                return {"type": "error", "data": {"message": "缺少反馈内容"}}

            if self.agent and session.last_evaluation:
                # 分析用户意图
                analysis = await self.agent.analyze_feedback(
                    feedback_text, session.last_evaluation
                )
                action = analysis.get("action", "unknown")

                if action == "accept":
                    session.last_evaluation = None
                    return {"type": "feedback_result", "data": {"action": "accepted"}}
                elif action == "reject":
                    session.last_evaluation = None
                    return {"type": "feedback_result", "data": {"action": "rejected"}}
                elif action == "modify":
                    # 执行修改指令
                    commands = analysis.get("commands", [])
                    if commands:
                        cmd = commands[0]
                        return await self._handle_single_command(session, cmd)
                    return {"type": "feedback_result", "data": {"action": "modify", "commands": commands}}
                else:
                    # 当作普通指令处理
                    return await self._handle_single_command(session, feedback_text)
            else:
                # 没有 Agent 或没有评估，当普通指令
                return await self._handle_single_command(session, feedback_text)

        return {"type": "error", "data": {"message": f"未知消息类型: {msg_type}"}}

    async def _handle_single_command(self, session: DrawingSession, text: str) -> dict:
        """处理单条指令，返回结果（非流式）"""
        record_id = session.get_active_record_id()
        engine = session.get_active_engine()
        parsed = parse_command(text)

        instructions = []
        response_text = ""

        try:
            if parsed.command_type == CommandType.DRAW_SHAPE:
                instructions = engine.draw_shape(
                    shape_type=parsed.shape_type or "circle",
                    color=parsed.color, size=parsed.size, position=parsed.position,
                )
                response_text = f"已绘制 {parsed.shape_type or '圆形'}"
            elif parsed.command_type == CommandType.DRAW_ART:
                art_type = parsed.art_type or "flow_field"
                method = getattr(engine, f"generate_{art_type}", None)
                if method:
                    instructions = await asyncio.to_thread(method, {"color": parsed.color, "append": True})
                    response_text = f"已生成 {art_type}"
            elif parsed.command_type == CommandType.DRAW_SCENE:
                instructions = await asyncio.to_thread(
                    engine.generate_landscape, parsed.scene_type or "sunset",
                    {"color": parsed.color, "append": True}
                )
                response_text = f"已绘制 {parsed.scene_type or '日落'}"
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
                response_text = f"未识别指令: {text}"
        except Exception as e:
            response_text = f"执行出错: {str(e)}"

        session.update_active_meta()
        return {
            "type": "drawing_update",
            "data": {
                "instructions": [asdict(i) for i in instructions],
                "state": engine.get_state(),
                "response": response_text,
                "error": False,
                "record_id": record_id,
                "records": session.list_records(),
            },
        }

    async def _execute_single(self, engine: DrawingEngine, parsed) -> list:
        """执行单条解析后的指令，返回指令列表"""
        if parsed.command_type == CommandType.DRAW_SHAPE:
            return engine.draw_shape(
                shape_type=parsed.shape_type or "circle",
                color=parsed.color,
                size=parsed.size,
                position=parsed.position,
            )

        elif parsed.command_type == CommandType.DRAW_ART:
            art_type = parsed.art_type or "flow_field"
            engine_method = getattr(engine, f"generate_{art_type}", None)
            if engine_method:
                return await asyncio.to_thread(engine_method, {"color": parsed.color, "append": True})
            return []

        elif parsed.command_type == CommandType.DRAW_SCENE:
            scene_type = parsed.scene_type or "sunset"
            return await asyncio.to_thread(
                engine.generate_landscape, scene_type, {"color": parsed.color, "append": True}
            )

        elif parsed.command_type == CommandType.SET_COLOR:
            engine.current_color = parsed.color or (50, 50, 50)
            return []

        elif parsed.command_type == CommandType.SET_SIZE:
            engine.current_size = parsed.size or 80
            return []

        elif parsed.command_type == CommandType.UNDO:
            return engine.undo()

        elif parsed.command_type == CommandType.REDO:
            return engine.redo()

        elif parsed.command_type == CommandType.CLEAR:
            return engine.clear()

        return []

    def _describe_command(self, parsed) -> str:
        """返回指令的可读描述"""
        if parsed.command_type == CommandType.DRAW_SHAPE:
            return f"画了{parsed.shape_type or '圆形'}"

        elif parsed.command_type == CommandType.DRAW_ART:
            art_names = {
                "flow_field": "流场", "fractal_tree": "分形树", "watercolor": "水彩",
                "mandala": "曼陀罗", "spirograph": "螺线", "voronoi": "沃罗诺伊",
                "particle": "粒子", "wave": "波浪", "stripe": "条纹", "gradient": "渐变",
            }
            return f"生成了{art_names.get(parsed.art_type, parsed.art_type)}"

        elif parsed.command_type == CommandType.DRAW_SCENE:
            scene_names = {
                "sunset": "日落", "ocean": "海洋", "mountain": "山脉",
                "starry_sky": "星空", "forest": "森林", "grassland": "草原",
                "desert": "沙漠", "snow": "雪景", "spring": "春天花海",
            }
            return f"绘制了{scene_names.get(parsed.scene_type, parsed.scene_type)}"

        elif parsed.command_type == CommandType.SET_COLOR:
            return f"改了颜色"

        elif parsed.command_type == CommandType.SET_SIZE:
            return f"改了大小"

        elif parsed.command_type == CommandType.UNDO:
            return "撤销"

        elif parsed.command_type == CommandType.REDO:
            return "重做"

        elif parsed.command_type == CommandType.CLEAR:
            return "清空了画布"

        return ""

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
