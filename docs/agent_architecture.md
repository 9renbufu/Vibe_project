# Voice Designer Agent 架构设计

## 1. 系统架构图

```
┌─────────────┐
│ Voice Input │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Whisper ASR │ 语音转文字
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ IntentAgent │ 意图识别
└──────┬──────┘
       │
       ├──────────────────┐
       │                  │
       ▼                  ▼
┌─────────────┐    ┌─────────────┐
│  Planner    │    │  Revision   │  新设计 / 修改设计
└──────┬──────┘    └──────┬──────┘
       │                  │
       └────────┬─────────┘
                │
                ▼
         ┌─────────────┐
         │ PromptAgent │ 提示词生成
         └──────┬──────┘
                │
                ▼
         ┌─────────────┐
         │ Image Gen   │ 图像生成
         └──────┬──────┘
                │
                ▼
         ┌─────────────┐
         │   Memory    │ 记忆存储
         └─────────────┘
```

## 2. Agent 详细设计

### 2.1 Intent Agent（意图识别代理）

**职责**：理解用户输入，识别设计意图

**输入**：用户语音转文字

**输出**：
```json
{
    "intent": "new_design | modify_design | ask_suggestion | export",
    "confidence": 0.95,
    "task_type": "logo | poster | banner | card | social | ip",
    "style": "cyberpunk | anime | luxury | minimalist",
    "entities": {
        "subject": "奶茶店",
        "colors": ["粉色", "白色"],
        "elements": ["杯子", "奶茶"],
        "audience": "年轻人",
        "mood": "清新"
    },
    "is_clear": true,
    "missing_info": [],
    "suggested_questions": []
}
```

**Prompt 设计要点**：
- 定义清晰的意图分类
- 提取关键实体信息
- 判断需求完整性
- 生成追问建议

---

### 2.2 Design Planner Agent（设计规划代理）

**职责**：根据意图生成完整设计方案

**输入**：
- 用户原始需求
- 意图分析结果
- 设计上下文

**输出**：
```json
{
    "project_name": "清新奶茶店Logo",
    "design_goal": "设计一个吸引年轻人的清新风格Logo",
    "task_type": "logo",
    "style": "modern",
    "style_name": "现代简约",
    "composition": {
        "layout": "居中布局",
        "focal_point": "奶茶杯图形",
        "hierarchy": ["主体图形", "品牌名称", "装饰元素"]
    },
    "elements": [
        {
            "name": "奶茶杯",
            "type": "shape",
            "description": "简约风格的奶茶杯轮廓",
            "position": "中心上方",
            "size": "大",
            "color": "#FFB6C1",
            "z_index": 10
        },
        {
            "name": "品牌名",
            "type": "text",
            "description": "茶颜悦色",
            "position": "中心下方",
            "size": "中",
            "color": "#333333",
            "z_index": 5
        }
    ],
    "color_palette": {
        "primary": "#FFB6C1",
        "secondary": "#FFFFFF",
        "accent": "#FF69B4",
        "background": "#FFF5F5",
        "text": "#333333",
        "palette": ["#FFB6C1", "#FFFFFF", "#FF69B4"]
    },
    "typography": {
        "title": "圆润可爱字体",
        "body": "简约无衬线",
        "accent": "手写风格"
    },
    "mood_keywords": ["清新", "可爱", "年轻", "活力"],
    "target_audience": "18-30岁年轻女性",
    "design_principles": ["简洁性", "可识别性", "适用性"],
    "image_prompt": "...",
    "explanation": "为您设计了一个清新可爱的奶茶店Logo..."
}
```

**Prompt 设计要点**：
- 结合风格库和任务库
- 考虑设计原则
- 生成结构化方案
- 包含完整 Prompt

---

### 2.3 Prompt Generator Agent（提示词生成代理）

**职责**：将设计方案转换为高质量图像 Prompt

**输入**：设计方案 JSON

**输出**：
```json
{
    "positive_prompt": "masterpiece, best quality, logo design, minimalist style, cute milk tea cup, pink and white color scheme, clean background, vector style, professional, 4k",
    "negative_prompt": "low quality, blurry, distorted, ugly, text error, watermark",
    "style_keywords": ["minimalist", "cute", "modern"],
    "technical_params": {
        "aspect_ratio": "1:1",
        "quality": "hd"
    }
}
```

**Prompt 结构**：
1. 质量词：masterpiece, best quality, 4k
2. 类型词：logo design, poster design
3. 风格词：minimalist, cyberpunk, anime
4. 主体描述：具体元素描述
5. 配色描述：color scheme
6. 构图描述：composition
7. 光影效果：lighting
8. 背景描述：background

---

### 2.4 Design Revision Agent（设计修改代理）

**职责**：理解修改意见，生成修改方案

**输入**：
- 用户修改意见
- 当前设计方案
- 当前 Prompt

**输出**：
```json
{
    "revision_type": "color",
    "understanding": "您希望颜色更亮更鲜艳",
    "changes": [
        {
            "target": "配色",
            "action": "提高亮度",
            "description": "使用更鲜艳的颜色",
            "prompt_addition": "bright, vibrant, luminous",
            "prompt_removal": "dark, muted"
        }
    ],
    "updated_prompt": "..., bright, vibrant, luminous",
    "explanation": "已将颜色调整为更鲜艳的效果"
}
```

**常见修改指令映射**：
| 用户输入 | 修改类型 | Prompt 添加 |
|---------|---------|------------|
| 颜色更亮 | color | bright, vibrant |
| 颜色更暗 | color | dark, deep tones |
| 换成红色 | color | red color scheme |
| 更简约 | style | minimalist, simple |
| 更科技 | style | high-tech, futuristic |
| 更可爱 | style | cute, kawaii |
| 加个阴影 | element | shadow effect |
| 字体大一点 | text | larger typography |
| 居中 | composition | center alignment |
| 留白多一点 | composition | more whitespace |

---

## 3. 风格库设计

```python
STYLE_LIBRARY = {
    "apple": {
        "name": "Apple 极简风",
        "keywords": ["极简", "简约", "苹果", "白色"],
        "prompt": "Apple-style minimalist design, clean white background...",
        "colors": ["#ffffff", "#f5f5f7", "#1d1d1f", "#0071e3"],
    },
    "cyberpunk": {
        "name": "赛博朋克",
        "keywords": ["赛博", "科技", "未来", "霓虹"],
        "prompt": "Cyberpunk style, neon lights, dark background...",
        "colors": ["#00d4ff", "#ff00ff", "#7b2ff7"],
    },
    # ... 更多风格
}
```

---

## 4. Pipeline 流程

```python
class DesignPipeline:
    async def process_voice_input(self, user_input: str):
        # Step 1: Intent Analysis
        intent = await analyze_intent(self.llm, user_input)

        # Step 2: Check if revision
        if intent["intent"] == "modify_design":
            return await self._handle_revision(user_input)

        # Step 3: Design Planning
        plan = await generate_design_plan(self.llm, user_input, intent)

        # Step 4: Prompt Generation
        prompt = await generate_image_prompt(self.llm, plan)

        # Step 5: Image Generation
        image = await self.image_gen.generate(prompt)

        return {"plan": plan, "image": image}
```

---

## 5. 48小时开发路线

### 第一阶段（12小时）
- [x] Agent 框架搭建
- [x] Intent Agent
- [x] Style Library

### 第二阶段（12小时）
- [x] Planner Agent
- [x] Prompt Agent
- [x] Pipeline 集成

### 第三阶段（12小时）
- [x] Revision Agent
- [x] 图像生成集成
- [x] WebSocket 通信

### 第四阶段（12小时）
- [ ] UI 优化
- [ ] 测试调试
- [ ] 文档完善
