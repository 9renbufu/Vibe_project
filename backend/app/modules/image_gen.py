"""
图像生成模块 - 支持多种图像生成 API
"""

import os
import httpx
import base64
from typing import Optional
from abc import ABC, abstractmethod


class ImageGenerator(ABC):
    """图像生成器基类"""

    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        """生成图像，返回 base64 编码"""
        pass


class DallEGenerator(ImageGenerator):
    """OpenAI DALL-E / GPT-Image 生成器"""

    def __init__(self, api_key: str, model: str = "dall-e-3", base_url: str = None):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url or "https://api.openai.com/v1"

    async def generate(self, prompt: str, **kwargs) -> str:
        size = kwargs.get("size", "1024x1024")

        # 构建请求参数
        payload = {
            "model": self.model,
            "prompt": prompt,
            "n": 1,
        }

        # gpt-image-2 系列模型参数
        if "gpt-image" in self.model:
            # gpt-image-2 生成较慢，使用较小尺寸避免代理超时
            if size == "1024x1024":
                size = "512x512"
            payload["size"] = size
        else:
            # dall-e-3 参数
            quality = os.getenv("DALLE_QUALITY", "standard")
            payload["size"] = size
            payload["quality"] = quality
            payload["response_format"] = "b64_json"

        # gpt-image-2 生成较慢，使用 5 分钟超时
        timeout = 300.0 if "gpt-image" in self.model else 180.0

        async with httpx.AsyncClient() as client:
            print(f"[DallE] Generating with model={self.model}, size={size}, timeout={timeout}s")

            response = await client.post(
                f"{self.base_url}/images/generations",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=timeout,
            )

            print(f"[DallE] Response status: {response.status_code}")

            if response.status_code != 200:
                error_text = response.text
                print(f"[DallE] Error {response.status_code}: {error_text}")
                # 如果 b64_json 失败，尝试不带 response_format
                if "response_format" in payload and response.status_code == 400:
                    payload.pop("response_format", None)
                    response = await client.post(
                        f"{self.base_url}/images/generations",
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json",
                        },
                        json=payload,
                        timeout=timeout,
                    )

            response.raise_for_status()
            data = response.json()
            image_data = data["data"][0]

            # 处理不同的返回格式
            if "b64_json" in image_data:
                return image_data["b64_json"]
            elif "url" in image_data:
                # 下载图片并转为 base64
                img_response = await client.get(image_data["url"], timeout=60.0)
                img_response.raise_for_status()
                import base64 as b64
                return b64.b64encode(img_response.content).decode()
            else:
                raise Exception(f"Unknown response format: {image_data}")


class QwenImageGenerator(ImageGenerator):
    """通义万相生成器"""

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def generate(self, prompt: str, **kwargs) -> str:
        import asyncio

        async with httpx.AsyncClient() as client:
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
                    "parameters": {"size": "1024*1024", "n": 1},
                },
                timeout=30.0,
            )
            response.raise_for_status()
            task_id = response.json()["output"]["task_id"]

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
                    img_response = await client.get(image_url, timeout=60.0)
                    img_response.raise_for_status()
                    return base64.b64encode(img_response.content).decode()
                elif task_data["output"]["task_status"] == "FAILED":
                    raise Exception(f"Image generation failed")

            raise Exception("Image generation timeout")


class ZhipuImageGenerator(ImageGenerator):
    """智谱 CogView 生成器"""

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def generate(self, prompt: str, **kwargs) -> str:
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
                    "size": "1024x1024",
                    "response_format": "b64_json",
                },
                timeout=120.0,
            )
            response.raise_for_status()
            return response.json()["data"][0]["b64_json"]


class ImageGeneratorFactory:
    """图像生成器工厂"""

    @staticmethod
    def create() -> Optional[ImageGenerator]:
        provider = os.getenv("IMAGE_PROVIDER", "").lower()

        if provider == "dalle" or (not provider and os.getenv("OPENAI_API_KEY")):
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key and api_key != "your_api_key_here":
                base_url = os.getenv("OPENAI_BASE_URL")
                model = os.getenv("DALLE_MODEL", "dall-e-3")
                return DallEGenerator(api_key, model, base_url)

        elif provider == "qwen":
            api_key = os.getenv("DASHSCOPE_API_KEY")
            if api_key and api_key != "your_api_key_here":
                return QwenImageGenerator(api_key)

        elif provider == "zhipu":
            api_key = os.getenv("ZHIPU_API_KEY")
            if api_key and api_key != "your_api_key_here":
                return ZhipuImageGenerator(api_key)

        return None
