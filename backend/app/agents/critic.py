"""
设计评估 Agent (Critic) - 增强版
支持自我反思和自动优化建议
"""

from typing import Dict, Any, List
from .base import BaseAgent, AgentResult
from .state import AgentState, DesignStage, Evaluation


class CriticAgent(BaseAgent):
    """设计评估 Agent - 评估生成的设计质量"""

    def __init__(self, llm_client=None, vision_client=None):
        super().__init__(llm_client)
        self.vision = vision_client

    SYSTEM_PROMPT = """你是一个专业的设计评估Agent。你的任务是全面评估生成的设计质量。

评估维度（每项0-100分）：
1. brand_consistency - 品牌一致性：设计是否符合品牌调性和行业特征
2. creativity - 创意性：设计是否有独特的创意和视觉表达
3. commercial_value - 商业价值：设计是否具有商业吸引力和市场潜力
4. visual_impact - 视觉冲击力：设计的视觉效果和第一印象

你需要：
1. 仔细分析设计方案的每个元素
2. 识别设计中的优点和不足
3. 给出具体可执行的优化建议
4. 判断是否需要重新生成

返回JSON格式：

{
    "brand_consistency": 90,
    "creativity": 88,
    "commercial_value": 85,
    "visual_impact": 92,
    "overall": 89,
    "feedback": "整体评价，2-3句话",
    "strengths": ["优点1", "优点2"],
    "weaknesses": ["不足1", "不足2"],
    "suggestions": [
        "具体优化建议1（如：字体过细，建议加粗）",
        "具体优化建议2（如：色彩层级不足，建议增加对比度）",
        "具体优化建议3（如：品牌识别度不足，建议增加标志性元素）"
    ],
    "detailed_analysis": {
        "typography": "字体评估",
        "color": "色彩评估",
        "composition": "构图评估",
        "branding": "品牌元素评估"
    },
    "should_revise": false,
    "revision_priority": "low|medium|high"
}

只返回JSON，不要有其他文字。"""

    async def execute(self, state: AgentState, **kwargs) -> AgentResult:
        """执行设计评估"""
        try:
            # 获取当前版本
            current_version = state.current_version
            if not current_version:
                return AgentResult(
                    success=False,
                    data={},
                    message="没有可评估的设计版本",
                )

            # 构建评估提示
            prompt = self._build_prompt(state)
            image_base64 = current_version.image_base64

            # 优先使用 vision 模型进行图片评估
            if image_base64 and self.vision:
                print(f"[CriticAgent] 使用 Vision 模型进行图片评估")
                response = await self._call_vision(prompt, image_base64)
                result = self._parse_json_response(response)
            elif image_base64:
                # 没有 vision 模型，尝试主 LLM（可能不支持图片）
                print(f"[CriticAgent] 无 Vision 模型，使用纯文本评估")
                result = await self._call_llm_json(prompt, self.SYSTEM_PROMPT)
            else:
                result = await self._call_llm_json(prompt, self.SYSTEM_PROMPT)

            if not result or "overall" not in result:
                # 使用默认评估
                result = self._default_evaluation(state)

            # 更新评估状态
            evaluation = Evaluation(
                brand_consistency=result.get("brand_consistency", 70),
                creativity=result.get("creativity", 70),
                commercial_value=result.get("commercial_value", 70),
                aesthetics=result.get("visual_impact", result.get("aesthetics", 70)),
                overall=result.get("overall", 70),
                feedback=result.get("feedback", ""),
                suggestions=result.get("suggestions", []),
            )
            state.evaluation = evaluation

            # 保存评估到版本
            current_version.evaluation = {
                "overall": evaluation.overall,
                "feedback": evaluation.feedback,
                "scores": {
                    "brand_consistency": evaluation.brand_consistency,
                    "creativity": evaluation.creativity,
                    "commercial_value": evaluation.commercial_value,
                    "visual_impact": result.get("visual_impact", evaluation.aesthetics),
                }
            }

            # 判断是否需要修改
            should_revise = result.get("should_revise", False) or evaluation.overall < 65
            revision_priority = result.get("revision_priority", "low")
            if evaluation.overall < 50:
                revision_priority = "high"
            elif evaluation.overall < 65:
                revision_priority = "medium"

            return AgentResult(
                success=True,
                data={
                    "evaluation": {
                        "brand_consistency": evaluation.brand_consistency,
                        "creativity": evaluation.creativity,
                        "commercial_value": evaluation.commercial_value,
                        "visual_impact": result.get("visual_impact", evaluation.aesthetics),
                        "overall": evaluation.overall,
                        "feedback": evaluation.feedback,
                    },
                    "strengths": result.get("strengths", []),
                    "weaknesses": result.get("weaknesses", []),
                    "suggestions": result.get("suggestions", []),
                    "detailed_analysis": result.get("detailed_analysis", {}),
                    "should_revise": should_revise,
                    "revision_priority": revision_priority,
                },
                message=self._format_evaluation_message(result),
                next_stage="revising" if should_revise else "completed",
            )

        except Exception as e:
            return AgentResult(
                success=False,
                data={},
                message=self._format_error(e),
            )

    def _build_prompt(self, state: AgentState) -> str:
        """构建评估提示"""
        req = state.requirement
        plan = state.current_plan
        version = state.current_version

        plan_info = ""
        if plan:
            plan_info = f"""
设计方案：
- 名称：{plan.name}
- 描述：{plan.description}
- 风格：{plan.style}
- 元素：{', '.join(plan.elements)}
- 配色：{', '.join(plan.color_palette)}
- 氛围：{plan.mood}
- 构图：{plan.composition}
"""

        # 获取历史评估作为参考
        history_context = ""
        if state.versions:
            prev_evals = [v.evaluation for v in state.versions[:-1] if v.evaluation]
            if prev_evals:
                last_eval = prev_evals[-1]
                history_context = f"""
之前的评估结果：
- 评分：{last_eval.get('overall', 'N/A')}
- 反馈：{last_eval.get('feedback', 'N/A')}
请对比分析改进情况。"""

        return f"""请全面评估以下设计：

用户需求：{req.original_text}
风格偏好：{req.style}
行业领域：{req.industry}
目标用户：{req.target_users}
{plan_info}
生成提示词：{version.prompt if version else ''}
{history_context}

请从品牌一致性、创意性、商业价值、视觉冲击力四个维度进行详细评估，
并给出具体的优化建议（如：字体过细、色彩层级不足、品牌识别度不足等）。"""

    async def _call_vision(self, prompt: str, image_base64: str) -> str:
        """使用 vision 模型进行图片评估"""
        content = [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_base64}"}},
        ]
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": content},
        ]
        try:
            response = await self.vision.chat(messages)
            return response or ""
        except Exception as e:
            print(f"[CriticAgent] Vision 评估失败: {e}")
            return ""

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """解析 LLM 返回的 JSON"""
        import json
        if not response:
            return {}
        try:
            cleaned = response.strip()
            if cleaned.startswith("```"):
                lines = cleaned.split("\n")
                cleaned = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
            return json.loads(cleaned)
        except (json.JSONDecodeError, Exception):
            try:
                start = response.find("{")
                end = response.rfind("}") + 1
                if start >= 0 and end > start:
                    return json.loads(response[start:end])
            except:
                pass
            return {}

    def _default_evaluation(self, state: AgentState) -> Dict[str, Any]:
        """默认评估（LLM不可用时）"""
        # 基于方案评分的默认评估
        base_score = 70
        if state.current_plan:
            base_score = state.current_plan.score or 70

        # 根据需求复杂度调整
        req = state.requirement
        complexity_bonus = 0
        if req.elements:
            complexity_bonus += len(req.elements) * 2
        if req.style:
            complexity_bonus += 5

        final_score = min(base_score + complexity_bonus, 95)

        return {
            "brand_consistency": final_score + 3,
            "creativity": final_score - 2,
            "commercial_value": final_score - 5,
            "visual_impact": final_score + 5,
            "overall": final_score,
            "feedback": f"设计方案整体符合{req.style or '现代'}风格要求，视觉效果{'良好' if final_score >= 75 else '尚可'}。",
            "strengths": [
                "风格表达清晰",
                "构图合理",
            ],
            "weaknesses": [
                "细节可以进一步优化",
            ],
            "suggestions": [
                "可以尝试调整字体粗细以增强可读性",
                "考虑增加色彩对比度以提升视觉冲击力",
                "可以加入更多品牌标志性元素以增强识别度",
            ],
            "detailed_analysis": {
                "typography": "字体选择合适，建议适当加粗",
                "color": "配色协调，建议增加对比度",
                "composition": "构图平衡，主次分明",
                "branding": "品牌元素基本到位，可增加标志性符号",
            },
            "should_revise": final_score < 65,
            "revision_priority": "high" if final_score < 50 else ("medium" if final_score < 65 else "low"),
        }

    def _format_evaluation_message(self, result: Dict) -> str:
        """格式化评估消息"""
        overall = result.get("overall", 0)
        suggestions = result.get("suggestions", [])

        parts = [f"设计评估完成，综合评分：{overall}/100"]

        if suggestions:
            parts.append(f"主要建议：{suggestions[0]}")

        if result.get("should_revise"):
            priority = result.get("revision_priority", "medium")
            if priority == "high":
                parts.append("评分较低，建议重新生成")
            else:
                parts.append("有待优化，可选择自动优化")

        return "。".join(parts)
