"""
LLM 客户端模块 - 支持多种大模型 API
"""

import os
import asyncio
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod


class BaseLLMClient(ABC):
    """LLM 客户端基类"""

    @abstractmethod
    async def chat(self, messages: List[Dict[str, str]], system: str = "") -> str:
        pass


class ClaudeClient(BaseLLMClient):
    """Claude 客户端"""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        from anthropic import Anthropic
        self.client = Anthropic(api_key=api_key, timeout=120.0)
        self.model = model

    async def chat(self, messages: List[Dict[str, str]], system: str = "") -> str:
        response = await asyncio.to_thread(
            self.client.messages.create,
            model=self.model,
            max_tokens=2000,
            system=system,
            messages=messages,
        )
        return response.content[0].text


class OpenAICompatibleClient(BaseLLMClient):
    """OpenAI 兼容客户端（支持 OpenAI、DeepSeek、通义千问等）"""

    def __init__(self, api_key: str, model: str, base_url: str = None):
        from openai import OpenAI
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=120.0,
            max_retries=2,
        )
        self.model = model

    async def chat(self, messages: List[Dict[str, str]], system: str = "") -> str:
        formatted = []
        if system:
            formatted.append({"role": "system", "content": system})
        formatted.extend(messages)

        response = await asyncio.to_thread(
            self.client.chat.completions.create,
            model=self.model,
            messages=formatted,
            max_tokens=2000,
        )
        return response.choices[0].message.content


class LLMClientFactory:
    """LLM 客户端工厂"""

    @staticmethod
    def create() -> Optional[BaseLLMClient]:
        provider = os.getenv("LLM_PROVIDER", "deepseek").lower()

        if provider == "claude":
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if api_key:
                model = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")
                return ClaudeClient(api_key, model)

        elif provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                model = os.getenv("OPENAI_MODEL", "gpt-4o")
                base_url = os.getenv("OPENAI_BASE_URL")
                return OpenAICompatibleClient(api_key, model, base_url)

        elif provider == "deepseek":
            api_key = os.getenv("DEEPSEEK_API_KEY")
            if api_key:
                return OpenAICompatibleClient(
                    api_key=api_key,
                    model="deepseek-chat",
                    base_url="https://api.deepseek.com",
                )

        elif provider == "qwen":
            api_key = os.getenv("DASHSCOPE_API_KEY")
            if api_key:
                model = os.getenv("QWEN_MODEL", "qwen-plus")
                return OpenAICompatibleClient(
                    api_key=api_key,
                    model=model,
                    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                )

        elif provider == "zhipu":
            api_key = os.getenv("ZHIPU_API_KEY")
            if api_key:
                model = os.getenv("ZHIPU_MODEL", "glm-4-flash")
                return OpenAICompatibleClient(
                    api_key=api_key,
                    model=model,
                    base_url="https://open.bigmodel.cn/api/paas/v4",
                )

        elif provider == "moonshot":
            api_key = os.getenv("MOONSHOT_API_KEY")
            if api_key:
                return OpenAICompatibleClient(
                    api_key=api_key,
                    model="moonshot-v1-8k",
                    base_url="https://api.moonshot.cn/v1",
                )

        elif provider == "ollama":
            base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
            model = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
            return OpenAICompatibleClient(
                api_key="ollama",
                model=model,
                base_url=base_url,
            )

        return None
