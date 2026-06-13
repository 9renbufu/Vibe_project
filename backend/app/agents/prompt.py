"""
提示词生成 Agent
"""

from typing import Dict, Any
from .base import BaseAgent, AgentResult
from .state import AgentState, DesignStage


class PromptAgent(BaseAgent):
    """提示词生成 Agent - 生成高质量的图像生成提示词"""

    SYSTEM_PROMPT = """你是一个专业的提示词工程师。根据设计方案，生成高质量的图像生成提示词。

关键要求：positive_prompt 必须以艺术媒介风格开头（如 "digital illustration," "watercolor painting," "flat vector art," "hand-drawn sketch," 等），
然后才是具体内容描述。这确保生成的图片有明确的艺术质感，而不是 AI 默认的写实风格。

返回JSON格式：

{
    "positive_prompt": "艺术媒介风格, 详细的正面提示词，包含风格、元素、构图、色彩等描述",
    "negative_prompt": "负面提示词，描述要避免的内容",
    "style_keywords": ["艺术媒介", "风格关键词列表"],
    "technical_params": {
        "aspect_ratio": "1:1 或 16:9 或 9:16",
        "quality": "high 或 standard"
    }
}

提示词应该：
1. 以艺术媒介风格开头（如 illustration, painting, vector art 等）
2. 详细但不冗长
3. 包含具体的视觉描述和画面质感
4. 使用专业的设计术语
5. 考虑构图和色彩搭配

只返回JSON，不要有其他文字。"""

    async def execute(self, state: AgentState, **kwargs) -> AgentResult:
        """执行提示词生成"""
        try:
            # 获取当前方案
            plan = state.current_plan
            if not plan:
                return AgentResult(
                    success=False,
                    data={},
                    message="没有选择设计方案",
                )

            # 构建提示词生成提示
            prompt = self._build_prompt(state, plan)

            # 调用 LLM 生成提示词
            result = await self._call_llm_json(prompt, self.SYSTEM_PROMPT)

            if not result or "positive_prompt" not in result:
                # 使用默认提示词
                result = self._default_prompt(state, plan)

            # 保存提示词到当前版本
            if state.current_version:
                state.current_version.prompt = result["positive_prompt"]

            return AgentResult(
                success=True,
                data={
                    "positive_prompt": result["positive_prompt"],
                    "negative_prompt": result.get("negative_prompt", ""),
                    "style_keywords": result.get("style_keywords", []),
                    "technical_params": result.get("technical_params", {}),
                },
                message="提示词生成完成",
                next_stage="generating",
            )

        except Exception as e:
            return AgentResult(
                success=False,
                data={},
                message=self._format_error(e),
            )

    def _build_prompt(self, state: AgentState, plan) -> str:
        """构建提示词生成提示"""
        req = state.requirement
        revision_context = ""

        # 如果是修改，加入修改意见
        if state.stage == DesignStage.REVISING and state.conversation_history:
            last_messages = [m for m in state.conversation_history[-3:] if m["role"] == "user"]
            if last_messages:
                revision_context = f"\n用户修改意见：{last_messages[-1]['content']}"

        # 匹配风格库
        from ..agent.style_library import match_style, STYLE_LIBRARY
        matched_style_id = match_style(plan.style + " " + req.original_text)
        style_ref = STYLE_LIBRARY.get(matched_style_id, {})
        style_prompt_ref = style_ref.get("prompt", "")

        return f"""根据以下设计方案，生成图像生成提示词：

设计方案：
- 名称：{plan.name}
- 描述：{plan.description}
- 风格：{plan.style}
- 元素：{', '.join(plan.elements)}
- 配色：{', '.join(plan.color_palette)}
- 氛围：{plan.mood}
- 构图：{plan.composition}

用户原始需求：{req.original_text}
行业：{req.industry}
目标用户：{req.target_users}
{revision_context}

风格参考：{style_prompt_ref}

重要：positive_prompt 必须以方案中的艺术媒介风格开头（如 "{plan.style}"），确保画面有手绘/插画/绘画质感，而非 AI 默认写实风格。
请生成详细的图像生成提示词。"""

    def _default_prompt(self, state: AgentState, plan) -> Dict[str, Any]:
        """默认提示词（LLM不可用时）"""
        parts = []

        # 风格描述
        if plan.style:
            style_map = {
                "minimalist": "minimalist style, clean lines, simple composition",
                "cyberpunk": "cyberpunk style, neon lights, futuristic, high-tech",
                "luxury": "luxury style, elegant, premium, sophisticated",
                "cute": "cute style, kawaii, playful, colorful",
                "modern": "modern style, contemporary, sleek, professional",
                "chinese": "Chinese style, traditional elements, cultural motifs",
            }
            parts.append(style_map.get(plan.style, f"{plan.style} style"))

        # 元素描述
        if plan.elements:
            parts.append(f"featuring {', '.join(plan.elements)}")

        # 氛围描述
        if plan.mood:
            mood_map = {
                "professional": "professional atmosphere",
                "creative": "creative and innovative",
                "elegant": "elegant and refined",
                "energetic": "dynamic and energetic",
            }
            parts.append(mood_map.get(plan.mood, plan.mood))

        # 构图描述
        if plan.composition:
            parts.append(plan.composition)

        # 色彩描述
        if plan.color_palette:
            parts.append(f"color palette: {', '.join(plan.color_palette)}")

        positive_prompt = ", ".join(parts)
        if not positive_prompt:
            positive_prompt = f"high quality {plan.name} design"

        # 添加质量描述
        positive_prompt += ", high quality, detailed, professional design"

        negative_prompt = "low quality, blurry, distorted, ugly, bad anatomy, watermark, text, signature"

        return {
            "positive_prompt": positive_prompt,
            "negative_prompt": negative_prompt,
            "style_keywords": [plan.style] if plan.style else [],
            "technical_params": {
                "aspect_ratio": "1:1",
                "quality": "high",
            },
        }
