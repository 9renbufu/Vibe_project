import re
from typing import Optional, Tuple


class VoiceProcessor:
    def __init__(self):
        self.common_corrections = {
            "画虎": "画壶",
            "化": "画",
            "话一个": "画一个",
            "花": "画",
            "圆": "圆形",
            "方块": "矩形",
            "三角": "三角形",
            "红色": "红色",
            "蓝色": "蓝色",
            "绿色": "绿色",
            "黄色": "黄色",
        }
        self.command_keywords = {
            "draw": ["画", "画一个", "创建", "绘制", "画出", "描绘"],
            "move": ["移动", "移到", "移", "挪", "搬到"],
            "delete": ["删除", "去掉", "擦掉", "移除", "消除"],
            "modify": ["修改", "改变", "调整", "变"],
            "clear": ["清空", "清除", "全部删除", "重新开始"],
        }

    def correct_text(self, text: str) -> str:
        corrected = text
        for wrong, right in self.common_corrections.items():
            corrected = corrected.replace(wrong, right)

        corrected = re.sub(r'\s+', ' ', corrected).strip()
        return corrected

    def extract_command_type(self, text: str) -> Tuple[str, float]:
        text_lower = text.lower()
        for cmd_type, keywords in self.command_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return cmd_type, 0.9
        return "unknown", 0.3

    def extract_color(self, text: str) -> Optional[Tuple[int, int, int]]:
        colors = {
            "红": (255, 0, 0), "red": (255, 0, 0),
            "蓝": (0, 0, 255), "blue": (0, 0, 255),
            "绿": (0, 128, 0), "green": (0, 128, 0),
            "黄": (255, 255, 0), "yellow": (255, 255, 0),
            "黑": (0, 0, 0), "black": (0, 0, 0),
            "白": (255, 255, 255), "white": (255, 255, 255),
            "紫": (128, 0, 128), "purple": (128, 0, 128),
            "橙": (255, 165, 0), "orange": (255, 165, 0),
            "粉": (255, 192, 203), "pink": (255, 192, 203),
            "灰": (128, 128, 128), "gray": (128, 128, 128),
        }
        text_lower = text.lower()
        for color_name, rgb in colors.items():
            if color_name in text_lower:
                return rgb
        return None

    def extract_shape(self, text: str) -> Optional[str]:
        shapes = {
            "圆": "circle", "圆形": "circle", "circle": "circle",
            "方": "rectangle", "矩形": "rectangle", "方形": "rectangle",
            "rectangle": "rectangle", "square": "rectangle",
            "线": "line", "直线": "line", "line": "line",
            "三角": "triangle", "三角形": "triangle", "triangle": "triangle",
        }
        text_lower = text.lower()
        for shape_name, shape_type in shapes.items():
            if shape_name in text_lower:
                return shape_type
        return None

    def extract_size(self, text: str) -> Optional[Tuple[float, float]]:
        size_patterns = [
            r'(\d+)\s*[xX×]\s*(\d+)',
            r'半径\s*(\d+)',
            r'radius\s*(\d+)',
            r'宽\s*(\d+).*高\s*(\d+)',
        ]
        for pattern in size_patterns:
            match = re.search(pattern, text)
            if match:
                groups = match.groups()
                if len(groups) == 2:
                    return float(groups[0]), float(groups[1])
                elif len(groups) == 1:
                    r = float(groups[0])
                    return r * 2, r * 2
        return None

    def extract_position_hint(self, text: str) -> Optional[str]:
        positions = ["左", "右", "上", "下", "中间", "中心", "left", "right", "top", "bottom", "center"]
        for pos in positions:
            if pos in text.lower():
                return pos
        return None

    def process(self, raw_text: str) -> dict:
        corrected = self.correct_text(raw_text)
        cmd_type, confidence = self.extract_command_type(corrected)
        color = self.extract_color(corrected)
        shape = self.extract_shape(corrected)
        size = self.extract_size(corrected)
        position_hint = self.extract_position_hint(corrected)

        return {
            "original": raw_text,
            "corrected": corrected,
            "command_type": cmd_type,
            "confidence": confidence,
            "color": color,
            "shape": shape,
            "size": size,
            "position_hint": position_hint,
        }
