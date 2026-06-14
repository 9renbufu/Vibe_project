"""
中文语音指令解析引擎
支持同音字容错、组合指令拆解、优先级修正
"""

import re
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, List, Tuple, Dict, Any

try:
    import jieba
    HAS_JIEBA = True
except ImportError:
    HAS_JIEBA = False


class CommandType(str, Enum):
    DRAW_SHAPE = "draw_shape"
    DRAW_SCENE = "draw_scene"
    DRAW_ART = "draw_art"
    SET_COLOR = "set_color"
    SET_SIZE = "set_size"
    UNDO = "undo"
    REDO = "redo"
    CLEAR = "clear"
    MOVE = "move"
    DELETE = "delete"
    FILL = "fill"
    UNKNOWN = "unknown"


@dataclass
class ParsedCommand:
    command_type: CommandType
    shape_type: Optional[str] = None
    color: Optional[Tuple[int, int, int]] = None
    size: Optional[float] = None
    position: Optional[Tuple[float, float]] = None
    position_name: Optional[str] = None
    art_type: Optional[str] = None
    scene_type: Optional[str] = None
    count: int = 1  # 数量参数
    params: Dict[str, Any] = field(default_factory=dict)
    raw_text: str = ""
    confidence: float = 0.0


# ============ 同音字/近音字纠错映射 ============
HOMOPHONE_MAP: Dict[str, str] = {
    # 形状同音字
    "元形": "圆形", "园形": "圆形", "原形": "圆形",
    "圆形": "圆形", "元形": "圆形",
    "三角型": "三角形", "三角行": "三角形",
    "矩行": "矩形", "矩型": "矩形",
    "心型": "心形", "星型": "星形",
    "椭圆型": "椭圆形",
    # 颜色同音字
    "红涩": "红色", "红社": "红色",
    "蓝涩": "蓝色", "蓝社": "蓝色",
    "绿涩": "绿色", "绿社": "绿色",
    "黄涩": "黄色",
    "紫涩": "紫色",
    "黑涩": "黑色", "嘿色": "黑色",
    "百色": "白色", "拜色": "白色",
    # 动作同音字
    "花": "画", "话": "画", "化": "画",
    "话一个": "画一个", "花一个": "画一个",
    # 场景同音字
    "日": "日落", "夕阳": "日落",
    "新空": "星空", "心空": "星空",
}

# ============ 语气词/填充词 ============
FILLER_WORDS = [
    "的", "了", "呢", "吧", "啊", "呀", "哦", "嘛", "哈",
    "嗯", "呃", "那个", "就是", "然后", "接着", "再",
    "请", "帮我", "能不能", "可以", "我想", "我要",
    "一个", "一幅", "一张", "一条", "一根", "一棵",
    "个", "幅", "张", "条", "根", "棵",
]


# ============ 颜色映射 ============
COLOR_MAP: Dict[str, Tuple[int, int, int]] = {
    "红": (220, 50, 50), "红色": (220, 50, 50), "大红": (255, 0, 0),
    "蓝": (50, 100, 220), "蓝色": (50, 100, 220), "天蓝": (100, 180, 255),
    "深蓝": (20, 40, 150), "浅蓝": (150, 200, 255),
    "绿": (50, 180, 80), "绿色": (50, 180, 80), "深绿": (20, 100, 40),
    "浅绿": (150, 230, 150), "草绿": (100, 200, 80),
    "黄": (240, 210, 50), "黄色": (240, 210, 50), "金黄": (255, 200, 0),
    "紫": (150, 50, 200), "紫色": (150, 50, 200), "深紫": (80, 20, 120),
    "橙": (255, 165, 0), "橙色": (255, 165, 0), "橘": (255, 140, 0),
    "粉": (255, 150, 200), "粉色": (255, 150, 200), "粉红": (255, 100, 150),
    "黑": (30, 30, 30), "黑色": (30, 30, 30),
    "白": (245, 245, 245), "白色": (245, 245, 245),
    "灰": (150, 150, 150), "灰色": (150, 150, 150), "深灰": (80, 80, 80),
    "浅灰": (200, 200, 200), "银": (192, 192, 192), "银色": (192, 192, 192),
    "金": (255, 215, 0), "金色": (255, 215, 0),
    "棕": (139, 90, 43), "棕色": (139, 90, 43), "咖啡": (100, 60, 30),
    "青": (0, 200, 200), "青色": (0, 200, 200), "靛": (75, 0, 130),
    "品红": (255, 0, 255), "玫红": (255, 50, 100),
    "暖色": (255, 180, 100), "冷色": (100, 150, 255),
}

# ============ 形状映射 ============
SHAPE_MAP: Dict[str, str] = {
    "圆": "circle", "圆形": "circle", "圆圈": "circle",
    "矩形": "rectangle", "长方形": "rectangle", "正方形": "square",
    "方": "rectangle", "方形": "rectangle", "方块": "rectangle",
    "三角": "triangle", "三角形": "triangle",
    "线": "line", "线条": "line", "直线": "line",
    "星": "star", "星形": "star", "五角星": "star",
    "心": "heart", "心形": "heart", "爱心": "heart",
    "椭圆": "ellipse", "椭圆形": "ellipse",
    "多边形": "polygon", "六边形": "hexagon", "五边形": "pentagon",
    "菱形": "diamond", "梯形": "trapezoid",
    "箭头": "arrow", "十字": "cross",
}

# ============ 位置映射 ============
POSITION_MAP: Dict[str, Tuple[float, float]] = {
    "中间": (0.5, 0.5), "中心": (0.5, 0.5), "中央": (0.5, 0.5),
    "左上": (0.2, 0.2), "左上角": (0.2, 0.2),
    "右上": (0.8, 0.2), "右上角": (0.8, 0.2),
    "左下": (0.2, 0.8), "左下角": (0.2, 0.8),
    "右下": (0.8, 0.8), "右下角": (0.8, 0.8),
    "左边": (0.2, 0.5), "左侧": (0.2, 0.5), "左": (0.2, 0.5),
    "右边": (0.8, 0.5), "右侧": (0.8, 0.5), "右": (0.8, 0.5),
    "上面": (0.5, 0.2), "上方": (0.5, 0.2), "顶部": (0.5, 0.1),
    "下面": (0.5, 0.8), "下方": (0.5, 0.8), "底部": (0.5, 0.9),
}

# ============ 程序化艺术映射 ============
ART_MAP: Dict[str, str] = {
    "流场": "flow_field", "流动": "flow_field", "流体": "flow_field",
    "风场": "flow_field", "磁场": "flow_field",
    "分形": "fractal_tree", "树": "fractal_tree", "分形树": "fractal_tree",
    "树木": "fractal_tree", "森林": "fractal_tree",
    "水彩": "watercolor", "水墨": "watercolor", "晕染": "watercolor",
    "曼陀罗": "mandala", "万花筒": "mandala", "对称": "mandala",
    "螺线": "spirograph", "螺旋": "spirograph", "旋转": "spirograph",
    "花纹": "spirograph",
    "沃罗诺伊": "voronoi", "细胞": "voronoi", "气泡": "voronoi",
    "几何": "voronoi",
    "粒子": "particle", "烟花": "particle", "星星": "particle",
    "波浪": "wave", "波纹": "wave", "涟漪": "wave",
    "条纹": "stripe", "渐变": "gradient",
}

# ============ 场景映射 ============
SCENE_MAP: Dict[str, str] = {
    "日落": "sunset", "夕阳": "sunset", "黄昏": "sunset", "傍晚": "sunset",
    "海洋": "ocean", "大海": "ocean", "海": "ocean", "海边": "ocean",
    "山": "mountain", "山脉": "mountain", "群山": "mountain", "高山": "mountain",
    "星空": "starry_sky", "夜空": "starry_sky", "夜晚": "starry_sky",
    "太空": "starry_sky", "宇宙": "starry_sky", "星河": "starry_sky", "银河": "starry_sky",
    "森林": "forest", "树林": "forest", "丛林": "forest",
    "草原": "grassland", "草地": "grassland",
    "沙漠": "desert", "沙丘": "desert",
    "雪景": "snow", "冬天": "snow", "雪": "snow",
    "春天": "spring", "花海": "spring",
}


def _correct_homophones(text: str) -> str:
    """同音字纠错"""
    for wrong, right in HOMOPHONE_MAP.items():
        text = text.replace(wrong, right)
    return text


def _clean_text(text: str) -> str:
    """预处理：去标点、纠错、去语气词"""
    # 去标点和空白
    clean = re.sub(r'[，。！？、；：""''（）\s]+', '', text)
    # 同音字纠错
    clean = _correct_homophones(clean)
    return clean


def _extract_color(text: str) -> Optional[Tuple[int, int, int]]:
    """提取颜色"""
    for name, rgb in COLOR_MAP.items():
        if name in text:
            return rgb
    return None


def _extract_shape(text: str) -> Optional[str]:
    """提取形状"""
    for name, shape in SHAPE_MAP.items():
        if name in text:
            return shape
    return None


def _extract_position(text: str) -> Optional[Tuple[float, float]]:
    """提取位置（相对坐标 0-1）"""
    for name, pos in POSITION_MAP.items():
        if name in text:
            return pos
    px_match = re.search(r'(\d+)\s*[像素px,，]\s*(\d+)', text)
    if px_match:
        return (float(px_match.group(1)) / 1200, float(px_match.group(2)) / 800)
    return None


def _extract_size(text: str) -> Optional[float]:
    """提取大小"""
    size_map = {
        "很大": 200, "超大": 250, "巨大": 300,
        "大": 150, "较大": 130,
        "中": 80, "中等": 80,
        "小": 40, "较小": 35, "很小": 25, "迷你": 20,
        "粗": 150, "细": 30,
    }
    for name, size in size_map.items():
        if name in text:
            return size
    num_match = re.search(r'(\d+)\s*(?:像素|px|大小|半径)', text)
    if num_match:
        return float(num_match.group(1))
    return None


def _extract_count(text: str) -> int:
    """提取数量"""
    count_map = {
        "一": 1, "二": 2, "两": 2, "三": 3, "四": 4, "五": 5,
        "六": 6, "七": 7, "八": 8, "九": 9, "十": 10,
    }
    for word, num in count_map.items():
        # 匹配 "画三个"、"画五 个" 等
        if re.search(rf'{word}\s*个|{word}\s*条|{word}\s*根|{word}\s*棵', text):
            return num
    num_match = re.search(r'(\d+)\s*[个条根棵幅张]', text)
    if num_match:
        return int(num_match.group(1))
    return 1


def _extract_art_type(text: str) -> Optional[str]:
    """提取程序化艺术类型"""
    for name, art in ART_MAP.items():
        if name in text:
            return art
    return None


def _extract_scene_type(text: str) -> Optional[str]:
    """提取场景类型"""
    for name, scene in SCENE_MAP.items():
        if name in text:
            return scene
    return None


def _extract_direction(text: str) -> Optional[str]:
    """提取移动方向"""
    direction_map = {
        "左": "left", "往左": "left", "向左": "left",
        "右": "right", "往右": "right", "向右": "right",
        "上": "up", "往上": "up", "向上": "up",
        "下": "down", "往下": "down", "向下": "down",
    }
    for name, direction in direction_map.items():
        if name in text:
            return direction
    return None


def _has_draw_intent(text: str) -> bool:
    """检测是否包含绘图意图动词"""
    return bool(re.search(r'画|创建|来|做|生成|加|添|增加|再来|花一个|话一个', text))


def _split_compound(text: str) -> List[str]:
    """拆分复合指令：按'然后'、'接着'、'再'、'还有'分句"""
    parts = re.split(r'然后|接着|再|还有|并且|同时|之后', text)
    return [p.strip() for p in parts if p.strip()]


def _parse_single(text: str, clean: str) -> ParsedCommand:
    """解析单条指令（已纠错的文本）"""

    # ============ 撤销/重做/清空（最高优先级）============
    if re.search(r'撤销|回退|后悔|返回上一步|上一步', clean):
        return ParsedCommand(command_type=CommandType.UNDO, raw_text=text, confidence=0.95)

    if re.search(r'重做|恢复|前进|下一步', clean):
        return ParsedCommand(command_type=CommandType.REDO, raw_text=text, confidence=0.95)

    if re.search(r'清空|清除|全部删除|重新开始|重置|清屏', clean):
        return ParsedCommand(command_type=CommandType.CLEAR, raw_text=text, confidence=0.95)

    # ============ 移动 ============
    direction = _extract_direction(clean)
    if direction and re.search(r'移动|挪|移', clean):
        dist_match = re.search(r'(\d+)', clean)
        dist = float(dist_match.group(1)) if dist_match else 100
        return ParsedCommand(
            command_type=CommandType.MOVE,
            params={"direction": direction, "distance": dist},
            raw_text=text, confidence=0.9,
        )

    # ============ 删除 ============
    if re.search(r'删除|去掉|移除|擦除', clean):
        shape = _extract_shape(clean)
        return ParsedCommand(
            command_type=CommandType.DELETE,
            shape_type=shape,
            raw_text=text, confidence=0.9,
        )

    # ============ 提取所有属性 ============
    color = _extract_color(clean)
    shape = _extract_shape(clean)
    art_type = _extract_art_type(clean)
    scene_type = _extract_scene_type(clean)
    pos = _extract_position(clean)
    size = _extract_size(clean)
    count = _extract_count(clean)
    has_draw = _has_draw_intent(clean)

    # ============ 纯设置颜色（无形状/艺术/场景，且有明确的颜色设置动词）============
    if color and not shape and not art_type and not scene_type:
        if re.search(r'改.*颜色|换.*颜色|变.*颜色|设置.*颜色|颜色.*改|颜色.*换|颜色.*设|涂|填充|把.*色', clean):
            return ParsedCommand(
                command_type=CommandType.SET_COLOR,
                color=color, raw_text=text, confidence=0.85,
            )

    # ============ 纯设置大小（无形状/艺术/场景）============
    if size and not shape and not art_type and not scene_type:
        if re.search(r'大小|尺寸|粗细|调.*大|调.*小|改.*大|改.*小', clean):
            return ParsedCommand(
                command_type=CommandType.SET_SIZE,
                size=size, raw_text=text, confidence=0.85,
            )

    # ============ 程序化艺术（优先级高于形状）============
    if art_type:
        return ParsedCommand(
            command_type=CommandType.DRAW_ART,
            art_type=art_type, color=color,
            size=size, raw_text=text, confidence=0.9,
        )

    # ============ 场景 ============
    if scene_type:
        return ParsedCommand(
            command_type=CommandType.DRAW_SCENE,
            scene_type=scene_type, color=color,
            raw_text=text, confidence=0.9,
        )

    # ============ 基础图形（组合指令：颜色+形状+位置+大小+数量）============
    if shape:
        return ParsedCommand(
            command_type=CommandType.DRAW_SHAPE,
            shape_type=shape, color=color,
            size=size, position=pos, count=count,
            raw_text=text, confidence=0.85 if has_draw else 0.6,
        )

    # ============ 填充 ============
    if re.search(r'填充|涂满|填色', clean):
        return ParsedCommand(
            command_type=CommandType.FILL,
            color=color, raw_text=text, confidence=0.8,
        )

    # ============ 模糊匹配：有绘图意图但没匹配到形状/艺术 ============
    if has_draw:
        # 尝试从文本推断
        if color:
            # "画红色的" - 默认画圆
            return ParsedCommand(
                command_type=CommandType.DRAW_SHAPE,
                shape_type="circle", color=color,
                size=size, position=pos,
                raw_text=text, confidence=0.5,
            )

    return ParsedCommand(
        command_type=CommandType.UNKNOWN,
        raw_text=text, confidence=0.0,
    )


def parse_command(text: str) -> ParsedCommand:
    """主解析入口"""
    text = text.strip()
    if not text:
        return ParsedCommand(command_type=CommandType.UNKNOWN, raw_text=text)

    # 预处理：纠错 + 去标点
    clean = _clean_text(text)

    # 检查是否是复合指令（包含"然后"、"接着"、"再"等）
    parts = _split_compound(clean)
    if len(parts) > 1:
        # 复合指令：解析第一部分，返回最高优先级的结果
        # 后续部分由调用方循环处理
        first = _parse_single(text, parts[0])
        # 把剩余部分存入 params 供后续处理
        first.params["compound_parts"] = parts[1:]
        first.confidence = max(first.confidence - 0.05, 0.3)
        return first

    return _parse_single(text, clean)
