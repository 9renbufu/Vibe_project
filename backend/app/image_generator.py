import os
import httpx
import base64
from typing import Optional
from abc import ABC, abstractmethod


class BaseImageGenerator(ABC):
    @abstractmethod
    async def generate(self, prompt: str, size: str = "1024x1024") -> str:
        """Generate image and return base64 encoded image data"""
        pass


class DallEGenerator(BaseImageGenerator):
    def __init__(self, api_key: str, model: str = "dall-e-3", base_url: str = None):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url or "https://api.openai.com/v1"

    async def generate(self, prompt: str, size: str = "1024x1024") -> str:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/images/generations",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "size": size,
                    "quality": "hd",
                    "response_format": "b64_json",
                    "n": 1,
                },
                timeout=120.0,
            )
            response.raise_for_status()
            data = response.json()
            return data["data"][0]["b64_json"]


class QwenImageGenerator(BaseImageGenerator):
    """通义万相 - 阿里云图像生成"""

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def generate(self, prompt: str, size: str = "1024x1024") -> str:
        async with httpx.AsyncClient() as client:
            # 提交任务
            response = await client.post(
                "https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "X-DashScope-Async": "enable",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "wanx-v1",
                    "input": {"prompt": prompt},
                    "parameters": {
                        "size": size.replace("x", "*"),
                        "n": 1,
                    },
                },
                timeout=30.0,
            )
            response.raise_for_status()
            task_id = response.json()["output"]["task_id"]

            # 轮询获取结果
            import asyncio
            for _ in range(60):
                await asyncio.sleep(2)
                result = await client.get(
                    f"https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
                result.raise_for_status()
                task_data = result.json()

                if task_data["output"]["task_status"] == "SUCCEEDED":
                    image_url = task_data["output"]["results"][0]["url"]
                    # 下载图片并转为 base64
                    img_response = await client.get(image_url)
                    img_response.raise_for_status()
                    return base64.b64encode(img_response.content).decode()
                elif task_data["output"]["task_status"] == "FAILED":
                    raise Exception(f"Image generation failed: {task_data}")

            raise Exception("Image generation timeout")


class ZhipuImageGenerator(BaseImageGenerator):
    """智谱 CogView 图像生成"""

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def generate(self, prompt: str, size: str = "1024x1024") -> str:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://open.bigmodel.cn/api/paas/v4/images/generations",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "cogview-3-plus",
                    "prompt": prompt,
                    "size": size,
                    "response_format": "b64_json",
                },
                timeout=120.0,
            )
            response.raise_for_status()
            data = response.json()
            return data["data"][0]["b64_json"]


class ImageGenerator:
    def __init__(self, lazy_init: bool = True):
        self.generator: Optional[BaseImageGenerator] = None
        self._initialized = False
        if not lazy_init:
            self._init_generator()

    def _ensure_initialized(self):
        if not self._initialized:
            self._init_generator()
            self._initialized = True

    def _init_generator(self):
        provider = os.getenv("IMAGE_PROVIDER", "").lower()

        if provider == "dalle" or (not provider and os.getenv("OPENAI_API_KEY")):
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key and api_key != "your_api_key_here":
                base_url = os.getenv("OPENAI_BASE_URL")
                model = os.getenv("DALLE_MODEL", "dall-e-3")
                self.generator = DallEGenerator(api_key, model, base_url)
                print(f"Using DALL-E model: {model}")

        elif provider == "qwen":
            api_key = os.getenv("DASHSCOPE_API_KEY")
            if api_key and api_key != "your_api_key_here":
                self.generator = QwenImageGenerator(api_key)
                print("Using Qwen WanX image model")

        elif provider == "zhipu":
            api_key = os.getenv("ZHIPU_API_KEY")
            if api_key and api_key != "your_api_key_here":
                self.generator = ZhipuImageGenerator(api_key)
                print("Using Zhipu CogView model")

        if not self.generator:
            print("No image generator configured")

    async def generate(self, prompt: str, size: str = "1024x1024") -> Optional[str]:
        self._ensure_initialized()
        if not self.generator:
            return None
        try:
            return await self.generator.generate(prompt, size)
        except Exception as e:
            print(f"Image generation error: {e}")
            return None

    def is_available(self) -> bool:
        self._ensure_initialized()
        return self.generator is not None
