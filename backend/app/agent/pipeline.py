"""
Agent Pipeline - Agent 流水线
职责：协调各个 Agent 的工作流程
"""

import json
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

from .intent_agent import analyze_intent
from .planner_agent import generate_design_plan
from .prompt_agent import generate_image_prompt, enhance_prompt_for_revision
from .revision_agent import analyze_revision
from .style_library import STYLE_LIBRARY, match_style, match_task_type


@dataclass
class DesignState:
    """设计状态"""
    phase: str = "idle"
    current_plan: Dict[str, Any] = field(default_factory=dict)
    current_prompt: str = ""
    current_image: str = ""
    history: list = field(default_factory=list)
    user_input: str = ""
    intent_result: Dict[str, Any] = field(default_factory=dict)


class DesignPipeline:
    """设计流水线"""

    def __init__(self, llm_client=None, image_generator=None):
        self.llm = llm_client
        self.image_gen = image_generator
        self.state = DesignState()

    async def process_voice_input(self, user_input: str) -> Dict[str, Any]:
        """
        处理语音输入的完整流程

        流程：
        Voice Input → Intent Agent → Planner Agent → Prompt Agent → Image Generator
        """
        self.state.user_input = user_input
        result = {
            "response": "",
            "action": "ask",
            "phase": "processing",
            "image": None,
            "plan": None,
            "intent": None,
        }

        try:
            # Step 1: Intent Analysis
            print(f"[Pipeline] Step 1: Analyzing intent...")
            self.state.phase = "intent"
            intent_result = await analyze_intent(self.llm, user_input)
            self.state.intent_result = intent_result
            result["intent"] = intent_result

            # 检查是否是修改请求
            if intent_result.get("intent") == "modify_design":
                return await self._handle_revision(user_input)

            # 检查是否是导出请求
            if intent_result.get("intent") == "export":
                result["response"] = "好的，正在为您导出设计..."
                result["action"] = "export"
                result["phase"] = "exporting"
                return result

            # Step 2: Design Planning
            print(f"[Pipeline] Step 2: Generating design plan...")
            self.state.phase = "planning"
            design_context = {
                "current_plan": self.state.current_plan,
                "history": self.state.history[-3:] if self.state.history else [],
            }
            plan = await generate_design_plan(
                self.llm, user_input, intent_result, design_context
            )
            self.state.current_plan = plan
            result["plan"] = plan

            # Step 3: Prompt Generation
            print(f"[Pipeline] Step 3: Generating image prompt...")
            self.state.phase = "prompting"
            prompt_result = await generate_image_prompt(self.llm, plan)
            self.state.current_prompt = prompt_result.get("positive_prompt", "")
            result["prompt"] = prompt_result

            # Step 4: Image Generation
            if self.image_gen and self.state.current_prompt:
                print(f"[Pipeline] Step 4: Generating image...")
                self.state.phase = "generating"
                image_data = await self.image_gen.generate(self.state.current_prompt)

                if image_data:
                    self.state.current_image = image_data
                    self.state.history.append({
                        "input": user_input,
                        "plan": plan,
                        "prompt": self.state.current_prompt,
                        "timestamp": datetime.now().isoformat(),
                    })
                    result["image"] = image_data

            # 构建回复
            result["response"] = plan.get("explanation", f"已为您设计完成！")
            result["action"] = "generate"
            result["phase"] = "completed"

        except Exception as e:
            print(f"[Pipeline] Error: {e}")
            result["response"] = f"处理过程中出现问题：{str(e)}"
            result["action"] = "error"
            result["phase"] = "error"

        return result

    async def _handle_revision(self, user_input: str) -> Dict[str, Any]:
        """处理修改请求"""
        self.state.phase = "revising"
        result = {
            "response": "",
            "action": "revise",
            "phase": "revising",
            "image": None,
        }

        try:
            # 分析修改意见
            revision_result = await analyze_revision(
                self.llm,
                user_input,
                self.state.current_plan,
                self.state.current_prompt,
            )

            # 更新 Prompt
            updated_prompt = revision_result.get("updated_prompt", self.state.current_prompt)
            if not updated_prompt:
                updated_prompt = enhance_prompt_for_revision(
                    self.state.current_prompt,
                    user_input,
                )

            self.state.current_prompt = updated_prompt

            # 重新生成图像
            if self.image_gen and updated_prompt:
                print(f"[Pipeline] Regenerating image with revision...")
                self.state.phase = "generating"
                image_data = await self.image_gen.generate(updated_prompt)

                if image_data:
                    self.state.current_image = image_data
                    result["image"] = image_data

            result["response"] = revision_result.get(
                "explanation",
                f"已根据您的要求进行修改：{user_input}"
            )
            result["phase"] = "completed"

        except Exception as e:
            print(f"[Pipeline] Revision error: {e}")
            result["response"] = f"修改过程中出现问题：{str(e)}"

        return result

    def get_state(self) -> Dict[str, Any]:
        """获取当前状态"""
        return {
            "phase": self.state.phase,
            "current_plan": self.state.current_plan,
            "current_prompt": self.state.current_prompt,
            "has_image": bool(self.state.current_image),
            "history_count": len(self.state.history),
            "intent": self.state.intent_result,
        }

    def reset(self):
        """重置状态"""
        self.state = DesignState()
