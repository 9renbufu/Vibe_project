"""
设计规划 Agent
"""

from typing import Dict, Any, List
from .base import BaseAgent, AgentResult
from .state import AgentState, DesignStage, DesignPlan


class PlanningAgent(BaseAgent):
    """设计规划 Agent - 生成多个设计方案"""

    SYSTEM_PROMPT = """你是一个专业的设计规划Agent。根据用户需求，生成3个不同的设计方案。

返回JSON格式：

{
    "plans": [
        {
            "name": "方案名称",
            "description": "详细描述",
            "style": "设计风格",
            "elements": ["设计元素列表"],
            "color_palette": ["配色方案"],
            "mood": "情感氛围",
            "composition": "构图说明",
            "score": 0到100的预估评分
        }
    ],
    "recommendation": "推荐的方案索引(0-2)",
    "reasoning": "推荐理由"
}

只返回JSON，不要有其他文字。"""

    async def execute(self, state: AgentState, **kwargs) -> AgentResult:
        """执行设计规划"""
        try:
            # 构建规划提示
            prompt = self._build_prompt(state)

            # 调用 LLM 生成方案
            result = await self._call_llm_json(prompt, self.SYSTEM_PROMPT)

            if not result or "plans" not in result:
                # 使用默认方案
                plans = self._default_plans(state)
            else:
                plans = self._parse_plans(result["plans"])

            # 更新状态
            state.plans = plans
            recommendation = result.get("recommendation", 0)
            if 0 <= recommendation < len(plans):
                state.select_plan(plans[recommendation].id)

            return AgentResult(
                success=True,
                data={
                    "plans": [
                        {
                            "id": p.id,
                            "name": p.name,
                            "description": p.description,
                            "style": p.style,
                            "elements": p.elements,
                            "score": p.score,
                            "selected": p.selected,
                        }
                        for p in plans
                    ],
                    "recommendation": recommendation,
                    "reasoning": result.get("reasoning", ""),
                },
                message=f"生成了 {len(plans)} 个设计方案",
                next_stage="generating",
            )

        except Exception as e:
            return AgentResult(
                success=False,
                data={},
                message=self._format_error(e),
            )

    def _build_prompt(self, state: AgentState) -> str:
        """构建规划提示"""
        req = state.requirement
        memory_context = ""

        if state.memory.get("preferred_styles"):
            memory_context = f"\n用户偏好风格：{state.memory['preferred_styles']}"

        return f"""根据以下设计需求，生成3个不同的设计方案：

原始输入：{req.original_text}
意图：{req.intent}
风格偏好：{req.style}
情感氛围：{req.mood}
行业领域：{req.industry}
目标用户：{req.target_users}
设计元素：{', '.join(req.elements)}
颜色偏好：{', '.join(req.colors)}
关键词：{', '.join(req.keywords)}
{memory_context}

请生成3个有差异的设计方案，每个方案都要有独特的创意角度。"""

    def _parse_plans(self, plans_data: List[Dict]) -> List[DesignPlan]:
        """解析方案数据"""
        result = []
        for i, plan_data in enumerate(plans_data):
            plan = DesignPlan(
                name=plan_data.get("name", f"方案 {i + 1}"),
                description=plan_data.get("description", ""),
                style=plan_data.get("style", ""),
                elements=plan_data.get("elements", []),
                color_palette=plan_data.get("color_palette", []),
                mood=plan_data.get("mood", ""),
                composition=plan_data.get("composition", ""),
                score=plan_data.get("score", 70),
            )
            result.append(plan)
        return result

    def _default_plans(self, state: AgentState) -> List[DesignPlan]:
        """默认方案（LLM不可用时）"""
        req = state.requirement
        style = req.style or "modern"

        plans = [
            DesignPlan(
                name=f"{style.title()} 经典方案",
                description=f"采用经典{style}风格，注重视觉平衡和专业感",
                style=style,
                elements=req.elements or ["主要图形", "文字排版", "装饰元素"],
                color_palette=req.colors or ["#3B82F6", "#1E40AF", "#FFFFFF"],
                mood=req.mood or "professional",
                composition="居中构图，主次分明",
                score=75,
            ),
            DesignPlan(
                name=f"{style.title()} 创意方案",
                description=f"突破传统的{style}风格，加入创新元素和动态感",
                style=style,
                elements=req.elements or ["抽象图形", "渐变色彩", "几何元素"],
                color_palette=["#8B5CF6", "#EC4899", "#F59E0B"],
                mood="creative",
                composition="不对称构图，富有动感",
                score=80,
            ),
            DesignPlan(
                name=f"{style.title()} 极简方案",
                description=f"极简主义{style}风格，用最少元素传达最强信息",
                style="minimalist",
                elements=["核心图形", "简洁文字", "留白"],
                color_palette=["#111827", "#6B7280", "#F9FAFB"],
                mood="clean",
                composition="大量留白，聚焦核心",
                score=70,
            ),
        ]

        # 根据需求调整
        if req.industry:
            for plan in plans:
                plan.elements.insert(0, f"{req.industry}相关元素")

        return plans
