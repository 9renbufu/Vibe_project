"""
Agent 编排器 - 协调所有 Agent 的工作流程
支持思考过程展示、自动优化和记忆系统
"""

from typing import Dict, Any, Optional, Callable, Awaitable
from .state import AgentState, DesignStage
from .base import AgentResult
from .requirement import RequirementAgent
from .planning import PlanningAgent
from .prompt import PromptAgent
from .generation import GenerationAgent
from .critic import CriticAgent
from .revision import RevisionAgent
from .memory import DesignMemoryAgent


class AgentOrchestrator:
    """Agent 编排器"""

    def __init__(self, llm_client=None, image_generator=None):
        self.llm = llm_client
        self.image_gen = image_generator

        # 初始化所有 Agent
        self.requirement_agent = RequirementAgent(llm_client)
        self.planning_agent = PlanningAgent(llm_client)
        self.prompt_agent = PromptAgent(llm_client)
        self.generation_agent = GenerationAgent(llm_client, image_generator)
        self.critic_agent = CriticAgent(llm_client)
        self.revision_agent = RevisionAgent(llm_client)
        self.memory_agent = DesignMemoryAgent(llm_client)

        # 状态
        self.state = AgentState()

        # 回调函数
        self._on_stage_change: Optional[Callable[[str, Dict], Awaitable[None]]] = None
        self._on_agent_result: Optional[Callable[[str, AgentResult], Awaitable[None]]] = None
        self._on_thinking: Optional[Callable[[str, str], Awaitable[None]]] = None

    def set_callbacks(
        self,
        on_stage_change: Optional[Callable[[str, Dict], Awaitable[None]]] = None,
        on_agent_result: Optional[Callable[[str, AgentResult], Awaitable[None]]] = None,
        on_thinking: Optional[Callable[[str, str], Awaitable[None]]] = None,
    ):
        """设置回调函数"""
        self._on_stage_change = on_stage_change
        self._on_agent_result = on_agent_result
        self._on_thinking = on_thinking

    async def _notify_stage_change(self, stage: str, data: Dict = None):
        """通知阶段变化"""
        if self._on_stage_change:
            await self._on_stage_change(stage, data or {})

    async def _notify_agent_result(self, agent_name: str, result: AgentResult):
        """通知 Agent 执行结果"""
        if self._on_agent_result:
            await self._on_agent_result(agent_name, result)

    async def _notify_thinking(self, agent_name: str, thinking: str):
        """通知思考过程"""
        if self._on_thinking:
            await self._on_thinking(agent_name, thinking)

    async def process_input(self, user_input: str) -> Dict[str, Any]:
        """
        处理用户输入的完整流程

        流程：Requirement -> Planning -> Prompt -> Generation -> Critic -> (Revision -> Generation -> Critic)?
        """
        self.state.add_message("user", user_input)

        # 检查是否是修改请求
        if self.state.stage == DesignStage.COMPLETED and self._is_revision_request(user_input):
            return await self._handle_revision(user_input)

        # 检查是否是方案选择
        if self.state.plans and self._is_plan_selection(user_input):
            return await self._handle_plan_selection(user_input)

        # 完整流程
        return await self._full_pipeline(user_input)

    async def _full_pipeline(self, user_input: str) -> Dict[str, Any]:
        """完整设计流程"""
        result = {
            "response": "",
            "stage": "",
            "data": {},
        }

        try:
            # Step 0: 加载记忆
            await self._notify_thinking("MemoryAgent", "正在加载用户设计偏好...")
            memory_injection = self.memory_agent.get_prompt_injection()
            if memory_injection:
                await self._notify_thinking("MemoryAgent", f"已加载用户偏好:\n{memory_injection}")

            # Step 1: 需求分析
            await self._notify_thinking("RequirementAgent", f"正在分析用户输入: '{user_input}'...")
            await self._notify_stage_change("requirement", {"input": user_input})
            self.state.stage = DesignStage.REQUIREMENT

            req_result = await self.requirement_agent.execute(self.state, user_input)
            await self._notify_thinking("RequirementAgent", self._format_requirement_thinking(req_result))
            await self._notify_agent_result("RequirementAgent", req_result)

            if not req_result.success:
                result["response"] = f"需求分析失败：{req_result.message}"
                return result

            # 如果是查询记忆请求
            if req_result.data.get("intent") == "query_memory":
                memory_result = await self.memory_agent.execute(self.state, action="query")
                result["data"]["memory"] = memory_result.data
                result["response"] = "已查询设计记忆"
                result["stage"] = "completed"
                return result

            # 如果是导出请求
            if req_result.data.get("intent") == "export":
                result["response"] = "好的，正在为您导出设计..."
                result["stage"] = "export"
                return result

            # Step 2: 设计规划（注入记忆）
            await self._notify_thinking("PlanningAgent", "基于需求分析和历史偏好，正在生成多个设计方案...")
            await self._notify_stage_change("planning", req_result.data)
            self.state.stage = DesignStage.PLANNING

            # 将记忆注入到状态中供 PlanningAgent 使用
            self.state.memory["injection"] = memory_injection
            plan_result = await self.planning_agent.execute(self.state)
            await self._notify_thinking("PlanningAgent", self._format_plan_thinking(plan_result))
            await self._notify_agent_result("PlanningAgent", plan_result)

            if not plan_result.success:
                result["response"] = f"设计规划失败：{plan_result.message}"
                return result

            result["data"]["plans"] = plan_result.data.get("plans", [])

            # Step 3: 提示词生成（注入记忆）
            await self._notify_thinking("PromptAgent", "正在结合用户偏好生成图像提示词...")
            await self._notify_stage_change("prompt", plan_result.data)
            self.state.stage = DesignStage.GENERATING

            prompt_result = await self.prompt_agent.execute(self.state)
            await self._notify_thinking("PromptAgent", self._format_prompt_thinking(prompt_result))
            await self._notify_agent_result("PromptAgent", prompt_result)

            if not prompt_result.success:
                result["response"] = f"提示词生成失败：{prompt_result.message}"
                return result

            # Step 4: 图像生成
            await self._notify_thinking("GenerationAgent", "正在调用图像生成API，预计需要30-120秒...")
            await self._notify_stage_change("generating", prompt_result.data)

            gen_result = await self.generation_agent.execute(self.state, prompt_result.data)
            await self._notify_thinking("GenerationAgent", "图像生成完成，正在准备评估...")
            await self._notify_agent_result("GenerationAgent", gen_result)

            if not gen_result.success:
                result["response"] = f"图像生成失败：{gen_result.message}"
                return result

            result["data"]["image"] = gen_result.data.get("image")
            result["data"]["version"] = gen_result.data.get("version")

            # Step 5: 设计评估 (Critic Agent)
            await self._notify_thinking("CriticAgent", "正在从4个维度评估设计质量...")
            await self._notify_stage_change("evaluating", gen_result.data)
            self.state.stage = DesignStage.EVALUATING

            critic_result = await self.critic_agent.execute(self.state)
            await self._notify_thinking("CriticAgent", self._format_critic_thinking(critic_result))
            await self._notify_agent_result("CriticAgent", critic_result)

            if critic_result.success:
                result["data"]["evaluation"] = critic_result.data.get("evaluation")
                result["data"]["suggestions"] = critic_result.data.get("suggestions", [])

                # 自动优化：如果评分低于阈值，自动进行修改
                if critic_result.data.get("should_revise"):
                    await self._notify_thinking("CriticAgent", "评分较低，启动自动优化流程...")
                    result["data"]["auto_optimizing"] = True

                    # 自动修改
                    revision_result = await self._auto_optimize(critic_result.data)
                    if revision_result.get("success"):
                        result["data"]["image"] = revision_result.get("image")
                        result["data"]["version"] = revision_result.get("version")
                        result["data"]["evaluation"] = revision_result.get("evaluation")
                        result["data"]["optimized"] = True

            # Step 6: 更新记忆
            await self._notify_thinking("MemoryAgent", "正在更新用户设计偏好...")
            memory_result = await self.memory_agent.execute(self.state, action="update")
            if memory_result.success:
                result["data"]["memory_updated"] = True
                result["data"]["preferences"] = memory_result.data.get("long_term_summary", {})

            # 完成
            self.state.stage = DesignStage.COMPLETED
            result["stage"] = "completed"

            # 生成回复
            result["response"] = self._generate_response(result["data"])

        except Exception as e:
            result["response"] = f"处理过程中出现问题：{str(e)}"
            self.state.stage = DesignStage.ERROR
            self.state.error = str(e)

        self.state.add_message("assistant", result["response"])
        return result

    async def _auto_optimize(self, critic_data: Dict) -> Dict[str, Any]:
        """自动优化流程"""
        if self.state.revision_count >= self.state.MAX_REVISIONS:
            print(f"[Orchestrator] Max revisions ({self.state.MAX_REVISIONS}) reached, skipping auto-optimize")
            return {"success": False}

        try:
            self.state.revision_count += 1
            # 使用建议作为修改意见
            suggestions = critic_data.get("suggestions", [])
            feedback = critic_data.get("feedback", "")
            optimization_input = f"根据评估反馈进行优化：{feedback}。建议：{', '.join(suggestions)}"

            # 修改分析
            await self._notify_thinking("RevisionAgent", f"正在分析优化方向: {optimization_input}")
            self.state.stage = DesignStage.REVISING

            revision_result = await self.revision_agent.execute(self.state, optimization_input)
            await self._notify_agent_result("RevisionAgent", revision_result)

            if not revision_result.success:
                return {"success": False}

            # 重新生成提示词
            await self._notify_thinking("PromptAgent", "正在生成优化后的提示词...")
            prompt_result = await self.prompt_agent.execute(self.state)

            if not prompt_result.success:
                return {"success": False}

            # 重新生成图像
            await self._notify_thinking("GenerationAgent", "正在生成优化后的图像...")
            gen_result = await self.generation_agent.execute(self.state, prompt_result.data)

            if not gen_result.success:
                return {"success": False}

            # 重新评估
            await self._notify_thinking("CriticAgent", "正在评估优化后的设计...")
            critic_result = await self.critic_agent.execute(self.state)

            return {
                "success": True,
                "image": gen_result.data.get("image"),
                "version": gen_result.data.get("version"),
                "evaluation": critic_result.data.get("evaluation") if critic_result.success else None,
            }

        except Exception as e:
            print(f"Auto optimize error: {e}")
            return {"success": False}

    async def _handle_revision(self, user_input: str) -> Dict[str, Any]:
        """处理修改请求"""
        result = {
            "response": "",
            "stage": "revising",
            "data": {},
        }

        # 检查修订次数限制
        if self.state.revision_count >= self.state.MAX_REVISIONS:
            result["response"] = f"已达最大修订次数（{self.state.MAX_REVISIONS}次），如需继续修改请重置会话。"
            result["stage"] = "completed"
            return result

        try:
            self.state.revision_count += 1
            # 修改分析
            await self._notify_thinking("RevisionAgent", f"正在分析用户修改意见: '{user_input}'（第{self.state.revision_count}次修订）")
            await self._notify_stage_change("revising", {"feedback": user_input})
            self.state.stage = DesignStage.REVISING

            revision_result = await self.revision_agent.execute(self.state, user_input)
            await self._notify_thinking("RevisionAgent", self._format_revision_thinking(revision_result))
            await self._notify_agent_result("RevisionAgent", revision_result)

            if not revision_result.success:
                result["response"] = f"修改分析失败：{revision_result.message}"
                return result

            result["data"]["revision"] = revision_result.data

            # 重新生成提示词
            await self._notify_thinking("PromptAgent", "正在根据修改意见调整提示词...")
            prompt_result = await self.prompt_agent.execute(self.state)

            # 重新生成图像
            if prompt_result.success:
                await self._notify_thinking("GenerationAgent", "正在重新生成图像...")
                gen_result = await self.generation_agent.execute(self.state, prompt_result.data)
                if gen_result.success:
                    result["data"]["image"] = gen_result.data.get("image")
                    result["data"]["version"] = gen_result.data.get("version")

                    # 重新评估
                    await self._notify_thinking("CriticAgent", "正在评估修改后的设计...")
                    critic_result = await self.critic_agent.execute(self.state)
                    if critic_result.success:
                        result["data"]["evaluation"] = critic_result.data.get("evaluation")

            self.state.stage = DesignStage.COMPLETED
            result["stage"] = "completed"
            result["response"] = f"已根据您的意见完成修改：{revision_result.data.get('explanation', '')}"

        except Exception as e:
            result["response"] = f"修改过程中出现问题：{str(e)}"

        self.state.add_message("assistant", result["response"])
        return result

    async def _handle_plan_selection(self, user_input: str) -> Dict[str, Any]:
        """处理方案选择"""
        # 简单匹配方案编号
        for i, plan in enumerate(self.state.plans):
            if str(i + 1) in user_input or plan.name in user_input:
                self.state.select_plan(plan.id)
                await self._notify_thinking("PlanningAgent", f"用户选择了方案: {plan.name}")
                return {
                    "response": f"已选择方案：{plan.name}，正在生成设计...",
                    "stage": "selected",
                    "data": {"selected_plan": plan.id},
                }

        # 默认选择第一个
        if self.state.plans:
            self.state.select_plan(self.state.plans[0].id)

        return {
            "response": "请选择一个设计方案",
            "stage": "selecting",
            "data": {"plans": [{"id": p.id, "name": p.name} for p in self.state.plans]},
        }

    def _is_revision_request(self, text: str) -> bool:
        """判断是否是修改请求"""
        revision_keywords = ["修改", "调整", "改变", "换个", "重新", "不满意", "优化", "revision", "modify", "change", "optimize"]
        return any(kw in text.lower() for kw in revision_keywords)

    def _is_plan_selection(self, text: str) -> bool:
        """判断是否是方案选择"""
        if not self.state.plans:
            return False
        # 检查是否包含方案编号
        for i in range(len(self.state.plans)):
            if str(i + 1) in text:
                return True
        return False

    def _format_requirement_thinking(self, result: AgentResult) -> str:
        """格式化需求分析思考过程"""
        if not result.success:
            return f"需求分析失败: {result.message}"
        data = result.data
        return f"""需求分析完成：
- 意图识别: {data.get('intent', '未知')}
- 设计风格: {data.get('style', '未指定')}
- 情感氛围: {data.get('mood', '未指定')}
- 行业领域: {data.get('industry', '未指定')}
- 设计元素: {', '.join(data.get('elements', []))}
- 置信度: {data.get('confidence', 0):.0%}"""

    def _format_plan_thinking(self, result: AgentResult) -> str:
        """格式化设计规划思考过程"""
        if not result.success:
            return f"设计规划失败: {result.message}"
        plans = result.data.get("plans", [])
        lines = [f"生成了 {len(plans)} 个设计方案:"]
        for i, plan in enumerate(plans):
            lines.append(f"  方案{i+1}: {plan.get('name', '')} (评分: {plan.get('score', 0)})")
            lines.append(f"    {plan.get('description', '')[:50]}...")
        return "\n".join(lines)

    def _format_prompt_thinking(self, result: AgentResult) -> str:
        """格式化提示词生成思考过程"""
        if not result.success:
            return f"提示词生成失败: {result.message}"
        prompt = result.data.get("positive_prompt", "")
        return f"""提示词生成完成:
- 正面提示词: {prompt[:100]}...
- 风格关键词: {', '.join(result.data.get('style_keywords', []))}"""

    def _format_critic_thinking(self, result: AgentResult) -> str:
        """格式化评估思考过程"""
        if not result.success:
            return f"评估失败: {result.message}"
        eval_data = result.data.get("evaluation", {})
        suggestions = result.data.get("suggestions", [])
        lines = [
            "设计评估完成:",
            f"  - 品牌一致性: {eval_data.get('brand_consistency', 0)}/100",
            f"  - 创意性: {eval_data.get('creativity', 0)}/100",
            f"  - 商业价值: {eval_data.get('commercial_value', 0)}/100",
            f"  - 视觉冲击力: {eval_data.get('visual_impact', eval_data.get('aesthetics', 0))}/100",
            f"  - 综合评分: {eval_data.get('overall', 0)}/100",
        ]
        if suggestions:
            lines.append("优化建议:")
            for s in suggestions:
                lines.append(f"  - {s}")
        if result.data.get("should_revise"):
            lines.append("评分较低，将自动进行优化...")
        return "\n".join(lines)

    def _format_revision_thinking(self, result: AgentResult) -> str:
        """格式化修改思考过程"""
        if not result.success:
            return f"修改分析失败: {result.message}"
        data = result.data
        return f"""修改分析完成:
- 修改类型: {data.get('revision_type', 'minor')}
- 修改说明: {data.get('explanation', '')}
- 提示词调整: {data.get('prompt_adjustments', '')[:50]}..."""

    def _generate_response(self, data: Dict) -> str:
        """生成回复文本"""
        parts = []

        if data.get("plans"):
            parts.append(f"为您生成了 {len(data['plans'])} 个设计方案")

        if data.get("evaluation"):
            eval_data = data["evaluation"]
            parts.append(f"设计评分：{eval_data.get('overall', 0)}/100")
            if eval_data.get("feedback"):
                parts.append(eval_data["feedback"])

        if data.get("optimized"):
            parts.append("已自动完成优化")

        if data.get("suggestions"):
            parts.append(f"优化建议：{', '.join(data['suggestions'][:3])}")

        if data.get("version"):
            parts.append(f"版本 {data['version']} 已生成")

        if not parts:
            parts.append("设计已完成")

        return "。".join(parts) + "。"

    def get_state(self) -> Dict[str, Any]:
        """获取当前状态"""
        return self.state.to_dict()

    def reset(self):
        """重置状态"""
        self.state = AgentState()
        self.state.revision_count = 0
