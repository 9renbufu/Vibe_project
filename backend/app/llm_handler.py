import os
import json
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
from .models import (
    DrawingAction, AIResponse, Shape, ShapeType, Position, Color
)


class BaseLLM(ABC):
    @abstractmethod
    async def chat(self, messages: List[Dict[str, str]], system: str) -> str:
        pass


class ClaudeLLM(BaseLLM):
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        from anthropic import Anthropic
        self.client = Anthropic(api_key=api_key)
        self.model = model

    async def chat(self, messages: List[Dict[str, str]], system: str) -> str:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            system=system,
            messages=messages,
        )
        return response.content[0].text


class OpenAILLM(BaseLLM):
    def __init__(self, api_key: str, model: str = "gpt-4o", base_url: str = None):
        from openai import OpenAI
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url,
        )
        self.model = model

    async def chat(self, messages: List[Dict[str, str]], system: str) -> str:
        formatted = [{"role": "system", "content": system}] + messages
        response = self.client.chat.completions.create(
            model=self.model,
            messages=formatted,
            max_tokens=2000,
        )
        return response.choices[0].message.content


class LLMHandler:
    def __init__(self):
        self.conversation_history: List[Dict[str, str]] = []
        self.llm: Optional[BaseLLM] = None
        self._init_llm()

    def _init_llm(self):
        provider = os.getenv("LLM_PROVIDER", "claude").lower()

        if provider == "claude":
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if api_key:
                model = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")
                self.llm = ClaudeLLM(api_key, model)
                print(f"Using Claude model: {model}")

        elif provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                model = os.getenv("OPENAI_MODEL", "gpt-4o")
                base_url = os.getenv("OPENAI_BASE_URL")
                self.llm = OpenAILLM(api_key, model, base_url)
                print(f"Using OpenAI model: {model}")

        elif provider == "deepseek":
            api_key = os.getenv("DEEPSEEK_API_KEY")
            if api_key:
                self.llm = OpenAILLM(
                    api_key=api_key,
                    model="deepseek-chat",
                    base_url="https://api.deepseek.com"
                )
                print("Using DeepSeek model")

        elif provider == "qwen":
            api_key = os.getenv("DASHSCOPE_API_KEY")
            if api_key:
                self.llm = OpenAILLM(
                    api_key=api_key,
                    model=os.getenv("QWEN_MODEL", "qwen-turbo"),
                    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
                )
                print("Using Qwen model")

        elif provider == "zhipu":
            api_key = os.getenv("ZHIPU_API_KEY")
            if api_key:
                self.llm = OpenAILLM(
                    api_key=api_key,
                    model=os.getenv("ZHIPU_MODEL", "glm-4-flash"),
                    base_url="https://open.bigmodel.cn/api/paas/v4"
                )
                print("Using Zhipu GLM model")

        elif provider == "moonshot":
            api_key = os.getenv("MOONSHOT_API_KEY")
            if api_key:
                self.llm = OpenAILLM(
                    api_key=api_key,
                    model="moonshot-v1-8k",
                    base_url="https://api.moonshot.cn/v1"
                )
                print("Using Moonshot model")

        elif provider == "ollama":
            base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
            model = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
            self.llm = OpenAILLM(
                api_key="ollama",
                model=model,
                base_url=base_url,
            )
            print(f"Using Ollama model: {model}")

        if not self.llm:
            print("No LLM configured, using fallback parser")

    def _build_system_prompt(self, scene_state: Dict[str, Any]) -> str:
        shapes_desc = ""
        for s in scene_state.get("shapes", []):
            name = s.get("name", s.get("id", "unknown"))
            shapes_desc += f"- {name} ({s['type']}) at ({s['position']['x']}, {s['position']['y']})\n"

        return f"""你是一个 AI 绘图助手。将自然语言指令转换为绘图动作。

当前场景状态:
- 画布大小: {scene_state.get('width', 800)}x{scene_state.get('height', 600)}
- 背景色: rgb({scene_state.get('background', {}).get('r', 255)}, {scene_state.get('background', {}).get('g', 255)}, {scene_state.get('background', {}).get('b', 255)})
- 已有图形:
{shapes_desc if shapes_desc else "  (空画布)"}

请用 JSON 格式回复:
{{
    "actions": [
        {{
            "action": "create" | "move" | "delete" | "modify" | "clear",
            "shape": {{
                "type": "circle" | "rectangle" | "line" | "triangle" | "polygon" | "text",
                "position": {{"x": 数字, "y": 数字}},
                "name": "描述性名称",
                "color": {{"r": 0-255, "g": 0-255, "b": 0-255}},
                "fill": true/false,
                "width": 数字,
                "height": 数字,
                "radius": 数字,
                "text": "文字内容",
                "zIndex": 数字
            }},
            "target_name": "已有图形的名称",
            "position": {{"x": 数字, "y": 数字}},
            "properties": {{}}
        }}
    ],
    "explanation": "简短解释你做了什么",
    "scene_description": "场景描述"
}}

重要:
- 使用描述性名称如 "太阳"、"房子"、"树" 方便用户后续引用
- 位置应在画布范围内 (0-800 x, 0-600 y)
- 复杂场景拆分为多个图形
- 使用 zIndex 控制图层 (越大越上层)
- 颜色要丰富有创意
- 只返回 JSON，不要其他内容"""

    async def process_command(
        self, command: str, scene_state: Dict[str, Any]
    ) -> AIResponse:
        system_prompt = self._build_system_prompt(scene_state)

        messages = self.conversation_history.copy()
        messages.append({"role": "user", "content": command})

        try:
            if not self.llm:
                return self._fallback_parse(command, scene_state)

            response_text = await self.llm.chat(messages, system_prompt)

            self.conversation_history.append({"role": "user", "content": command})
            self.conversation_history.append(
                {"role": "assistant", "content": response_text}
            )

            if len(self.conversation_history) > 20:
                self.conversation_history = self.conversation_history[-20:]

            return self._parse_response(response_text)

        except Exception as e:
            print(f"LLM API error: {e}")
            return self._fallback_parse(command, scene_state)

    def _parse_response(self, text: str) -> AIResponse:
        try:
            json_start = text.find("{")
            json_end = text.rfind("}") + 1
            if json_start != -1 and json_end > json_start:
                data = json.loads(text[json_start:json_end])
                actions = []
                for a in data.get("actions", []):
                    shape = None
                    if "shape" in a and a["shape"]:
                        s = a["shape"]
                        shape = Shape(
                            id="",
                            type=ShapeType(s.get("type", "circle")),
                            position=Position(**s.get("position", {"x": 400, "y": 300})),
                            name=s.get("name"),
                            color=Color(**s.get("color", {"r": 0, "g": 0, "b": 0})),
                            fill=s.get("fill", True),
                            width=s.get("width"),
                            height=s.get("height"),
                            radius=s.get("radius"),
                            text=s.get("text"),
                            zIndex=s.get("zIndex", 0),
                        )
                    action = DrawingAction(
                        action=a.get("action", "create"),
                        shape=shape,
                        shape_id=a.get("shape_id"),
                        target_name=a.get("target_name"),
                        position=Position(**a["position"]) if "position" in a else None,
                        properties=a.get("properties"),
                    )
                    actions.append(action)

                return AIResponse(
                    actions=actions,
                    explanation=data.get("explanation", ""),
                    scene_description=data.get("scene_description"),
                )
        except Exception as e:
            print(f"Parse error: {e}")

        return AIResponse(actions=[], explanation="无法解析指令")

    def _fallback_parse(self, command: str, scene_state: Dict) -> AIResponse:
        actions = []
        explanation = ""
        cmd = command.lower()

        if "太阳" in cmd or "sun" in cmd:
            if "画" in cmd or "draw" in cmd or "创建" in cmd:
                actions.append(DrawingAction(
                    action="create",
                    shape=Shape(
                        id="", type=ShapeType.CIRCLE,
                        position=Position(x=600, y=150),
                        radius=60, name="太阳",
                        color=Color(r=255, g=200, b=0), fill=True, zIndex=1,
                    )
                ))
                explanation = "画了一个黄色太阳"
            elif "移" in cmd or "move" in cmd:
                shape = None
                for s in scene_state.get("shapes", []):
                    if "太阳" in (s.get("name") or ""):
                        shape = s
                        break
                if shape:
                    new_x = 200 if "左" in cmd else 600
                    actions.append(DrawingAction(
                        action="move",
                        target_name=shape.get("name"),
                        position=Position(x=new_x, y=150),
                    ))
                    explanation = f"将太阳移到{'左边' if '左' in cmd else '右边'}"

        elif "房子" in cmd or "house" in cmd:
            actions.append(DrawingAction(
                action="create",
                shape=Shape(
                    id="", type=ShapeType.RECTANGLE,
                    position=Position(x=350, y=300),
                    width=200, height=150, name="房子",
                    color=Color(r=139, g=90, b=43), fill=True, zIndex=1,
                )
            ))
            actions.append(DrawingAction(
                action="create",
                shape=Shape(
                    id="", type=ShapeType.TRIANGLE,
                    position=Position(x=450, y=220),
                    width=240, height=100, name="屋顶",
                    color=Color(r=180, g=30, b=30), fill=True, zIndex=2,
                )
            ))
            explanation = "画了一栋房子"

        elif "树" in cmd or "tree" in cmd:
            actions.append(DrawingAction(
                action="create",
                shape=Shape(
                    id="", type=ShapeType.RECTANGLE,
                    position=Position(x=150, y=350),
                    width=30, height=80, name="树干",
                    color=Color(r=101, g=67, b=33), fill=True, zIndex=1,
                )
            ))
            actions.append(DrawingAction(
                action="create",
                shape=Shape(
                    id="", type=ShapeType.CIRCLE,
                    position=Position(x=165, y=300),
                    radius=50, name="树冠",
                    color=Color(r=34, g=139, b=34), fill=True, zIndex=2,
                )
            ))
            explanation = "画了一棵树"

        elif "清除" in cmd or "clear" in cmd or "清空" in cmd:
            actions.append(DrawingAction(action="clear"))
            explanation = "已清空画布"

        else:
            explanation = f"收到指令: {command}（需要配置 LLM API 进行更复杂的解析）"

        return AIResponse(actions=actions, explanation=explanation)

    def clear_history(self):
        self.conversation_history.clear()

    def get_provider(self) -> str:
        return os.getenv("LLM_PROVIDER", "none")
