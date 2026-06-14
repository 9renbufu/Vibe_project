"""
Agent 基类
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass
from .state import AgentState


@dataclass
class AgentResult:
    """Agent 执行结果"""
    success: bool
    data: Dict[str, Any]
    message: str = ""
    next_stage: Optional[str] = None


class BaseAgent(ABC):
    """Agent 基类"""

    def __init__(self, llm_client=None):
        self.llm = llm_client
        self.name = self.__class__.__name__

    @abstractmethod
    async def execute(self, state: AgentState, **kwargs) -> AgentResult:
        """执行 Agent 任务"""
        pass

    async def _call_llm(self, prompt: str, system_prompt: str = "", retries: int = 2) -> str:
        """调用 LLM，带重试"""
        if not self.llm:
            return ""

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        for attempt in range(retries + 1):
            try:
                response = await self.llm.chat(messages)
                if response:
                    return response
                print(f"[{self.name}] LLM returned empty response (attempt {attempt + 1})")
            except Exception as e:
                print(f"[{self.name}] LLM Error (attempt {attempt + 1}/{retries + 1}): {e}")

            if attempt < retries:
                await asyncio.sleep(1 * (attempt + 1))

        return ""

    async def _call_llm_with_image(self, prompt: str, image_base64: str, system_prompt: str = "") -> str:
        """调用 LLM，支持图片输入（多模态）。不支持时自动回退纯文本。"""
        if not self.llm:
            return ""

        # 构建多模态消息
        content = [
            {"type": "text", "text": prompt},
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{image_base64}"},
            },
        ]
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": content})

        try:
            response = await self.llm.chat(messages)
            if response:
                return response
        except Exception as e:
            err_msg = str(e)
            # 400 错误说明模型不支持图片，直接回退，不重试
            if "400" in err_msg or "image_url" in err_msg or "unknown variant" in err_msg:
                print(f"[{self.name}] LLM 不支持图片输入，回退到纯文本评估")
            else:
                print(f"[{self.name}] LLM Vision Error: {e}")

        # 回退到纯文本
        return await self._call_llm(prompt, system_prompt, retries=1)

    async def _call_llm_json(self, prompt: str, system_prompt: str = "") -> Dict[str, Any]:
        """调用 LLM 并解析 JSON 响应"""
        import json

        response = await self._call_llm(prompt, system_prompt)
        if not response:
            return {}

        try:
            # 清理响应，提取 JSON
            cleaned = response.strip()
            if cleaned.startswith("```"):
                # 移除 markdown 代码块
                lines = cleaned.split("\n")
                cleaned = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

            return json.loads(cleaned)
        except json.JSONDecodeError:
            # 尝试提取 JSON 部分
            try:
                start = response.find("{")
                end = response.rfind("}") + 1
                if start >= 0 and end > start:
                    return json.loads(response[start:end])
            except:
                pass
            return {}

    def _format_error(self, error: Exception) -> str:
        """格式化错误信息"""
        return f"[{self.name}] Error: {str(error)}"
