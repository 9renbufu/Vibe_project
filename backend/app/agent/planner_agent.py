"""
Design Planner Agent - 设计规划代理
职责：根据意图分析结果，生成完整的设计方案
"""

import json
from typing import Dict, Any, List
from .style_library import STYLE_LIBRARY, TASK_TYPES, get_style_prompt, get_task_prompt


PLANNER_SYSTEM_PROMPT = """你是一个专业的设计规划师。根据用户需求，生成详细的设计方案。

## 输入
你会收到：
1. 用户原始需求
2. 意图分析结果（任务类型、风格、元素等）

## 输出格式
```json
{
    "project_name": "项目名称",
    "design_goal": "设计目标（一句话）",
    "task_type": "logo|poster|banner|card|social|ip|ui|packaging",
    "style": "风格ID",
    "style_name": "风格名称",
    "composition": {
        "layout": "布局方式",
        "focal_point": "视觉焦点",
        "hierarchy": ["层次1", "层次2"]
    },
    "elements": [
        {
            "name": "元素名称",
            "type": "text|shape|image|icon",
            "description": "详细描述",
            "position": "位置",
            "size": "大小",
            "color": "颜色",
            "z_index": 1
        }
    ],
    "color_palette": {
        "primary": "#主色",
        "secondary": "#辅色",
        "accent": "#强调色",
        "background": "#背景色",
        "text": "#文字色",
        "palette": ["#hex1", "#hex2", "#hex3"]
    },
    "typography": {
        "title": "标题字体风格",
        "body": "正文字体风格",
        "accent": "强调文字风格"
    },
    "mood_keywords": ["关键词1", "关键词2"],
    "target_audience": "目标受众",
    "design_principles": ["原则1", "原则2"],
    "image_prompt": "完整的英文图像生成提示词",
    "explanation": "给用户的中文解释"
}
```

## 设计原则
1. 简洁明了：少即是多
2. 层次分明：主次清晰
3. 配色和谐：不超过3-4种主要颜色
4. 风格统一：元素风格一致
5. 目标导向：服务于设计目的

## Prompt 生成技巧
1. 先描述整体风格和氛围
2. 再描述主体元素
3. 然后是细节和装饰
4. 最后是技术质量要求
5. 添加负面提示词避免问题

只返回 JSON，不要其他内容。"""


async def generate_design_plan(
    llm_client,
    user_input: str,
    intent_result: Dict[str, Any],
    design_context: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """生成设计方案"""
    if not llm_client:
        return _fallback_plan(user_input, intent_result)

    try:
        # 构建上下文
        context_info = ""
        if design_context:
            context_info = f"\n\n当前设计上下文：{json.dumps(design_context, ensure_ascii=False)}"

        # 获取风格和任务的 Prompt
        style_id = intent_result.get("style", "modern")
        task_type = intent_result.get("task_type", "poster")

        style_info = STYLE_LIBRARY.get(style_id, STYLE_LIBRARY["modern"])
        task_info = TASK_TYPES.get(task_type, TASK_TYPES["poster"])

        style_context = f"""
参考风格：{style_info['name']}
风格 Prompt：{style_info['prompt']}
推荐配色：{', '.join(style_info['colors'])}

任务类型：{task_info['name']}
任务 Prompt：{task_info['prompt_prefix']}
设计要点：{', '.join(task_info['aspects'])}
"""

        messages = [
            {"role": "user", "content": f"""
用户需求：{user_input}

意图分析：
{json.dumps(intent_result, ensure_ascii=False, indent=2)}

{style_context}
{context_info}

请生成详细的设计方案。
"""}
        ]

        response = await llm_client.chat(messages, PLANNER_SYSTEM_PROMPT)

        # 解析 JSON
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0]
        elif "```" in response:
            response = response.split("```")[1].split("```")[0]

        json_start = response.find("{")
        json_end = response.rfind("}") + 1
        if json_start != -1 and json_end > json_start:
            result = json.loads(response[json_start:json_end])

            # 确保有 image_prompt
            if "image_prompt" not in result:
                result["image_prompt"] = _build_image_prompt(result)

            return result

    except Exception as e:
        print(f"Planner error: {e}")

    return _fallback_plan(user_input, intent_result)


def _fallback_plan(user_input: str, intent_result: Dict[str, Any]) -> Dict[str, Any]:
    """后备设计方案"""
    style_id = intent_result.get("style", "modern")
    task_type = intent_result.get("task_type", "poster")

    style_info = STYLE_LIBRARY.get(style_id, STYLE_LIBRARY["modern"])
    task_info = TASK_TYPES.get(task_type, TASK_TYPES["poster"])

    subject = intent_result.get("entities", {}).get("subject", user_input[:20])

    return {
        "project_name": f"{subject}设计",
        "design_goal": f"设计一个{style_info['name']}风格的{task_info['name']}",
        "task_type": task_type,
        "style": style_id,
        "style_name": style_info["name"],
        "composition": {
            "layout": "居中布局",
            "focal_point": "主体元素",
            "hierarchy": ["主体", "背景", "装饰"]
        },
        "elements": [
            {
                "name": "主体",
                "type": "shape",
                "description": subject,
                "position": "中心",
                "size": "大",
                "color": style_info["colors"][0] if style_info["colors"] else "#000000",
                "z_index": 10
            }
        ],
        "color_palette": {
            "primary": style_info["colors"][0] if style_info["colors"] else "#000000",
            "secondary": style_info["colors"][1] if len(style_info["colors"]) > 1 else "#666666",
            "accent": style_info["colors"][2] if len(style_info["colors"]) > 2 else "#ff0000",
            "background": "#ffffff",
            "text": "#333333",
            "palette": style_info["colors"]
        },
        "typography": {
            "title": "粗体大字",
            "body": "常规体",
            "accent": "装饰体"
        },
        "mood_keywords": [style_info["name"], task_info["name"]],
        "target_audience": "大众",
        "design_principles": task_info["aspects"],
        "image_prompt": f"{task_info['prompt_prefix']}, {style_info['prompt']}, {subject}, high quality, professional design",
        "explanation": f"为您设计了一个{style_info['name']}风格的{task_info['name']}，主体是{subject}。"
    }


def _build_image_prompt(plan: Dict[str, Any]) -> str:
    """从设计方案构建图像 Prompt"""
    parts = []

    # 任务类型
    task_type = plan.get("task_type", "poster")
    task_info = TASK_TYPES.get(task_type)
    if task_info:
        parts.append(task_info["prompt_prefix"])

    # 风格
    style_id = plan.get("style", "modern")
    style_info = STYLE_LIBRARY.get(style_id)
    if style_info:
        parts.append(style_info["prompt"])

    # 元素
    elements = plan.get("elements", [])
    element_desc = ", ".join([e.get("description", "") for e in elements[:3]])
    if element_desc:
        parts.append(element_desc)

    # 配色
    colors = plan.get("color_palette", {}).get("palette", [])
    if colors:
        parts.append(f"color palette: {', '.join(colors[:3])}")

    # 质量
    parts.append("high quality, professional design, 4k")

    return ", ".join(parts)
