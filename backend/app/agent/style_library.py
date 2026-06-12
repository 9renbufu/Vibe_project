"""
设计风格库 - 定义各种设计风格的 Prompt 模板
"""

STYLE_LIBRARY = {
    # ===== 视觉风格 =====
    "apple": {
        "name": "Apple 极简风",
        "keywords": ["极简", "简约", "苹果", "白色", "干净"],
        "prompt": "Apple-style minimalist design, clean white background, subtle shadows, rounded corners, San Francisco typography, premium feel, lots of whitespace, simple geometric shapes",
        "colors": ["#ffffff", "#f5f5f7", "#1d1d1f", "#0071e3"],
        "description": "苹果风格，极简白色调，精致阴影",
    },
    "minimalist": {
        "name": "极简主义",
        "keywords": ["极简", "简约", "简单", "留白"],
        "prompt": "Minimalist design, geometric shapes, limited color palette, bold typography, negative space, clean lines, modern aesthetics",
        "colors": ["#000000", "#ffffff", "#ff0000", "#0000ff"],
        "description": "极简主义，几何图形，大胆配色",
    },
    "cyberpunk": {
        "name": "赛博朋克",
        "keywords": ["赛博", "科技", "未来", "霓虹", "霓虹灯"],
        "prompt": "Cyberpunk style, neon lights, dark background, glowing effects, futuristic elements, holographic, electric blue and magenta, rain-soaked streets, digital glitch effects",
        "colors": ["#00d4ff", "#ff00ff", "#7b2ff7", "#00ff88"],
        "description": "赛博朋克，霓虹灯光，未来感",
    },
    "anime": {
        "name": "日系动漫",
        "keywords": ["动漫", "二次元", "日系", "可爱", "萌"],
        "prompt": "Anime style, vibrant colors, expressive characters, Studio Ghibli inspired, soft shading, cute aesthetic, Japanese illustration",
        "colors": ["#ff6b9d", "#c44dff", "#4dc9ff", "#ffcc00"],
        "description": "日系动漫风格，色彩鲜艳，可爱元素",
    },
    "luxury": {
        "name": "奢华高端",
        "keywords": ["奢华", "高端", "豪华", "金色", "黑色"],
        "prompt": "Luxury design, gold and black color scheme, elegant typography, premium textures, marble patterns, metallic accents, sophisticated atmosphere",
        "colors": ["#c9a84c", "#1a1a1a", "#f5f5f5", "#8b7355"],
        "description": "奢华风格，金黑配色，高端质感",
    },
    "modern": {
        "name": "现代简约",
        "keywords": ["现代", "时尚", "潮流"],
        "prompt": "Modern design, bold gradients, abstract shapes, contemporary typography, dynamic composition, trendy color palette",
        "colors": ["#667eea", "#764ba2", "#f093fb", "#f5576c"],
        "description": "现代风格，渐变色彩，动感构图",
    },
    "chinese": {
        "name": "中国风",
        "keywords": ["中国风", "国潮", "传统", "古典", "水墨"],
        "prompt": "Chinese traditional style, ink wash painting, red and gold colors, ancient patterns, calligraphy elements, cultural symbols, elegant brush strokes",
        "colors": ["#c41e3a", "#ffd700", "#2f4f4f", "#8b0000"],
        "description": "中国风，水墨画，红金配色",
    },
    "retro": {
        "name": "复古怀旧",
        "keywords": ["复古", "怀旧", "老式", "vintage"],
        "prompt": "Retro vintage style, muted colors, aged textures, nostalgic typography, 80s aesthetic, film grain effect, old school design",
        "colors": ["#d4a574", "#c9956b", "#8b6f47", "#f4e4c1"],
        "description": "复古风格，怀旧色调，做旧质感",
    },
    "cartoon": {
        "name": "卡通手绘",
        "keywords": ["卡通", "手绘", "可爱", "趣味"],
        "prompt": "Cartoon style, hand-drawn illustration, playful design, bright colors, rounded shapes, fun characters, whimsical elements",
        "colors": ["#ff6b6b", "#4ecdc4", "#45b7d1", "#96ceb4"],
        "description": "卡通风格，手绘插画，趣味元素",
    },
    "gradient": {
        "name": "渐变流体",
        "keywords": ["渐变", "流体", "彩色"],
        "prompt": "Gradient design, fluid shapes, colorful transitions, mesh gradients, abstract blobs, vibrant color mixing, modern aesthetic",
        "colors": ["#667eea", "#764ba2", "#f093fb", "#f5576c"],
        "description": "渐变风格，流体形状，色彩过渡",
    },
    "neon": {
        "name": "霓虹灯光",
        "keywords": ["霓虹", "灯光", "发光"],
        "prompt": "Neon glow effects, dark background, electric colors, glowing text, light trails, nightclub aesthetic, vibrant illumination",
        "colors": ["#00ff88", "#00d4ff", "#ff00ff", "#ffff00"],
        "description": "霓虹风格，发光效果，深色背景",
    },
    "watercolor": {
        "name": "水彩手绘",
        "keywords": ["水彩", "手绘", "艺术"],
        "prompt": "Watercolor painting style, soft washes, blending colors, artistic brush strokes, paper texture, delicate and flowing",
        "colors": ["#87ceeb", "#ffb6c1", "#98fb98", "#dda0dd"],
        "description": "水彩风格，柔和色彩，艺术感",
    },
    "tech": {
        "name": "科技感",
        "keywords": ["科技", "技术", "未来", "数字"],
        "prompt": "High-tech design, futuristic interface, holographic elements, circuit patterns, digital grid, cool blue tones, advanced technology feel",
        "colors": ["#00d4ff", "#0066cc", "#003366", "#00ff88"],
        "description": "科技风格，未来界面，数字元素",
    },
}


# ===== 设计任务类型 =====
TASK_TYPES = {
    "logo": {
        "name": "Logo 设计",
        "keywords": ["logo", "标志", "商标", "标识"],
        "prompt_prefix": "Professional logo design, vector style, scalable, memorable symbol",
        "aspects": ["简洁性", "可识别性", "可缩放性", "适用性"],
    },
    "poster": {
        "name": "海报设计",
        "keywords": ["海报", "poster", "宣传", "广告"],
        "prompt_prefix": "Eye-catching poster design, bold typography, clear hierarchy, visual impact",
        "aspects": ["视觉冲击力", "信息层次", "配色协调", "文字可读性"],
    },
    "banner": {
        "name": "横幅/Banner",
        "keywords": ["横幅", "banner", "头图", "封面"],
        "prompt_prefix": "Web banner design, clear message, call to action, responsive layout",
        "aspects": ["尺寸适配", "信息简洁", "视觉引导", "行动号召"],
    },
    "card": {
        "name": "名片/卡片",
        "keywords": ["名片", "卡片", "card"],
        "prompt_prefix": "Business card design, professional layout, contact information hierarchy",
        "aspects": ["信息完整", "排版清晰", "品牌一致", "印刷适配"],
    },
    "social": {
        "name": "社交媒体图",
        "keywords": ["朋友圈", "小红书", "社交媒体", "头像"],
        "prompt_prefix": "Social media graphic, engaging visual, platform optimized, shareable content",
        "aspects": ["平台适配", "吸引力", "传播性", "品牌调性"],
    },
    "ip": {
        "name": "IP 形象",
        "keywords": ["ip", "吉祥物", "形象", "角色", "mascot"],
        "prompt_prefix": "Character design, mascot, cute and memorable, brand personality, consistent style",
        "aspects": ["辨识度", "可爱度", "品牌关联", "延展性"],
    },
    "ui": {
        "name": "UI 界面",
        "keywords": ["界面", "ui", "app", "网页"],
        "prompt_prefix": "UI design, user-friendly interface, clear navigation, modern aesthetics",
        "aspects": ["易用性", "视觉层次", "交互逻辑", "响应式"],
    },
    "packaging": {
        "name": "包装设计",
        "keywords": ["包装", "礼盒", "产品"],
        "prompt_prefix": "Product packaging design, shelf appeal, brand recognition, unboxing experience",
        "aspects": ["货架展示", "品牌识别", "开箱体验", "材质质感"],
    },
}


def get_style_prompt(style_name: str) -> str:
    """获取风格 Prompt"""
    style = STYLE_LIBRARY.get(style_name)
    return style["prompt"] if style else ""


def get_task_prompt(task_type: str) -> str:
    """获取任务类型 Prompt"""
    task = TASK_TYPES.get(task_type)
    return task["prompt_prefix"] if task else ""


def match_style(text: str) -> str:
    """从文本匹配风格"""
    text_lower = text.lower()
    for style_id, style in STYLE_LIBRARY.items():
        for keyword in style["keywords"]:
            if keyword in text_lower:
                return style_id
    return "modern"  # 默认现代风格


def match_task_type(text: str) -> str:
    """从文本匹配任务类型"""
    text_lower = text.lower()
    for task_id, task in TASK_TYPES.items():
        for keyword in task["keywords"]:
            if keyword in text_lower:
                return task_id
    return "poster"  # 默认海报
