"""
需求分析 Agent
"""

from typing import Dict, Any
from .base import BaseAgent, AgentResult
from .state import AgentState, DesignStage


class RequirementAgent(BaseAgent):
    """需求分析 Agent - 理解用户意图和需求"""

    SYSTEM_PROMPT = """你是一个专业的需求分析Agent。你的任务是理解用户的输入，提取设计需求。

分析用户输入，返回JSON格式的需求分析结果：

{
    "intent": "create_design|modify_design|ask_question|export",
    "style": "设计风格（如：minimalist, cyberpunk, luxury, cute, modern等）",
    "mood": "情感氛围（如：professional, playful, elegant, energetic等）",
    "industry": "行业领域（如：tech, food, fashion, education等）",
    "target_users": "目标用户群体",
    "elements": ["需要包含的设计元素列表"],
    "colors": ["偏好颜色"],
    "keywords": ["关键词列表"],
    "confidence": 0.0到1.0的置信度
}

只返回JSON，不要有其他文字。"""

    async def execute(self, state: AgentState, user_input: str = "", **kwargs) -> AgentResult:
        """执行需求分析"""
        try:
            # 构建分析提示
            prompt = self._build_prompt(state, user_input)

            # 调用 LLM 分析
            result = await self._call_llm_json(prompt, self.SYSTEM_PROMPT)

            if not result:
                # 使用默认分析
                result = self._default_analysis(user_input)

            # 更新状态
            state.requirement.original_text = user_input
            state.requirement.intent = result.get("intent", "create_design")
            state.requirement.style = result.get("style", "modern")
            state.requirement.mood = result.get("mood", "professional")
            state.requirement.industry = result.get("industry", "")
            state.requirement.target_users = result.get("target_users", "")
            state.requirement.elements = result.get("elements", [])
            state.requirement.colors = result.get("colors", [])
            state.requirement.keywords = result.get("keywords", [])

            # 更新记忆
            state.memory["last_style"] = state.requirement.style
            state.memory["last_mood"] = state.requirement.mood
            state.memory["last_industry"] = state.requirement.industry

            return AgentResult(
                success=True,
                data={
                    "intent": state.requirement.intent,
                    "style": state.requirement.style,
                    "mood": state.requirement.mood,
                    "industry": state.requirement.industry,
                    "elements": state.requirement.elements,
                    "keywords": state.requirement.keywords,
                    "confidence": result.get("confidence", 0.8),
                },
                message=f"需求分析完成：{state.requirement.intent}",
                next_stage="planning" if state.requirement.intent == "create_design" else None,
            )

        except Exception as e:
            return AgentResult(
                success=False,
                data={},
                message=self._format_error(e),
            )

    def _build_prompt(self, state: AgentState, user_input: str) -> str:
        """构建分析提示"""
        context = ""
        if state.memory:
            context = f"\n历史偏好：风格={state.memory.get('last_style', '')}, 氛围={state.memory.get('last_mood', '')}"

        if state.requirement.original_text:
            context += f"\n之前的输入：{state.requirement.original_text}"

        return f"""分析以下用户输入的设计需求：

用户输入：{user_input}
{context}

请提取设计需求并返回JSON。"""

    def _default_analysis(self, user_input: str) -> Dict[str, Any]:
        """默认分析（LLM不可用时）"""
        # 简单的关键词匹配
        text_lower = user_input.lower()

        # 检测意图
        intent = "create_design"
        if any(w in text_lower for w in ["修改", "调整", "改变", "modify", "change"]):
            intent = "modify_design"
        elif any(w in text_lower for w in ["导出", "下载", "export", "download"]):
            intent = "export"

        # 检测风格
        style = "modern"
        style_keywords = {
            "minimalist": ["简约", "极简", "minimalist"],
            "cyberpunk": ["赛博朋克", "科技感", "cyberpunk", "未来"],
            "luxury": ["奢华", "高端", "luxury", "豪华"],
            "cute": ["可爱", "萌", "cute", "卡哇伊"],
            "chinese": ["中国风", "国潮", "chinese", "传统"],
            "retro": ["复古", "怀旧", "retro", "vintage"],
        }

        for s, keywords in style_keywords.items():
            if any(k in text_lower for k in keywords):
                style = s
                break

        # 提取元素
        elements = []
        element_keywords = ["logo", "海报", "banner", "名片", "图标", "字体"]
        for kw in element_keywords:
            if kw in text_lower:
                elements.append(kw)

        return {
            "intent": intent,
            "style": style,
            "mood": "professional",
            "industry": "",
            "target_users": "",
            "elements": elements,
            "colors": [],
            "keywords": user_input.split()[:5],
            "confidence": 0.6,
        }
