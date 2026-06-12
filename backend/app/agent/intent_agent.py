"""
Intent Agent - 意图识别代理
职责：理解用户输入，识别设计意图
"""

import json
from typing import Dict, Any, Optional


INTENT_SYSTEM_PROMPT = """你是一个意图识别专家。分析用户输入，识别设计意图。

## 输出格式
```json
{
    "intent": "意图类型",
    "confidence": 0.0-1.0,
    "task_type": "任务类型",
    "style": "风格偏好",
    "entities": {
        "subject": "设计主体",
        "colors": ["颜色"],
        "elements": ["元素"],
        "audience": "目标受众",
        "mood": "情绪氛围"
    },
    "is_clear": true/false,
    "missing_info": ["缺少的信息"],
    "suggested_questions": ["建议询问的问题"]
}
```

## 意图类型
- new_design: 新建设计
- modify_design: 修改现有设计
- ask_suggestion: 询问建议
- export: 导出作品
- general_chat: 普通对话

## 任务类型
- logo: Logo设计
- poster: 海报设计
- banner: 横幅设计
- card: 名片/卡片
- social: 社交媒体图
- ip: IP形象/吉祥物
- ui: UI界面
- packaging: 包装设计
- illustration: 插画
- other: 其他

## 风格识别
从用户输入中识别风格偏好：
- 极简/minimalist/简约
- 赛博朋克/cyberpunk/科技感
- 动漫/anime/二次元
- 奢华/luxury/高端
- 中国风/国潮/传统
- 复古/retro/vintage
- 卡通/cartoon/可爱
- 现代/modern/时尚

只返回 JSON，不要其他内容。"""


async def analyze_intent(llm_client, user_input: str) -> Dict[str, Any]:
    """分析用户意图"""
    if not llm_client:
        return _fallback_intent(user_input)

    try:
        messages = [{"role": "user", "content": user_input}]
        response = await llm_client.chat(messages, INTENT_SYSTEM_PROMPT)

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
        print(f"Intent analysis error: {e}")

    return _fallback_intent(user_input)


def _fallback_intent(user_input: str) -> Dict[str, Any]:
    """后备意图识别"""
    input_lower = user_input.lower()

    # 检测意图
    intent = "new_design"
    if any(word in input_lower for word in ["修改", "调整", "改", "换", "变"]):
        intent = "modify_design"
    elif any(word in input_lower for word in ["建议", "推荐", "怎么"]):
        intent = "ask_suggestion"
    elif any(word in input_lower for word in ["导出", "保存", "下载"]):
        intent = "export"

    # 检测任务类型
    task_type = "poster"
    task_keywords = {
        "logo": ["logo", "标志", "商标"],
        "poster": ["海报", "poster"],
        "banner": ["横幅", "banner"],
        "card": ["名片", "卡片"],
        "social": ["朋友圈", "头像"],
        "ip": ["吉祥物", "ip", "形象"],
    }
    for ttype, keywords in task_keywords.items():
        if any(kw in input_lower for kw in keywords):
            task_type = ttype
            break

    # 检测风格
    style = "modern"
    style_keywords = {
        "cyberpunk": ["赛博", "科技", "霓虹"],
        "anime": ["动漫", "二次元"],
        "luxury": ["奢华", "高端", "豪华"],
        "chinese": ["中国风", "国潮"],
        "minimalist": ["极简", "简约"],
    }
    for st, keywords in style_keywords.items():
        if any(kw in input_lower for kw in keywords):
            style = st
            break

    return {
        "intent": intent,
        "confidence": 0.7,
        "task_type": task_type,
        "style": style,
        "entities": {
            "subject": user_input[:20],
            "colors": [],
            "elements": [],
            "audience": "",
            "mood": "",
        },
        "is_clear": len(user_input) > 10,
        "missing_info": [],
        "suggested_questions": [],
    }
