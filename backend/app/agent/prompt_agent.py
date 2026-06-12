"""
Prompt Generator Agent - 提示词生成代理
职责：将设计方案转换为高质量的图像生成 Prompt
"""

import json
from typing import Dict, Any, List


PROMPT_SYSTEM_PROMPT = """你是一个专业的 AI 绘图提示词专家。将设计方案转换为高质量的图像生成提示词。

## 输入
你会收到设计方案 JSON，包含：
- 任务类型
- 设计风格
- 设计元素
- 配色方案
- 构图方式

## 输出格式
```json
{
    "positive_prompt": "正面提示词（英文）",
    "negative_prompt": "负面提示词（英文）",
    "style_keywords": ["风格关键词"],
    "technical_params": {
        "aspect_ratio": "1:1 | 16:9 | 9:16 | 4:3",
        "quality": "standard | hd",
        "style_preset": "预设风格"
    }
}
```

## Prompt 结构（按顺序）
1. **质量词**：masterpiece, best quality, highly detailed, 4k, professional
2. **类型词**：poster design, logo design, illustration, etc.
3. **风格词**：minimalist, cyberpunk, anime, luxury, etc.
4. **主体描述**：what is the main subject
5. **元素细节**：specific elements and their arrangement
6. **配色描述**：color scheme and palette
7. **构图描述**：layout and composition
8. **光影效果**：lighting and shadows
9. **材质纹理**：textures and materials
10. **背景描述**：background details

## 负面提示词模板
low quality, blurry, distorted, deformed, ugly, bad anatomy,
bad proportions, extra limbs, duplicate, watermark, signature,
text error, misspelling, cropped, out of frame

## 不同任务类型的 Prompt 重点

### Logo
- 强调：simple, memorable, scalable, vector style, iconic
- 避免：complex details, realistic photos

### 海报
- 强调：eye-catching, bold typography, clear hierarchy, visual impact
- 注意：text readability, call to action

### IP 形象
- 强调：cute, memorable, consistent style, character design
- 注意：expressions, poses, brand personality

### UI 界面
- 强调：clean layout, user-friendly, modern, responsive
- 注意：navigation, buttons, content hierarchy

只返回 JSON，不要其他内容。"""


async def generate_image_prompt(
    llm_client,
    design_plan: Dict[str, Any],
) -> Dict[str, Any]:
    """生成图像 Prompt"""
    if not llm_client:
        return _fallback_prompt(design_plan)

    try:
        messages = [
            {"role": "user", "content": f"""
设计方案：
{json.dumps(design_plan, ensure_ascii=False, indent=2)}

请生成高质量的图像生成提示词。
"""}
        ]

        response = await llm_client.chat(messages, PROMPT_SYSTEM_PROMPT)

        # 解析 JSON
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0]
        elif "```" in response:
            response = response.split("```")[1].split("```")[0]

        json_start = response.find("{")
        json_end = response.rfind("}") + 1
        if json_start != -1 and json_end > json_start:
            return json.loads(response[json_start:json_end])

    except Exception as e:
        print(f"Prompt generation error: {e}")

    return _fallback_prompt(design_plan)


def _fallback_prompt(design_plan: Dict[str, Any]) -> Dict[str, Any]:
    """后备 Prompt 生成"""
    parts = []

    # 质量词
    parts.append("masterpiece, best quality, highly detailed, 4k, professional")

    # 任务类型
    task_type = design_plan.get("task_type", "poster")
    task_prompts = {
        "logo": "logo design, vector style, iconic symbol",
        "poster": "poster design, eye-catching, bold composition",
        "banner": "web banner design, clear message",
        "card": "business card design, professional layout",
        "social": "social media graphic, engaging visual",
        "ip": "character design, cute mascot, memorable",
        "ui": "UI design, clean interface, modern",
        "packaging": "packaging design, product presentation",
    }
    parts.append(task_prompts.get(task_type, "design"))

    # 风格
    style = design_plan.get("style", "modern")
    style_keywords = {
        "apple": "Apple style, minimalist, clean white, subtle shadows",
        "minimalist": "minimalist, geometric, simple, clean",
        "cyberpunk": "cyberpunk, neon lights, futuristic, dark",
        "anime": "anime style, vibrant, Japanese illustration",
        "luxury": "luxury, gold and black, elegant, premium",
        "modern": "modern, trendy, gradient, contemporary",
        "chinese": "Chinese traditional, ink wash, red and gold",
        "retro": "retro vintage, muted colors, nostalgic",
        "cartoon": "cartoon style, hand-drawn, playful",
    }
    parts.append(style_keywords.get(style, "modern design"))

    # 元素
    elements = design_plan.get("elements", [])
    if elements:
        element_desc = ", ".join([e.get("description", "") for e in elements[:3] if e.get("description")])
        if element_desc:
            parts.append(element_desc)

    # 配色
    colors = design_plan.get("color_palette", {}).get("palette", [])
    if colors:
        parts.append(f"color scheme: {', '.join(colors[:3])}")

    # 构图
    composition = design_plan.get("composition", {})
    if composition.get("layout"):
        parts.append(f"{composition['layout']} composition")

    positive_prompt = ", ".join(parts)

    negative_prompt = (
        "low quality, blurry, distorted, deformed, ugly, bad anatomy, "
        "bad proportions, extra limbs, duplicate, watermark, signature, "
        "text error, misspelling, cropped, out of frame, worst quality"
    )

    return {
        "positive_prompt": positive_prompt,
        "negative_prompt": negative_prompt,
        "style_keywords": [style],
        "technical_params": {
            "aspect_ratio": "1:1",
            "quality": "hd",
            "style_preset": style,
        }
    }


def enhance_prompt_for_revision(
    original_prompt: str,
    revision_instruction: str,
    design_context: Dict[str, Any] = None,
) -> str:
    """增强修改提示词"""
    parts = [original_prompt]

    # 解析修改指令
    instruction_lower = revision_instruction.lower()

    # 颜色修改
    color_map = {
        "红": "red", "蓝": "blue", "绿": "green", "黄": "yellow",
        "紫": "purple", "橙": "orange", "粉": "pink", "黑": "black",
        "白": "white", "灰": "gray", "金": "gold", "银": "silver",
    }
    for cn, en in color_map.items():
        if cn in instruction_lower:
            parts.append(f"{en} color scheme")

    # 亮度修改
    if any(word in instruction_lower for word in ["亮", "浅", "淡"]):
        parts.append("brighter, lighter colors")
    elif any(word in instruction_lower for word in ["暗", "深"]):
        parts.append("darker, deeper colors")

    # 风格修改
    if "科技" in instruction_lower:
        parts.append("high-tech, futuristic elements")
    if "可爱" in instruction_lower:
        parts.append("cute, kawaii style")
    if "简约" in instruction_lower:
        parts.append("more minimalist, simpler")
    if "复杂" in instruction_lower:
        parts.append("more detailed, intricate")

    # 年轻化
    if "年轻" in instruction_lower:
        parts.append("youthful, trendy, modern")

    # 商务化
    if "商务" in instruction_lower or "专业" in instruction_lower:
        parts.append("professional, business-like")

    return ", ".join(parts)
