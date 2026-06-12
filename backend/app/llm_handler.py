import os
import json
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
from .models import (
    DrawingAction, AIResponse, Shape, ShapeType, Position, Color
)
from .image_generator import ImageGenerator


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
        self.image_generator = ImageGenerator(lazy_init=False)
        self._init_llm()
        print(f"Image generator available: {self.image_generator.is_available()}")

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

        return f"""你是一个专业的 AI 绘图助手，擅长将自然语言转换为精美的绘图指令。

当前场景状态:
- 画布大小: {scene_state.get('width', 800)}x{scene_state.get('height', 600)}
- 已有图形:
{shapes_desc if shapes_desc else "  (空画布)"}

请用 JSON 格式回复，生成绘图动作:
{{
    "actions": [
        {{
            "action": "create" | "move" | "delete" | "modify" | "clear",
            "shape": {{
                "type": "circle" | "ellipse" | "rectangle" | "triangle" | "line" | "text" | "polygon",
                "position": {{"x": 数字, "y": 数字}},
                "name": "描述性中文名称",
                "color": {{"r": 0-255, "g": 0-255, "b": 0-255, "a": 0-1}},
                "fill": true/false,
                "width": 数字,
                "height": 数字,
                "radius": 数字,
                "text": "文字内容",
                "zIndex": 数字 (1-100, 越大越上层)
            }},
            "target_name": "已有图形的名称",
            "position": {{"x": 数字, "y": 数字}},
            "properties": {{}}
        }}
    ],
    "explanation": "简短中文解释",
    "scene_description": "场景描述"
}}

绘图技巧:
1. 使用描述性中文名称: "太阳"、"房子"、"树木"、"云朵"
2. 位置范围: x(0-800), y(0-600)
3. 颜色丰富: 天空用蓝色渐变，草地用绿色，太阳用金黄色
4. 层次分明: 背景 zIndex=1, 中景 zIndex=5-10, 前景 zIndex=20+
5. 复杂场景拆解: 先画背景(天空、地面)，再画主体(建筑、人物)，最后画细节(装饰、文字)
6. 场景示例:
   - "海边日落": 天空(蓝紫渐变) → 太阳(橙色圆) → 海面(蓝色矩形) → 沙滩(黄色) → 椰子树
   - "赛博朋克城市": 深色背景 → 霓虹建筑群 → 飞车灯光 → 全息广告牌
   - "森林小屋": 蓝天 → 绿色山丘 → 木屋 → 树木群 → 小路

只返回 JSON，不要其他内容。"""

    def _build_image_prompt_system(self) -> str:
        return """你是一个专业的 AI 绘图提示词专家。将用户的中文描述转换为高质量的英文图像生成提示词。

要求：
1. 将中文翻译成英文
2. 添加艺术风格描述（如：digital art, illustration, realistic, anime style 等）
3. 添加细节描述（色彩、光影、构图等）
4. 添加质量标签（如：high quality, detailed, masterpiece）

只返回英文提示词，不要其他内容。

示例：
用户："画一个赛博朋克城市"
返回："A cyberpunk city at night, neon lights, futuristic buildings, rain-soaked streets, holographic advertisements, vibrant purple and blue colors, digital art, highly detailed, 8k quality"

用户："画一个海边日落"
返回："Beautiful sunset over the ocean, golden hour, warm orange and pink sky, calm waves, silhouette of palm trees, peaceful atmosphere, realistic photography, high quality, stunning colors" """

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

            result = self._parse_response(response_text)

            # 尝试生成图像
            if self.image_generator.is_available():
                try:
                    # 生成图像提示词
                    image_prompt_system = self._build_image_prompt_system()
                    image_prompt_response = await self.llm.chat(
                        [{"role": "user", "content": command}],
                        image_prompt_system
                    )
                    image_prompt = image_prompt_response.strip()
                    print(f"Image prompt: {image_prompt}")

                    # 生成图像
                    image_data = await self.image_generator.generate(image_prompt)
                    if image_data:
                        result.image_url = image_data
                        result.image_prompt = image_prompt
                except Exception as e:
                    print(f"Image generation error: {e}")

            return result

        except Exception as e:
            print(f"LLM API error: {e}")
            return self._fallback_parse(command, scene_state)

    def _parse_response(self, text: str) -> AIResponse:
        try:
            # 处理 markdown 代码块
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]

            json_start = text.find("{")
            json_end = text.rfind("}") + 1
            if json_start != -1 and json_end > json_start:
                json_str = text[json_start:json_end]
                # 修复常见的 JSON 问题
                json_str = json_str.replace('\n', ' ').replace('\r', '')
                # 修复尾随逗号
                import re
                json_str = re.sub(r',\s*}', '}', json_str)
                json_str = re.sub(r',\s*]', ']', json_str)
                # 修复单引号
                json_str = json_str.replace("'", '"')
                data = json.loads(json_str)
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

        # JSON 解析失败时，返回原始文本作为解释
        return AIResponse(actions=[], explanation=text[:200] if text else "无法解析指令")

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
