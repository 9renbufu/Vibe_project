"""
设计修改 Agent
"""

from typing import Dict, Any
from .base import BaseAgent, AgentResult
from .state import AgentState, DesignStage


class RevisionAgent(BaseAgent):
    """设计修改 Agent - 根据反馈修改设计"""

    SYSTEM_PROMPT = """你是一个专业的设计修改Agent。根据评估反馈和用户意见，修改设计方案。

分析修改需求，返回JSON格式：

{
    "revision_type": "minor|major|complete",
    "updated_plan": {
        "name": "修改后的方案名称",
        "description": "修改后的描述",
        "style": "风格",
        "elements": ["修改后的元素"],
        "color_palette": ["修改后的配色"],
        "mood": "修改后的氛围"
    },
    "prompt_adjustments": "对提示词的调整建议",
    "explanation": "修改说明"
}

只返回JSON，不要有其他文字。"""

    async def execute(self, state: AgentState, user_feedback: str = "", **kwargs) -> AgentResult:
        """执行设计修改"""
        try:
            # 构建修改提示
            prompt = self._build_prompt(state, user_feedback)

            # 调用 LLM 生成修改方案
            result = await self._call_llm_json(prompt, self.SYSTEM_PROMPT)

            if not result:
                return AgentResult(
                    success=False,
                    data={},
                    message="无法生成修改方案",
                )

            # 更新方案
            revision_type = result.get("revision_type", "minor")
            updated_plan_data = result.get("updated_plan", {})

            if state.current_plan and updated_plan_data:
                plan = state.current_plan
                plan.name = updated_plan_data.get("name", plan.name)
                plan.description = updated_plan_data.get("description", plan.description)
                plan.style = updated_plan_data.get("style", plan.style)
                plan.elements = updated_plan_data.get("elements", plan.elements)
                plan.color_palette = updated_plan_data.get("color_palette", plan.color_palette)
                plan.mood = updated_plan_data.get("mood", plan.mood)

            # 记录修改历史
            if state.current_version:
                state.current_version.changes.append(
                    f"{revision_type}: {result.get('explanation', '')}"
                )

            return AgentResult(
                success=True,
                data={
                    "revision_type": revision_type,
                    "updated_plan": {
                        "id": state.current_plan.id if state.current_plan else "",
                        "name": state.current_plan.name if state.current_plan else "",
                        "description": state.current_plan.description if state.current_plan else "",
                        "elements": state.current_plan.elements if state.current_plan else [],
                    },
                    "prompt_adjustments": result.get("prompt_adjustments", ""),
                    "explanation": result.get("explanation", ""),
                },
                message=f"设计修改完成 ({revision_type})",
                next_stage="generating",
            )

        except Exception as e:
            return AgentResult(
                success=False,
                data={},
                message=self._format_error(e),
            )

    def _build_prompt(self, state: AgentState, user_feedback: str) -> str:
        """构建修改提示"""
        req = state.requirement
        plan = state.current_plan
        evaluation = state.evaluation

        eval_info = ""
        if evaluation:
            eval_info = f"""
当前评估：
- 总分：{evaluation.overall}
- 反馈：{evaluation.feedback}
- 建议：{', '.join(evaluation.suggestions)}
"""

        plan_info = ""
        if plan:
            plan_info = f"""
当前方案：
- 名称：{plan.name}
- 描述：{plan.description}
- 元素：{', '.join(plan.elements)}
- 配色：{', '.join(plan.color_palette)}
"""

        return f"""根据以下信息修改设计方案：

用户原始需求：{req.original_text}
用户反馈：{user_feedback}
{eval_info}
{plan_info}

请分析需要修改的内容并提供修改方案。"""
