"""
Voice Designer Agent - 核心设计代理
负责理解用户需求、规划设计方案、协调各模块完成设计任务
"""

import json
from typing import List, Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime


class DesignPhase(str, Enum):
    """设计阶段"""
    IDLE = "idle"                    # 等待指令
    REQUIREMENT = "requirement"      # 需求收集
    DISCUSSION = "discussion"        # 设计讨论
    PLANNING = "planning"            # 方案规划
    GENERATING = "generating"        # 图像生成
    REVIEWING = "reviewing"          # 方案评审
    REFINING = "refining"            # 修改优化
    EXPORTING = "exporting"          # 导出作品


class DesignStyle(str, Enum):
    """设计风格"""
    FLAT = "flat"                    # 扁平化
    GRADIENT = "gradient"            # 渐变风
    NEON = "neon"                    # 霓虹风
    MINIMAL = "minimal"              # 极简风
    REALISTIC = "realistic"          # 写实风
    CARTOON = "cartoon"              # 卡通风
    CYBERPUNK = "cyberpunk"          # 赛博朋克
    WATERCOLOR = "watercolor"        # 水彩风


@dataclass
class DesignElement:
    """设计元素"""
    name: str
    description: str
    position: str = "center"
    size: str = "medium"
    color: str = ""
    style: str = ""
    z_index: int = 0


@dataclass
class DesignContext:
    """设计上下文"""
    project_name: str = "未命名项目"
    phase: DesignPhase = DesignPhase.IDLE
    style: DesignStyle = DesignStyle.FLAT
    elements: List[DesignElement] = field(default_factory=list)
    color_palette: List[str] = field(default_factory=list)
    requirements: List[str] = field(default_factory=list)
    conversation_history: List[Dict[str, str]] = field(default_factory=list)
    generated_images: List[str] = field(default_factory=list)
    current_image_prompt: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_name": self.project_name,
            "phase": self.phase.value,
            "style": self.style.value,
            "elements": [
                {
                    "name": e.name,
                    "description": e.description,
                    "position": e.position,
                    "size": e.size,
                    "color": e.color,
                    "style": e.style,
                    "z_index": e.z_index,
                }
                for e in self.elements
            ],
            "color_palette": self.color_palette,
            "requirements": self.requirements,
            "conversation_history": self.conversation_history[-10:],  # 只保留最近10条
            "generated_images": self.generated_images[-5:],  # 只保留最近5张
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def add_message(self, role: str, content: str):
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        })
        self.updated_at = datetime.now().isoformat()


class DesignerAgent:
    """设计代理核心类"""

    def __init__(self, llm_client=None, image_generator=None):
        self.llm = llm_client
        self.image_gen = image_generator
        self.context = DesignContext()

    def get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """你是 Voice Designer，一个专业的 AI 设计助手。

## 你的角色
- 专业的平面设计师
- 耐心的设计顾问
- 创意灵感提供者

## 你的能力
1. 理解用户的设计需求（即使描述模糊）
2. 主动询问关键信息（风格、颜色、用途）
3. 提供专业的设计建议
4. 生成高质量的设计方案
5. 根据反馈进行修改

## 设计流程
1. **需求收集**：了解用户想要设计什么
2. **风格确认**：询问或推荐设计风格
3. **元素规划**：确定需要哪些设计元素
4. **配色方案**：确定颜色搭配
5. **生成方案**：创建设计初稿
6. **反馈优化**：根据用户反馈修改

## 沟通原则
- 用中文交流
- 简洁明了，不啰嗦
- 主动提供专业建议
- 遇到模糊需求时主动询问
- 每次回复不超过3句话

## 输出格式
回复 JSON 格式：
{
    "response": "你的回复内容",
    "action": "ask" | "plan" | "generate" | "refine" | "export",
    "phase": "requirement" | "discussion" | "planning" | "generating" | "reviewing" | "refining",
    "elements": [...],
    "image_prompt": "英文图像生成提示词（当需要生成图像时）",
    "style": "flat" | "gradient" | "neon" | "minimal" | "realistic" | "cartoon" | "cyberpunk" | "watercolor",
    "color_palette": ["#hex1", "#hex2", ...]
}

只返回 JSON，不要其他内容。"""

    def get_context_prompt(self) -> str:
        """获取上下文提示词"""
        ctx = self.context
        elements_desc = "\n".join([
            f"- {e.name}: {e.description} ({e.position}, {e.size})"
            for e in ctx.elements
        ]) if ctx.elements else "（暂无）"

        return f"""## 当前设计项目
- 项目名称：{ctx.project_name}
- 当前阶段：{ctx.phase.value}
- 设计风格：{ctx.style.value}
- 配色方案：{', '.join(ctx.color_palette) if ctx.color_palette else '未确定'}

## 已确定的设计元素
{elements_desc}

## 用户需求
{chr(10).join(['- ' + r for r in ctx.requirements]) if ctx.requirements else '（暂无）'}

## 已生成的图像数量：{len(ctx.generated_images)}"""

    async def process_input(self, user_input: str) -> Dict[str, Any]:
        """处理用户输入"""
        self.context.add_message("user", user_input)

        if not self.llm:
            return self._fallback_response(user_input)

        try:
            system_prompt = self.get_system_prompt()
            context_prompt = self.get_context_prompt()

            messages = [
                {"role": "system", "content": system_prompt + "\n\n" + context_prompt},
                *self.context.conversation_history[-6:],  # 最近3轮对话
            ]

            response = await self.llm.chat(messages, system_prompt)
            result = self._parse_response(response)

            # 更新上下文
            if result.get("elements"):
                self._update_elements(result["elements"])

            if result.get("style"):
                try:
                    self.context.style = DesignStyle(result["style"])
                except ValueError:
                    pass

            if result.get("color_palette"):
                self.context.color_palette = result["color_palette"]

            if result.get("phase"):
                try:
                    self.context.phase = DesignPhase(result["phase"])
                except ValueError:
                    pass

            # 保存助手回复
            self.context.add_message("assistant", result.get("response", ""))

            return result

        except Exception as e:
            print(f"Agent error: {e}")
            return self._fallback_response(user_input)

    def _parse_response(self, text: str) -> Dict[str, Any]:
        """解析 LLM 响应"""
        try:
            # 处理 markdown 代码块
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]

            json_start = text.find("{")
            json_end = text.rfind("}") + 1
            if json_start != -1 and json_end > json_start:
                return json.loads(text[json_start:json_end])
        except Exception as e:
            print(f"Parse error: {e}")

        return {
            "response": text[:200],
            "action": "ask",
            "phase": "discussion",
        }

    def _update_elements(self, elements_data: List[Dict]):
        """更新设计元素"""
        for elem_data in elements_data:
            element = DesignElement(
                name=elem_data.get("name", ""),
                description=elem_data.get("description", ""),
                position=elem_data.get("position", "center"),
                size=elem_data.get("size", "medium"),
                color=elem_data.get("color", ""),
                style=elem_data.get("style", ""),
                z_index=elem_data.get("z_index", 0),
            )
            # 更新或添加元素
            existing = next(
                (e for e in self.context.elements if e.name == element.name),
                None
            )
            if existing:
                idx = self.context.elements.index(existing)
                self.context.elements[idx] = element
            else:
                self.context.elements.append(element)

    def _fallback_response(self, user_input: str) -> Dict[str, Any]:
        """无 LLM 时的后备响应"""
        input_lower = user_input.lower()

        # 检测设计类型
        if any(word in input_lower for word in ["海报", "poster"]):
            self.context.requirements.append("海报设计")
            return {
                "response": "好的，我来帮你设计海报。请问是什么主题的海报？需要什么风格？",
                "action": "ask",
                "phase": "requirement",
            }

        if any(word in input_lower for word in ["logo", "标志"]):
            self.context.requirements.append("Logo设计")
            return {
                "response": "好的，我来帮你设计 Logo。请问是给什么品牌或公司设计？",
                "action": "ask",
                "phase": "requirement",
            }

        if any(word in input_lower for word in ["生成", "画", "create", "设计"]):
            return {
                "response": f"收到，我来为你设计。{user_input}",
                "action": "generate",
                "phase": "generating",
                "image_prompt": f"Professional design, {user_input}, high quality, modern style",
            }

        return {
            "response": "我是 Voice Designer，可以帮你进行设计创作。请告诉我你想设计什么？",
            "action": "ask",
            "phase": "idle",
        }

    def reset(self):
        """重置设计上下文"""
        self.context = DesignContext()

    def get_state(self) -> Dict[str, Any]:
        """获取当前状态"""
        return self.context.to_dict()
