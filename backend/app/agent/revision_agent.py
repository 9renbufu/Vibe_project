"""
Design Revision Agent - 设计修改代理
职责：理解用户修改意见，生成修改方案
"""

import json
from typing import Dict, Any, List


REVISION_SYSTEM_PROMPT = """你是一个设计修改专家。理解用户的修改意见，生成具体的修改方案。

## 输入
你会收到：
1. 用户修改意见
2. 当前设计方案
3. 当前图像 Prompt

## 输出格式
```json
{
    "revision_type": "修改类型",
    "understanding": "你对修改意见的理解（中文）",
    "changes": [
        {
            "target": "修改目标（元素/整体/配色/构图）",
            "action": "具体动作",
            "description": "修改描述",
            "prompt_addition": "添加到 Prompt 的内容",
            "prompt_removal": "需要从 Prompt 移除的内容"
        }
    ],
    "updated_prompt": "更新后的完整 Prompt",
    "explanation": "给用户的中文解释"
}
```

## 修改类型
- color: 颜色调整
- style: 风格调整
- element: 元素增删改
- composition: 构图调整
- mood: 氛围调整
- detail: 细节调整
- scale: 大小调整
- text: 文字调整

## 常见修改指令解析

### 颜色相关
- "颜色更亮" → brighter, more vibrant colors
- "颜色更暗" → darker, deeper tones
- "换成红色" → red color scheme, change primary color to red
- "加点蓝色" → add blue accents
- "配色太花" → simpler color palette, fewer colors

### 风格相关
- "更简约" → more minimalist, simplify
- "更科技" → more high-tech, futuristic
- "更可爱" → cuter, kawaii style
- "更商务" → more professional, business-like
- "更年轻" → more youthful, trendy

### 元素相关
- "加个图标" → add an icon element
- "去掉背景" → remove background, transparent
- "字体大一点" → larger typography, bigger text
- "加个阴影" → add shadow effect
- "加个边框" → add border, frame

### 构图相关
- "居中" → center alignment
- "靠左" → left alignment
- "留白多一点" → more whitespace, negative space
- "紧凑一点" → tighter composition

只返回 JSON，不要其他内容。"""


async def analyze_revision(
    llm_client,
    user_input: str,
    current_plan: Dict[str, Any] = None,
    current_prompt: str = None,
) -> Dict[str, Any]:
    """分析修改意见"""
    if not llm_client:
        return _fallback_revision(user_input, current_prompt)

    try:
        context = ""
        if current_plan:
            context += f"\n当前设计方案：\n{json.dumps(current_plan, ensure_ascii=False, indent=2)}"
        if current_prompt:
            context += f"\n当前 Prompt：\n{current_prompt}"

        messages = [
            {"role": "user", "content": f"""
用户修改意见：{user_input}
{context}

请分析修改意见并生成修改方案。
"""}
        ]

        response = await llm_client.chat(messages, REVISION_SYSTEM_PROMPT)

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
        print(f"Revision analysis error: {e}")

    return _fallback_revision(user_input, current_prompt)


def _fallback_revision(user_input: str, current_prompt: str = None) -> Dict[str, Any]:
    """后备修改分析"""
    input_lower = user_input.lower()
    changes = []
    prompt_additions = []

    # 颜色修改
    color_map = {
        "红": ("red", "红色"),
        "蓝": ("blue", "蓝色"),
        "绿": ("green", "绿色"),
        "黄": ("yellow", "黄色"),
        "紫": ("purple", "紫色"),
        "橙": ("orange", "橙色"),
        "粉": ("pink", "粉色"),
    }
    for cn, (en, name) in color_map.items():
        if cn in input_lower:
            changes.append({
                "target": "配色",
                "action": "修改颜色",
                "description": f"使用{name}",
                "prompt_addition": f"{en} color scheme",
                "prompt_removal": "",
            })
            prompt_additions.append(f"{en} color scheme")

    # 亮度修改
    if any(word in input_lower for word in ["亮", "浅", "淡"]):
        changes.append({
            "target": "整体",
            "action": "提高亮度",
            "description": "颜色更亮更鲜艳",
            "prompt_addition": "bright, vibrant, luminous",
            "prompt_removal": "dark, muted",
        })
        prompt_additions.append("bright, vibrant")
    elif any(word in input_lower for word in ["暗", "深"]):
        changes.append({
            "target": "整体",
            "action": "降低亮度",
            "description": "颜色更深沉",
            "prompt_addition": "dark, deep tones",
            "prompt_removal": "bright",
        })
        prompt_additions.append("dark, deep tones")

    # 风格修改
    style_changes = {
        "科技": ("high-tech, futuristic", "科技感"),
        "可爱": ("cute, kawaii", "可爱"),
        "简约": ("minimalist, simple", "简约"),
        "年轻": ("youthful, trendy", "年轻化"),
        "商务": ("professional, business", "商务"),
    }
    for keyword, (prompt_add, desc) in style_changes.items():
        if keyword in input_lower:
            changes.append({
                "target": "风格",
                "action": f"调整为{desc}风格",
                "description": f"增加{desc}元素",
                "prompt_addition": prompt_add,
                "prompt_removal": "",
            })
            prompt_additions.append(prompt_add)

    # 元素修改
    if "加" in input_lower or "增加" in input_lower:
        if "阴影" in input_lower:
            changes.append({
                "target": "效果",
                "action": "添加阴影",
                "description": "增加阴影效果",
                "prompt_addition": "shadow effect, drop shadow",
                "prompt_removal": "",
            })
            prompt_additions.append("shadow effect")
        elif "边框" in input_lower:
            changes.append({
                "target": "效果",
                "action": "添加边框",
                "description": "增加边框装饰",
                "prompt_addition": "border, frame",
                "prompt_removal": "",
            })
            prompt_additions.append("border, frame")

    # 如果没有识别到具体修改
    if not changes:
        changes.append({
            "target": "整体",
            "action": "优化调整",
            "description": user_input,
            "prompt_addition": user_input,
            "prompt_removal": "",
        })
        prompt_additions.append(user_input)

    # 构建更新后的 Prompt
    updated_prompt = current_prompt or ""
    if prompt_additions:
        updated_prompt = f"{updated_prompt}, {', '.join(prompt_additions)}"

    return {
        "revision_type": "mixed",
        "understanding": f"理解您的修改意见：{user_input}",
        "changes": changes,
        "updated_prompt": updated_prompt,
        "explanation": f"已根据您的要求进行修改：{', '.join([c['description'] for c in changes])}",
    }
