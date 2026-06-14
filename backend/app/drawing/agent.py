"""
绘图 LLM Agent - 指令纠错 + 画面评估 + 修改建议
作为规则引擎之上的智能增强层
"""

import json
import asyncio
from typing import Dict, Any, List, Optional

from ..modules.llm_client import BaseLLMClient


class DrawingAgent:
    """绘图智能助手：纠错、评估、修改建议"""

    def __init__(self, llm_client: BaseLLMClient, vision_client: BaseLLMClient = None):
        # 优先使用 vision client（通常是更强的模型如 GPT-5.4）
        self.llm = vision_client or llm_client
        self.vision = vision_client

    # ============ 理解任意意图，生成绘图指令 ============

    async def understand_and_generate(self, user_text: str) -> dict:
        """理解任意用户意图，生成结构化绘图数据"""
        if not self.llm:
            return {"understood": "", "commands": [], "shapes": [], "fallback": True}

        prompt = f"""用户说: "{user_text}"

请将用户的描述转换为绘图数据。返回 JSON，包含场景指令和结构化图形：

{{
  "understood": "你对用户意图的理解",
  "commands": ["场景或艺术指令，如 画星空、画海洋、画分形树"],
  "shapes": [
    {{"shape": "circle", "color": [255, 200, 0], "size": 120, "position": [0.8, 0.2], "label": "太阳"}},
    {{"shape": "rectangle", "color": [139, 90, 43], "size": 160, "position": [0.5, 0.6], "label": "墙"}},
    {{"shape": "triangle", "color": [220, 50, 50], "size": 140, "position": [0.5, 0.35], "label": "屋顶"}}
  ],
  "fallback": false
}}

shape 类型（必须是以下之一）：
- circle（圆）、rectangle（矩形）、triangle（三角形）、star（五角星）、heart（爱心）、ellipse（椭圆）、line（线条）

参数格式：
- color: RGB 数组 [r, g, b]，值 0-255
- size: 像素大小，建议 40-250
- position: 归一化坐标 [x, y]，0-1 之间。0.5=中心, 0.2=偏左/上, 0.8=偏右/下

commands 可用的场景/艺术指令：
- 画星空、画日落、画海洋、画山脉、画森林、画雪景、画春天
- 画流场、画分形树、画水彩、画曼陀罗、画螺线、画沃罗诺伊、画粒子、画波浪

创作规则：
1. 用多个基础图形组合来表达复杂事物，每个部件一个 shape
2. 通过不同颜色、大小、位置表达细节（如眼睛、耳朵等部件）
3. 先用 commands 画背景/场景，再用 shapes 画主体
4. 如果完全无法用图形表达，设 fallback=true

示例（画宇航员）：
commands: ["画星空"]
shapes: [
  {{"shape": "rectangle", "color": [180,180,180], "size": 140, "position": [0.5, 0.6], "label": "身体"}},
  {{"shape": "circle", "color": [220,220,220], "size": 100, "position": [0.5, 0.35], "label": "头盔"}},
  {{"shape": "circle", "color": [100,150,200], "size": 60, "position": [0.5, 0.35], "label": "面罩玻璃"}},
  {{"shape": "rectangle", "color": [180,180,180], "size": 60, "position": [0.38, 0.75], "label": "左腿"}},
  {{"shape": "rectangle", "color": [180,180,180], "size": 60, "position": [0.62, 0.75], "label": "右腿"}}
]

示例（画猫）：
shapes: [
  {{"shape": "circle", "color": [255,165,0], "size": 120, "position": [0.5, 0.5], "label": "脸"}},
  {{"shape": "triangle", "color": [255,165,0], "size": 40, "position": [0.4, 0.32], "label": "左耳"}},
  {{"shape": "triangle", "color": [255,165,0], "size": 40, "position": [0.6, 0.32], "label": "右耳"}},
  {{"shape": "circle", "color": [30,30,30], "size": 20, "position": [0.43, 0.47], "label": "左眼"}},
  {{"shape": "circle", "color": [30,30,30], "size": 20, "position": [0.57, 0.47], "label": "右眼"}},
  {{"shape": "circle", "color": [255,150,180], "size": 15, "position": [0.5, 0.55], "label": "鼻子"}}
]

示例（画房子）：
shapes: [
  {{"shape": "rectangle", "color": [139,90,43], "size": 200, "position": [0.5, 0.6], "label": "墙"}},
  {{"shape": "triangle", "color": [220,50,50], "size": 180, "position": [0.5, 0.35], "label": "屋顶"}},
  {{"shape": "rectangle", "color": [100,180,255], "size": 50, "position": [0.4, 0.55], "label": "左窗"}},
  {{"shape": "rectangle", "color": [100,180,255], "size": 50, "position": [0.6, 0.55], "label": "右窗"}},
  {{"shape": "rectangle", "color": [139,69,19], "size": 70, "position": [0.5, 0.72], "label": "门"}}
]"""

        system = "你是绘图指令生成器。将用户的任意描述转换为结构化绘图数据。返回纯 JSON，不要包含其他文字。"

        result = await self._call_llm(prompt, system)
        parsed = self._parse_json(result)
        if parsed.get("commands") or parsed.get("shapes"):
            return parsed
        return {"understood": "", "commands": [], "shapes": [], "fallback": True}

    # ============ 画面评估 ============

    async def evaluate_drawing(self, canvas_state: dict, command_history: list,
                                image_base64: str = None) -> dict:
        """画面美学评估，返回评分和建议"""
        if not self.llm:
            return self._default_evaluation()

        shapes_summary = self._summarize_shapes(canvas_state)
        recent_cmds = [h.get("text", "") for h in command_history[-5:]]

        prompt = f"""请评估这幅程序化生成的画作：

画布信息：
- 尺寸: {canvas_state.get('width', 1200)}x{canvas_state.get('height', 800)}
- 图形数量: {canvas_state.get('shape_count', 0)}
- 背景: {canvas_state.get('background', 'white')}
- 图形分布: {shapes_summary}
- 最近指令: {', '.join(recent_cmds)}

请严格用 JSON 格式返回评估（不要包含其他文字）：
{{
  "score": 75,
  "feedback": "一句话总体评价",
  "suggestions": [
    {{"text": "修改建议描述", "command": "对应的绘图指令"}},
    {{"text": "修改建议描述", "command": "对应的绘图指令"}}
  ],
  "color_feedback": "配色方面的评价",
  "composition_feedback": "构图方面的评价"
}}

评分标准：
- 60分以下：构图混乱，颜色不协调
- 60-75分：基本完整，有改进空间
- 75-85分：不错，色彩和构图较好
- 85分以上：优秀，视觉效果出色

建议的 command 必须是可执行的绘图指令，如"画一个红色的圆"、"画流场"等。"""

        system = "你是专业的美术评审老师，擅长评估程序化生成的数字艺术作品。请用 JSON 格式返回评估结果。"

        # 优先用 vision client（如果有图片）
        if image_base64 and self.vision:
            try:
                result = await self._call_llm_vision(prompt, image_base64, system)
                parsed = self._parse_json(result)
                if parsed.get("score"):
                    return parsed
            except Exception:
                pass

        # 回退到纯文本评估
        result = await self._call_llm(prompt, system)
        parsed = self._parse_json(result)
        return parsed if parsed.get("score") else self._default_evaluation()

    # ============ 修改建议 ============

    async def generate_revision(self, evaluation: dict, user_feedback: str,
                                 canvas_state: dict) -> dict:
        """根据评估和用户反馈生成修改指令"""
        if not self.llm:
            return {"should_revise": False, "commands": [], "explanation": ""}

        shapes_summary = self._summarize_shapes(canvas_state)

        prompt = f"""画布当前状态：
- 图形数量: {canvas_state.get('shape_count', 0)}
- 背景: {canvas_state.get('background', 'white')}
- 图形分布: {shapes_summary}

评估结果：
- 评分: {evaluation.get('score', 'N/A')}
- 反馈: {evaluation.get('feedback', '')}
- 配色评价: {evaluation.get('color_feedback', '')}
- 构图评价: {evaluation.get('composition_feedback', '')}

用户反馈: "{user_feedback}"

请根据评估结果和用户反馈，生成具体的修改指令。

返回 JSON（不要包含其他文字）：
{{
  "should_revise": true,
  "commands": ["绘图指令1", "绘图指令2"],
  "explanation": "修改说明"
}}

指令格式：
- "画一个[颜色]的[形状]" - 添加图形
- "画[艺术类型]" - 添加艺术效果
- "画[场景]" - 添加场景
- "撤销" - 撤销上一步
- "清空" - 重新开始

根据用户反馈判断意图：
- 如果用户说"好/可以/不错" → should_revise: false
- 如果用户说"不好/不行/重来" → should_revise: true，给出改进方案
- 如果用户说具体修改（如"改一下颜色"）→ should_revise: true，生成对应指令"""

        system = "你是绘图修改助手。根据评估结果和用户反馈，生成具体的绘图修改指令。只返回 JSON。"

        result = await self._call_llm(prompt, system)
        parsed = self._parse_json(result)
        return parsed if "should_revise" in parsed else {"should_revise": False, "commands": [], "explanation": ""}

    # ============ 用户反馈分析 ============

    async def analyze_feedback(self, user_text: str, evaluation: dict) -> dict:
        """分析用户反馈是接受、拒绝还是具体修改请求"""
        if not self.llm:
            return self._simple_feedback_analysis(user_text)

        prompt = f"""用户说: "{user_text}"
当前评估: 评分{evaluation.get('score', 'N/A')}，{evaluation.get('feedback', '')}

分析用户意图，返回 JSON：
{{
  "action": "accept" 或 "reject" 或 "modify",
  "confidence": 0.9,
  "commands": ["如果是 modify，给出具体指令"]
}}

判断规则：
- "好/可以/不错/就这样/行/没问题/接受" → accept
- "不好/不行/重来/算了/不要/拒绝" → reject
- 具体描述修改内容（如"加个红色的圆"/"改一下颜色"）→ modify"""

        system = "你是用户意图分析助手。判断用户是接受、拒绝还是要求修改。只返回 JSON。"

        result = await self._call_llm(prompt, system)
        parsed = self._parse_json(result)
        return parsed if "action" in parsed else self._simple_feedback_analysis(user_text)

    # ============ 内部方法 ============

    async def _call_llm(self, prompt: str, system: str = "", retries: int = 1) -> str:
        """调用 LLM，带重试"""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        for attempt in range(retries + 1):
            try:
                response = await self.llm.chat(messages)
                if response:
                    return response
            except Exception as e:
                print(f"[DrawingAgent] LLM Error (attempt {attempt + 1}): {e}")
                if attempt < retries:
                    await asyncio.sleep(1 * (attempt + 1))
        return ""

    async def _call_llm_vision(self, prompt: str, image_base64: str, system: str = "") -> str:
        """调用 Vision LLM（多模态）"""
        content = [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_base64}"}},
        ]
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": content})

        response = await self.vision.chat(messages)
        return response if response else ""

    def _parse_json(self, text: str) -> dict:
        """从 LLM 响应中提取 JSON"""
        if not text:
            return {}
        try:
            cleaned = text.strip()
            if cleaned.startswith("```"):
                lines = cleaned.split("\n")
                cleaned = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
            return json.loads(cleaned)
        except json.JSONDecodeError:
            try:
                start = text.find("{")
                end = text.rfind("}") + 1
                if start >= 0 and end > start:
                    return json.loads(text[start:end])
            except Exception:
                pass
            return {}

    def _summarize_shapes(self, canvas_state: dict) -> str:
        """总结画布上的图形分布"""
        shapes = canvas_state.get("shapes", [])
        if not shapes:
            return "空画布"

        type_count: Dict[str, int] = {}
        for s in shapes:
            stype = s.get("type", "unknown")
            type_count[stype] = type_count.get(stype, 0) + 1

        parts = [f"{t}x{c}" for t, c in type_count.items()]
        return ", ".join(parts[:10])

    def _default_evaluation(self) -> dict:
        """默认评估结果（LLM 不可用时）"""
        return {
            "score": 70,
            "feedback": "画作已完成",
            "suggestions": [],
            "color_feedback": "",
            "composition_feedback": "",
        }

    def _simple_feedback_analysis(self, text: str) -> dict:
        """简单反馈分析（LLM 不可用时的回退）"""
        accept_words = ["好", "可以", "不错", "就这样", "行", "没问题", "接受", "满意"]
        reject_words = ["不好", "不行", "重来", "算了", "不要", "拒绝", "不满意"]

        for w in accept_words:
            if w in text:
                return {"action": "accept", "confidence": 0.8, "commands": []}
        for w in reject_words:
            if w in text:
                return {"action": "reject", "confidence": 0.8, "commands": []}

        return {"action": "unknown", "confidence": 0.3, "commands": []}
