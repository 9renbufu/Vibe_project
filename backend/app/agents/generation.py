"""
图像生成 Agent
"""

from typing import Dict, Any
from datetime import datetime
from .base import BaseAgent, AgentResult
from .state import AgentState, DesignStage, DesignVersion


class GenerationAgent(BaseAgent):
    """图像生成 Agent - 调用图像生成API"""

    def __init__(self, llm_client=None, image_generator=None):
        super().__init__(llm_client)
        self.image_gen = image_generator

    async def execute(self, state: AgentState, prompt_data: Dict[str, Any] = None, **kwargs) -> AgentResult:
        """执行图像生成"""
        try:
            if not self.image_gen:
                return AgentResult(
                    success=False,
                    data={},
                    message="图像生成器未配置",
                )

            # 获取提示词
            positive_prompt = prompt_data.get("positive_prompt", "") if prompt_data else ""
            if not positive_prompt:
                return AgentResult(
                    success=False,
                    data={},
                    message="没有生成提示词",
                )

            # 创建新版本
            version = DesignVersion(
                version=len(state.versions) + 1,
                prompt=positive_prompt,
                plan_id=state.current_plan.id if state.current_plan else "",
            )

            # 调用图像生成
            image_base64 = await self.image_gen.generate(positive_prompt)

            if not image_base64:
                return AgentResult(
                    success=False,
                    data={},
                    message="图像生成失败",
                )

            # 更新版本
            version.image_base64 = image_base64
            state.add_version(version)

            return AgentResult(
                success=True,
                data={
                    "image": image_base64,
                    "prompt": positive_prompt,
                    "version": version.version,
                    "version_id": version.id,
                },
                message=f"图像生成完成 (版本 {version.version})",
                next_stage="evaluating",
            )

        except Exception as e:
            return AgentResult(
                success=False,
                data={},
                message=self._format_error(e),
            )
