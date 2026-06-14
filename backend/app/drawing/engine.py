"""
程序化绘图引擎
生成高质量的绘图指令，不依赖 LLM
"""

import math
import random
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, Tuple


# ============ Perlin Noise 实现 ============
class PerlinNoise:
    """简易 2D Perlin Noise"""

    def __init__(self, seed: int = 0):
        self.perm = list(range(256))
        random.seed(seed)
        random.shuffle(self.perm)
        self.perm *= 2

    def _fade(self, t: float) -> float:
        return t * t * t * (t * (t * 6 - 15) + 10)

    def _lerp(self, a: float, b: float, t: float) -> float:
        return a + t * (b - a)

    def _grad(self, h: int, x: float, y: float) -> float:
        h = h & 3
        if h == 0:
            return x + y
        elif h == 1:
            return -x + y
        elif h == 2:
            return x - y
        else:
            return -x - y

    def noise(self, x: float, y: float) -> float:
        X = int(math.floor(x)) & 255
        Y = int(math.floor(y)) & 255
        x -= math.floor(x)
        y -= math.floor(y)
        u = self._fade(x)
        v = self._fade(y)
        A = self.perm[X] + Y
        B = self.perm[X + 1] + Y
        return self._lerp(
            self._lerp(self._grad(self.perm[A], x, y), self._grad(self.perm[B], x - 1, y), u),
            self._lerp(self._grad(self.perm[A + 1], x, y - 1), self._grad(self.perm[B + 1], x - 1, y - 1), u),
            v,
        )


# ============ 数据结构 ============
@dataclass
class DrawingInstruction:
    """单条绘图指令"""
    action: str  # "create", "clear", "background", "batch"
    shape_type: Optional[str] = None  # "circle", "rect", "path", "line", "gradient", etc.
    params: Dict[str, Any] = field(default_factory=dict)
    layer: int = 0


# ============ 配色系统 ============
PALETTES = {
    "sunset": [(255, 94, 77), (255, 154, 0), (255, 206, 84), (255, 100, 100), (200, 80, 120)],
    "ocean": [(0, 105, 148), (0, 150, 199), (72, 202, 228), (144, 224, 239), (202, 240, 248)],
    "forest": [(34, 87, 60), (52, 140, 90), (82, 180, 100), (120, 200, 130), (60, 120, 60)],
    "neon": [(255, 0, 128), (0, 255, 200), (128, 0, 255), (255, 255, 0), (0, 200, 255)],
    "pastel": [(255, 182, 193), (176, 224, 230), (221, 160, 221), (152, 251, 152), (255, 218, 185)],
    "warm": [(220, 50, 50), (255, 140, 0), (255, 200, 50), (255, 100, 80), (200, 80, 60)],
    "cool": [(50, 100, 200), (80, 180, 220), (100, 200, 200), (60, 140, 180), (40, 80, 160)],
    "monochrome": [(60, 60, 60), (100, 100, 100), (140, 140, 140), (180, 180, 180), (220, 220, 220)],
}


def _color_str(c: Tuple[int, int, int]) -> str:
    return f"rgb({c[0]},{c[1]},{c[2]})"


def _color_with_alpha(c: Tuple[int, int, int], a: float) -> str:
    return f"rgba({c[0]},{c[1]},{c[2]},{a:.2f})"


def _color_var(c: Tuple[int, int, int], v: float = 20) -> Tuple[int, int, int]:
    return (
        max(0, min(255, c[0] + random.uniform(-v, v))),
        max(0, min(255, c[1] + random.uniform(-v, v))),
        max(0, min(255, c[2] + random.uniform(-v, v))),
    )


# ============ 绘图引擎 ============
class DrawingEngine:
    def __init__(self, width: int = 1200, height: int = 800):
        self.width = width
        self.height = height
        self.shapes: List[Dict] = []
        self.background: Tuple[int, int, int] = (255, 255, 255)
        self.history: List[Tuple[List[Dict], Tuple[int, int, int]]] = [([], (255, 255, 255))]
        self.history_index: int = 0
        self.current_color: Tuple[int, int, int] = (50, 50, 50)
        self.current_size: float = 80
        self.noise = PerlinNoise(seed=random.randint(0, 10000))

    def _save_state(self):
        self.history = self.history[:self.history_index + 1]
        self.history.append(([s.copy() for s in self.shapes], self.background))
        self.history_index += 1
        if len(self.history) > 50:
            self.history.pop(0)
            self.history_index -= 1

    def undo(self) -> List[DrawingInstruction]:
        if self.history_index > 0:
            self.history_index -= 1
            self.shapes, self.background = self.history[self.history_index]
        return self._full_redraw()

    def redo(self) -> List[DrawingInstruction]:
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.shapes, self.background = self.history[self.history_index]
        return self._full_redraw()

    def clear(self) -> List[DrawingInstruction]:
        self._save_state()
        self.shapes = []
        self.background = (255, 255, 255)
        return [DrawingInstruction(action="clear")]

    def get_current_instructions(self) -> List[DrawingInstruction]:
        """获取当前画布的完整指令（用于重绘）"""
        return self._full_redraw()

    def _full_redraw(self) -> List[DrawingInstruction]:
        instructions = [DrawingInstruction(action="clear")]
        instructions.append(DrawingInstruction(
            action="background",
            params={"color": _color_str(self.background)},
        ))
        for shape in self.shapes:
            instructions.append(DrawingInstruction(
                action="create",
                shape_type=shape.get("type"),
                params=shape.get("params", {}),
                layer=shape.get("layer", 0),
            ))
        return instructions

    def _add_shape(self, shape_type: str, params: Dict, layer: int = 0):
        self.shapes.append({"type": shape_type, "params": params, "layer": layer})

    # ============ 基础图形 ============
    def draw_shape(self, shape_type: str, color: Optional[Tuple[int, int, int]] = None,
                   size: Optional[float] = None, position: Optional[Tuple[float, float]] = None) -> List[DrawingInstruction]:
        self._save_state()
        c = color or self.current_color
        s = size or self.current_size
        cx = position[0] * self.width if position else self.width / 2
        cy = position[1] * self.height if position else self.height / 2

        instructions = []
        params = {"cx": cx, "cy": cy, "color": _color_str(c), "fill": _color_with_alpha(c, 0.85)}

        if shape_type == "circle":
            params["radius"] = s / 2
            self._add_shape("circle", params)
            instructions.append(DrawingInstruction(action="create", shape_type="circle", params=params))

        elif shape_type == "rectangle" or shape_type == "square":
            w = s if shape_type == "square" else s * 1.3
            h = s if shape_type == "square" else s * 0.8
            params.update({"x": cx - w / 2, "y": cy - h / 2, "width": w, "height": h, "radius": 4})
            self._add_shape("rect", params)
            instructions.append(DrawingInstruction(action="create", shape_type="rect", params=params))

        elif shape_type == "triangle":
            r = s / 2
            pts = [
                {"x": cx, "y": cy - r},
                {"x": cx - r * 0.866, "y": cy + r * 0.5},
                {"x": cx + r * 0.866, "y": cy + r * 0.5},
            ]
            params["points"] = pts
            self._add_shape("polygon", params)
            instructions.append(DrawingInstruction(action="create", shape_type="polygon", params=params))

        elif shape_type == "star":
            pts = []
            for i in range(10):
                angle = math.pi / 2 + i * math.pi / 5
                r = s / 2 if i % 2 == 0 else s / 4.5
                pts.append({"x": cx + r * math.cos(angle), "y": cy - r * math.sin(angle)})
            params["points"] = pts
            self._add_shape("polygon", params)
            instructions.append(DrawingInstruction(action="create", shape_type="polygon", params=params))

        elif shape_type == "heart":
            points = []
            for t_val in range(0, 360, 3):
                t = math.radians(t_val)
                x = 16 * math.sin(t) ** 3
                y = -(13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))
                points.append({"x": cx + x * s / 34, "y": cy + y * s / 34})
            params["points"] = points
            self._add_shape("polygon", params)
            instructions.append(DrawingInstruction(action="create", shape_type="polygon", params=params))

        elif shape_type == "line":
            params.update({"x1": cx - s / 2, "y1": cy, "x2": cx + s / 2, "y2": cy, "strokeWidth": 3})
            self._add_shape("line", params)
            instructions.append(DrawingInstruction(action="create", shape_type="line", params=params))

        elif shape_type == "ellipse":
            params.update({"radiusX": s / 2, "radiusY": s / 3})
            self._add_shape("ellipse", params)
            instructions.append(DrawingInstruction(action="create", shape_type="ellipse", params=params))

        else:
            # 默认画圆
            params["radius"] = s / 2
            self._add_shape("circle", params)
            instructions.append(DrawingInstruction(action="create", shape_type="circle", params=params))

        return instructions

    # ============ 流场 ============
    def generate_flow_field(self, params: Optional[Dict] = None) -> List[DrawingInstruction]:
        self._save_state()
        params = params or {}
        particle_count = params.get("particle_count", 150)
        step_count = params.get("step_count", 50)
        scale = params.get("noise_scale", 0.005)
        palette_name = params.get("palette", "neon")
        palette = PALETTES.get(palette_name, PALETTES["neon"])
        append_mode = params.get("append", False)
        self.noise = PerlinNoise(seed=random.randint(0, 99999))

        instructions = []
        if not append_mode:
            self.shapes = []
            self.background = (15, 15, 25)
            instructions.append(DrawingInstruction(action="background", params={"color": _color_str(self.background)}))

        for _ in range(particle_count):
            x = random.uniform(0, self.width)
            y = random.uniform(0, self.height)
            c = random.choice(palette)
            points = [{"x": x, "y": y}]

            for _ in range(step_count):
                angle = self.noise.noise(x * scale, y * scale) * math.pi * 4
                x += math.cos(angle) * 2.5
                y += math.sin(angle) * 2.5
                if 0 <= x <= self.width and 0 <= y <= self.height:
                    points.append({"x": x, "y": y})
                else:
                    break

            if len(points) > 3:
                shape_params = {
                    "points": points,
                    "stroke": _color_with_alpha(c, 0.4),
                    "strokeWidth": random.uniform(1, 2.5),
                }
                self._add_shape("path", shape_params, layer=1)
                instructions.append(DrawingInstruction(action="create", shape_type="path", params=shape_params, layer=1))

        return instructions

    # ============ 分形树 ============
    def generate_fractal_tree(self, params: Optional[Dict] = None) -> List[DrawingInstruction]:
        self._save_state()
        params = params or {}
        depth = params.get("depth", 7)
        angle = params.get("branch_angle", 25)
        decay = params.get("length_decay", 0.72)
        start_len = params.get("start_length", 140)
        append_mode = params.get("append", False)

        instructions = []
        if not append_mode:
            self.shapes = []
            self.background = (240, 248, 255)
            instructions.append(DrawingInstruction(action="background", params={"color": _color_str(self.background)}))

        cx = self.width / 2
        base_y = self.height * 0.85

        def branch(x, y, len_, angle_deg, d):
            if d <= 0 or len_ < 3:
                return
            rad = math.radians(angle_deg)
            x2 = x + len_ * math.cos(rad)
            y2 = y - len_ * math.sin(rad)

            t = 1 - d / depth
            r = int(80 + t * 40)
            g = int(50 + t * 150)
            b = int(30 + t * 20)
            c = (min(255, r), min(255, g), min(255, b))
            width = max(1, d * 1.8)

            shape_params = {
                "x1": x, "y1": y, "x2": x2, "y2": y2,
                "stroke": _color_str(c),
                "strokeWidth": width,
            }
            self._add_shape("line", shape_params, layer=d)
            instructions.append(DrawingInstruction(action="create", shape_type="line", params=shape_params, layer=d))

            jitter = random.uniform(-8, 8)
            branch(x2, y2, len_ * decay, angle_deg - angle + jitter, d - 1)
            branch(x2, y2, len_ * decay, angle_deg + angle + jitter, d - 1)
            if d > 6 and random.random() > 0.5:
                branch(x2, y2, len_ * decay * 0.8, angle_deg + jitter, d - 2)

        branch(cx, base_y, start_len, 90, depth)
        return instructions

    # ============ 水彩效果 ============
    def generate_watercolor(self, params: Optional[Dict] = None) -> List[DrawingInstruction]:
        self._save_state()
        params = params or {}
        layers = params.get("layers", 15)
        color = params.get("color", (180, 100, 200))
        cx = params.get("cx", self.width / 2)
        cy = params.get("cy", self.height / 2)
        radius = params.get("radius", 150)
        append_mode = params.get("append", False)

        instructions = []
        if not append_mode:
            self.shapes = []
            self.background = (252, 250, 248)
            instructions.append(DrawingInstruction(action="background", params={"color": _color_str(self.background)}))

        for _ in range(layers):
            c = _color_var(color, 30)
            ox = cx + random.gauss(0, radius * 0.3)
            oy = cy + random.gauss(0, radius * 0.3)
            r = radius * random.uniform(0.3, 1.0)

            for _ in range(3):
                jx = ox + random.gauss(0, r * 0.15)
                jy = oy + random.gauss(0, r * 0.15)
                jr = r * random.uniform(0.6, 1.2)
                shape_params = {
                    "cx": jx, "cy": jy, "radius": jr,
                    "fill": _color_with_alpha(c, random.uniform(0.03, 0.07)),
                    "stroke": "transparent",
                }
                self._add_shape("circle", shape_params, layer=1)
                instructions.append(DrawingInstruction(action="create", shape_type="circle", params=shape_params, layer=1))

        return instructions

    # ============ 曼陀罗 ============
    def generate_mandala(self, params: Optional[Dict] = None) -> List[DrawingInstruction]:
        self._save_state()
        params = params or {}
        symmetry = params.get("symmetry", 12)
        rings = params.get("rings", 4)
        palette_name = params.get("palette", "neon")
        palette = PALETTES.get(palette_name, PALETTES["neon"])
        append_mode = params.get("append", False)

        instructions = []
        if not append_mode:
            self.shapes = []
            self.background = (10, 10, 20)
            instructions.append(DrawingInstruction(action="background", params={"color": _color_str(self.background)}))

        cx = self.width / 2
        cy = self.height / 2

        for ring in range(rings):
            base_r = 40 + ring * 60
            c = palette[ring % len(palette)]
            motif_type = ring % 3

            for i in range(symmetry):
                angle = (2 * math.pi / symmetry) * i + (ring * 0.1)
                px = cx + base_r * math.cos(angle)
                py = cy + base_r * math.sin(angle)

                if motif_type == 0:
                    r = 15 + ring * 5
                    shape_params = {"cx": px, "cy": py, "radius": r,
                                    "fill": _color_with_alpha(c, 0.7), "stroke": _color_str(c), "strokeWidth": 1.5}
                    self._add_shape("circle", shape_params, layer=ring)
                    instructions.append(DrawingInstruction(action="create", shape_type="circle", params=shape_params, layer=ring))

                elif motif_type == 1:
                    size = 10 + ring * 4
                    pts = []
                    for j in range(6):
                        a = angle + j * math.pi / 3
                        pts.append({"x": px + size * math.cos(a), "y": py + size * math.sin(a)})
                    shape_params = {"points": pts, "fill": _color_with_alpha(c, 0.6), "stroke": _color_str(c), "strokeWidth": 1}
                    self._add_shape("polygon", shape_params, layer=ring)
                    instructions.append(DrawingInstruction(action="create", shape_type="polygon", params=shape_params, layer=ring))

                else:
                    # 花瓣形状
                    petal_pts = []
                    for t_val in range(0, 360, 10):
                        t = math.radians(t_val)
                        r2 = (10 + ring * 3) * abs(math.cos(3 * t))
                        petal_pts.append({
                            "x": px + r2 * math.cos(t + angle),
                            "y": py + r2 * math.sin(t + angle),
                        })
                    shape_params = {"points": petal_pts, "fill": _color_with_alpha(c, 0.5), "stroke": _color_str(c), "strokeWidth": 1}
                    self._add_shape("polygon", shape_params, layer=ring)
                    instructions.append(DrawingInstruction(action="create", shape_type="polygon", params=shape_params, layer=ring))

        # 中心装饰
        for i in range(8):
            a = i * math.pi / 4
            c = palette[i % len(palette)]
            shape_params = {
                "cx": cx + 25 * math.cos(a), "cy": cy + 25 * math.sin(a), "radius": 8,
                "fill": _color_with_alpha(c, 0.9), "stroke": "transparent",
            }
            self._add_shape("circle", shape_params, layer=rings + 1)
            instructions.append(DrawingInstruction(action="create", shape_type="circle", params=shape_params, layer=rings + 1))

        return instructions

    # ============ 螺线 ============
    def generate_spirograph(self, params: Optional[Dict] = None) -> List[DrawingInstruction]:
        self._save_state()
        params = params or {}
        R = params.get("R", 100)
        r = params.get("r", 63)
        d = params.get("d", 80)
        color = params.get("color", (80, 60, 200))
        append_mode = params.get("append", False)

        instructions = []
        if not append_mode:
            self.shapes = []
            self.background = (15, 15, 30)
            instructions.append(DrawingInstruction(action="background", params={"color": _color_str(self.background)}))

        cx = self.width / 2
        cy = self.height / 2
        points = []
        steps = 3000
        for i in range(steps):
            t = i * 2 * math.pi / steps * (R / math.gcd(R, r) if math.gcd(R, r) > 0 else 1)
            x = cx + (R - r) * math.cos(t) + d * math.cos((R - r) * t / r)
            y = cy + (R - r) * math.sin(t) - d * math.sin((R - r) * t / r)
            points.append({"x": x, "y": y})

        c_var = _color_var(color, 20)
        shape_params = {"points": points, "stroke": _color_with_alpha(c_var, 0.8), "strokeWidth": 1.5}
        self._add_shape("path", shape_params, layer=1)
        instructions.append(DrawingInstruction(action="create", shape_type="path", params=shape_params, layer=1))

        # 添加第二层螺线
        points2 = []
        for i in range(steps):
            t = i * 2 * math.pi / steps
            x = cx + (R - r + 20) * math.cos(t) + d * 0.7 * math.cos((R - r + 20) * t / r)
            y = cy + (R - r + 20) * math.sin(t) - d * 0.7 * math.sin((R - r + 20) * t / r)
            points2.append({"x": x, "y": y})

        c2 = _color_var(color, 40)
        shape_params2 = {"points": points2, "stroke": _color_with_alpha(c2, 0.5), "strokeWidth": 1}
        self._add_shape("path", shape_params2, layer=0)
        instructions.append(DrawingInstruction(action="create", shape_type="path", params=shape_params2, layer=0))

        return instructions

    # ============ 沃罗诺伊 ============
    def generate_voronoi(self, params: Optional[Dict] = None) -> List[DrawingInstruction]:
        self._save_state()
        params = params or {}
        seed_count = params.get("seed_count", 25)
        palette_name = params.get("palette", "pastel")
        palette = PALETTES.get(palette_name, PALETTES["pastel"])
        append_mode = params.get("append", False)

        instructions = []
        if not append_mode:
            self.shapes = []
            self.background = (255, 255, 255)
            instructions.append(DrawingInstruction(action="background", params={"color": _color_str(self.background)}))

        seeds = [(random.uniform(0, self.width), random.uniform(0, self.height)) for _ in range(seed_count)]
        colors = [_color_var(random.choice(palette), 15) for _ in range(seed_count)]

        # 网格采样近似 Voronoi
        step = 30
        for y in range(0, self.height, step):
            for x in range(0, self.width, step):
                min_d = float('inf')
                min_i = 0
                for i, (sx, sy) in enumerate(seeds):
                    d = (x - sx) ** 2 + (y - sy) ** 2
                    if d < min_d:
                        min_d = d
                        min_i = i
                shape_params = {
                    "x": x, "y": y, "width": step, "height": step,
                    "fill": _color_with_alpha(colors[min_i], 0.85),
                    "stroke": "transparent",
                }
                self._add_shape("rect", shape_params, layer=0)

        # 绘制种子点
        for sx, sy in seeds:
            shape_params = {"cx": sx, "cy": sy, "radius": 4, "fill": "rgba(0,0,0,0.6)", "stroke": "transparent"}
            self._add_shape("circle", shape_params, layer=1)

        # 批量指令
        instructions.append(DrawingInstruction(
            action="batch",
            params={"shapes": self.shapes.copy()},
            layer=0,
        ))
        return instructions

    # ============ 粒子效果 ============
    def generate_particle(self, params: Optional[Dict] = None) -> List[DrawingInstruction]:
        self._save_state()
        params = params or {}
        palette_name = params.get("palette", "neon")
        palette = PALETTES.get(palette_name, PALETTES["neon"])
        append_mode = params.get("append", False)

        instructions = []
        if not append_mode:
            self.shapes = []
            self.background = (15, 15, 30)
            instructions.append(DrawingInstruction(action="background", params={"color": _color_str(self.background)}))

        cx, cy = self.width / 2, self.height / 2
        particle_count = params.get("count", 80)

        for _ in range(particle_count):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(20, 200)
            x = cx + math.cos(angle) * speed
            y = cy + math.sin(angle) * speed
            radius = random.uniform(1.5, 6)
            color = _color_with_alpha(random.choice(palette), random.uniform(0.4, 0.9))
            shape_params = {"cx": x, "cy": y, "radius": radius, "fill": color, "stroke": "transparent"}
            self._add_shape("circle", shape_params, layer=0)

        # 添加几条射线
        for _ in range(8):
            angle = random.uniform(0, math.pi * 2)
            length = random.uniform(100, 300)
            x2 = cx + math.cos(angle) * length
            y2 = cy + math.sin(angle) * length
            color = _color_with_alpha(random.choice(palette), 0.3)
            shape_params = {"x1": cx, "y1": cy, "x2": x2, "y2": y2, "stroke": color, "strokeWidth": random.uniform(0.5, 2)}
            self._add_shape("line", shape_params, layer=1)

        instructions.append(DrawingInstruction(action="batch", params={"shapes": self.shapes.copy()}, layer=0))
        return instructions

    # ============ 波浪 ============
    def generate_wave(self, params: Optional[Dict] = None) -> List[DrawingInstruction]:
        self._save_state()
        params = params or {}
        palette_name = params.get("palette", "ocean")
        palette = PALETTES.get(palette_name, PALETTES["ocean"])
        append_mode = params.get("append", False)

        instructions = []
        if not append_mode:
            self.shapes = []
            self.background = (240, 248, 255)
            instructions.append(DrawingInstruction(action="background", params={"color": _color_str(self.background)}))

        wave_count = 12
        for i in range(wave_count):
            y_base = 100 + i * (self.height - 200) / wave_count
            amplitude = random.uniform(15, 40)
            frequency = random.uniform(0.005, 0.015)
            phase = random.uniform(0, math.pi * 2)
            color = _color_with_alpha(random.choice(palette), random.uniform(0.3, 0.7))

            points = []
            for x in range(0, self.width + 1, 4):
                y = y_base + math.sin(x * frequency + phase) * amplitude
                y += math.sin(x * frequency * 2.3 + phase * 1.7) * amplitude * 0.3
                points.append({"x": x, "y": y})

            shape_params = {"points": points, "stroke": color, "strokeWidth": random.uniform(1.5, 3.5)}
            self._add_shape("path", shape_params, layer=i)

        instructions.append(DrawingInstruction(action="batch", params={"shapes": self.shapes.copy()}, layer=0))
        return instructions

    # ============ 条纹 ============
    def generate_stripe(self, params: Optional[Dict] = None) -> List[DrawingInstruction]:
        self._save_state()
        params = params or {}
        palette_name = params.get("palette", "warm")
        palette = PALETTES.get(palette_name, PALETTES["warm"])
        append_mode = params.get("append", False)

        instructions = []
        if not append_mode:
            self.shapes = []
            self.background = (255, 255, 255)
            instructions.append(DrawingInstruction(action="background", params={"color": _color_str(self.background)}))

        stripe_type = random.choice(["horizontal", "vertical", "diagonal", "wave"])

        if stripe_type == "horizontal":
            stripe_h = random.randint(15, 40)
            for y in range(0, self.height, stripe_h * 2):
                color = _color_with_alpha(random.choice(palette), random.uniform(0.6, 0.9))
                shape_params = {"x": 0, "y": y, "width": self.width, "height": stripe_h, "fill": color, "stroke": "transparent"}
                self._add_shape("rect", shape_params, layer=0)

        elif stripe_type == "vertical":
            stripe_w = random.randint(15, 40)
            for x in range(0, self.width, stripe_w * 2):
                color = _color_with_alpha(random.choice(palette), random.uniform(0.6, 0.9))
                shape_params = {"x": x, "y": 0, "width": stripe_w, "height": self.height, "fill": color, "stroke": "transparent"}
                self._add_shape("rect", shape_params, layer=0)

        elif stripe_type == "diagonal":
            stripe_w = random.randint(20, 50)
            for i in range(-self.height, self.width + self.height, stripe_w * 2):
                points = [
                    {"x": i, "y": 0},
                    {"x": i + stripe_w, "y": 0},
                    {"x": i + stripe_w - self.height, "y": self.height},
                    {"x": i - self.height, "y": self.height},
                ]
                color = _color_with_alpha(random.choice(palette), random.uniform(0.5, 0.8))
                shape_params = {"points": points, "fill": color, "stroke": "transparent"}
                self._add_shape("polygon", shape_params, layer=0)

        else:  # wave
            for i in range(10):
                y_base = i * self.height / 10
                points = []
                for x in range(0, self.width + 1, 5):
                    y = y_base + math.sin(x * 0.02 + i) * 20
                    points.append({"x": x, "y": y})
                for x in range(self.width, -1, -5):
                    y = y_base + self.height / 12 + math.sin(x * 0.02 + i) * 20
                    points.append({"x": x, "y": y})
                color = _color_with_alpha(random.choice(palette), random.uniform(0.4, 0.7))
                shape_params = {"points": points, "fill": color, "stroke": "transparent"}
                self._add_shape("polygon", shape_params, layer=0)

        instructions.append(DrawingInstruction(action="batch", params={"shapes": self.shapes.copy()}, layer=0))
        return instructions

    # ============ 渐变 ============
    def generate_gradient(self, params: Optional[Dict] = None) -> List[DrawingInstruction]:
        self._save_state()
        params = params or {}
        palette_name = params.get("palette", "sunset")
        palette = PALETTES.get(palette_name, PALETTES["sunset"])
        append_mode = params.get("append", False)

        instructions = []
        if not append_mode:
            self.shapes = []
            self.background = palette[0]
            instructions.append(DrawingInstruction(action="background", params={"color": _color_str(self.background)}))

        gradient_type = random.choice(["linear", "radial", "conic"])

        if gradient_type == "linear":
            direction = random.choice(["vertical", "horizontal", "diagonal"])
            steps = 40
            for i in range(steps):
                t = i / (steps - 1)
                c1 = palette[0] if len(palette) > 0 else (255, 255, 255)
                c2 = palette[1] if len(palette) > 1 else (0, 0, 0)
                r = int(c1[0] + (c2[0] - c1[0]) * t)
                g = int(c1[1] + (c2[1] - c1[1]) * t)
                b = int(c1[2] + (c2[2] - c1[2]) * t)
                color = f"rgb({r},{g},{b})"

                if direction == "vertical":
                    h = self.height // steps + 1
                    shape_params = {"x": 0, "y": i * self.height // steps, "width": self.width, "height": h, "fill": color, "stroke": "transparent"}
                elif direction == "horizontal":
                    w = self.width // steps + 1
                    shape_params = {"x": i * self.width // steps, "y": 0, "width": w, "height": self.height, "fill": color, "stroke": "transparent"}
                else:
                    h = self.height // steps + 1
                    shape_params = {"x": 0, "y": i * self.height // steps, "width": self.width, "height": h, "fill": color, "stroke": "transparent"}
                self._add_shape("rect", shape_params, layer=0)

        elif gradient_type == "radial":
            cx, cy = self.width / 2, self.height / 2
            max_r = max(self.width, self.height) / 2
            steps = 30
            for i in range(steps, 0, -1):
                t = i / steps
                r = max_r * t
                c1 = palette[0] if len(palette) > 0 else (255, 255, 255)
                c2 = palette[1] if len(palette) > 1 else (0, 0, 0)
                cr = int(c1[0] + (c2[0] - c1[0]) * (1 - t))
                cg = int(c1[1] + (c2[1] - c1[1]) * (1 - t))
                cb = int(c1[2] + (c2[2] - c1[2]) * (1 - t))
                color = f"rgb({cr},{cg},{cb})"
                shape_params = {"cx": cx, "cy": cy, "radius": r, "fill": color, "stroke": "transparent"}
                self._add_shape("circle", shape_params, layer=0)

        else:  # conic
            cx, cy = self.width / 2, self.height / 2
            max_r = max(self.width, self.height) * 0.6
            steps = 36
            for i in range(steps):
                angle1 = i * math.pi * 2 / steps
                angle2 = (i + 1) * math.pi * 2 / steps
                t = i / steps
                ci = int(t * len(palette)) % len(palette) if palette else 0
                ci_next = (ci + 1) % len(palette) if palette else 0
                color = _color_with_alpha(palette[ci] if palette else (200, 200, 200), 0.8)
                points = [
                    {"x": cx, "y": cy},
                    {"x": cx + math.cos(angle1) * max_r, "y": cy + math.sin(angle1) * max_r},
                    {"x": cx + math.cos(angle2) * max_r, "y": cy + math.sin(angle2) * max_r},
                ]
                shape_params = {"points": points, "fill": color, "stroke": "transparent"}
                self._add_shape("polygon", shape_params, layer=0)

        instructions.append(DrawingInstruction(action="batch", params={"shapes": self.shapes.copy()}, layer=0))
        return instructions

    # ============ 风景场景 ============
    def generate_landscape(self, scene_type: str = "sunset", params: Optional[Dict] = None) -> List[DrawingInstruction]:
        self._save_state()
        params = params or {}
        append_mode = params.get("append", False)

        if not append_mode:
            self.shapes = []

        generators = {
            "sunset": self._gen_sunset,
            "ocean": self._gen_ocean,
            "mountain": self._gen_mountain,
            "starry_sky": self._gen_starry_sky,
            "forest": self._gen_forest,
            "grassland": self._gen_grassland,
            "desert": self._gen_desert,
            "snow": self._gen_snow,
            "spring": self._gen_spring,
        }

        gen_func = generators.get(scene_type, self._gen_sunset)
        instructions = gen_func(params)
        return instructions

    def _gen_sunset(self, params: Dict) -> List[DrawingInstruction]:
        instructions = []
        self.background = (20, 10, 40)
        instructions.append(DrawingInstruction(action="background", params={"color": _color_str(self.background)}))

        # 天空渐变（多层）
        gradient_stops = [
            (0.0, (20, 10, 40)), (0.3, (80, 30, 80)),
            (0.5, (200, 80, 60)), (0.65, (255, 150, 50)),
            (0.8, (255, 200, 100)), (1.0, (255, 230, 180)),
        ]
        h_stripes = 60
        for i in range(h_stripes):
            t = i / h_stripes
            c = self._interpolate_gradient(t, gradient_stops)
            y = t * self.height * 0.65
            shape_params = {
                "x": 0, "y": y, "width": self.width, "height": self.height * 0.65 / h_stripes + 1,
                "fill": _color_str(c), "stroke": "transparent",
            }
            self._add_shape("rect", shape_params, layer=0)
        instructions.append(DrawingInstruction(action="batch", params={"shapes": [s for s in self.shapes if s.get("layer") == 0]}, layer=0))

        # 太阳
        sun_x = self.width * 0.5
        sun_y = self.height * 0.48
        for r in range(60, 0, -3):
            alpha = 0.02 + (60 - r) / 60 * 0.08
            shape_params = {
                "cx": sun_x, "cy": sun_y, "radius": r,
                "fill": _color_with_alpha((255, 220, 100), alpha), "stroke": "transparent",
            }
            self._add_shape("circle", shape_params, layer=1)
        # 太阳核心
        shape_params = {"cx": sun_x, "cy": sun_y, "radius": 30, "fill": "rgb(255,240,200)", "stroke": "transparent"}
        self._add_shape("circle", shape_params, layer=2)
        instructions.append(DrawingInstruction(action="batch", params={"shapes": [s for s in self.shapes if s["layer"] in (1, 2)]}, layer=1))

        # 山脉
        for layer_i, (y_base, color, alpha) in enumerate([
            (0.6, (60, 30, 50), 0.9), (0.65, (40, 20, 40), 0.95), (0.7, (25, 15, 30), 1.0),
        ]):
            pts = self._generate_mountain_points(y_base, 0.08 + layer_i * 0.02)
            shape_params = {"points": pts, "fill": _color_with_alpha(color, alpha), "stroke": "transparent"}
            self._add_shape("polygon", shape_params, layer=3 + layer_i)
        instructions.append(DrawingInstruction(action="batch", params={"shapes": [s for s in self.shapes if s["layer"] >= 3]}, layer=3))

        # 海面反射
        for i in range(20):
            y = self.height * 0.72 + i * (self.height * 0.28 / 20)
            t = i / 20
            c = self._interpolate_gradient(t, [(0, (200, 130, 80)), (0.5, (100, 60, 80)), (1, (30, 20, 50))])
            shape_params = {
                "x": 0, "y": y, "width": self.width, "height": self.height * 0.28 / 60 + 1,
                "fill": _color_with_alpha(c, 0.7), "stroke": "transparent",
            }
            self._add_shape("rect", shape_params, layer=7)
        instructions.append(DrawingInstruction(action="batch", params={"shapes": [s for s in self.shapes if s["layer"] == 7]}, layer=7))

        return instructions

    def _gen_ocean(self, params: Dict) -> List[DrawingInstruction]:
        instructions = []
        self.background = (135, 206, 235)
        instructions.append(DrawingInstruction(action="background", params={"color": _color_str(self.background)}))

        # 海面
        for i in range(30):
            y = self.height * 0.4 + i * (self.height * 0.6 / 30)
            t = i / 30
            r = int(0 + t * 30)
            g = int(105 + t * 50)
            b = int(180 - t * 30)
            shape_params = {
                "x": 0, "y": y, "width": self.width, "height": self.height * 0.6 / 80 + 1,
                "fill": _color_str((r, g, b)), "stroke": "transparent",
            }
            self._add_shape("rect", shape_params, layer=0)

        # 波浪线
        for wave_i in range(8):
            y_base = self.height * 0.45 + wave_i * 25
            pts = []
            for x in range(0, self.width, 3):
                y = y_base + math.sin(x * 0.02 + wave_i * 0.5) * 8
                pts.append({"x": x, "y": y})
            alpha = 0.3 - wave_i * 0.015
            shape_params = {"points": pts, "stroke": _color_with_alpha((255, 255, 255), max(0.05, alpha)), "strokeWidth": 2}
            self._add_shape("path", shape_params, layer=1)

        instructions.append(DrawingInstruction(action="batch", params={"shapes": self.shapes.copy()}, layer=0))
        return instructions

    def _gen_mountain(self, params: Dict) -> List[DrawingInstruction]:
        instructions = []
        self.background = (200, 220, 240)
        instructions.append(DrawingInstruction(action="background", params={"color": _color_str(self.background)}))

        for i, (y_base, color, amp) in enumerate([
            (0.35, (180, 200, 210), 0.15), (0.45, (120, 150, 160), 0.12),
            (0.55, (80, 110, 100), 0.1), (0.65, (50, 80, 60), 0.08),
        ]):
            pts = self._generate_mountain_points(y_base, amp)
            shape_params = {"points": pts, "fill": _color_str(color), "stroke": "transparent"}
            self._add_shape("polygon", shape_params, layer=i)

        # 草地
        shape_params = {
            "x": 0, "y": self.height * 0.7, "width": self.width, "height": self.height * 0.3,
            "fill": "rgb(80,140,70)", "stroke": "transparent",
        }
        self._add_shape("rect", shape_params, layer=4)

        instructions.append(DrawingInstruction(action="batch", params={"shapes": self.shapes.copy()}, layer=0))
        return instructions

    def _gen_starry_sky(self, params: Dict) -> List[DrawingInstruction]:
        instructions = []
        self.background = (5, 5, 20)
        instructions.append(DrawingInstruction(action="background", params={"color": _color_str(self.background)}))

        # 银河光带（淡淡的斜向椭圆区域）
        milky_cx = self.width * 0.5
        milky_cy = self.height * 0.35
        for _ in range(40):
            angle = random.uniform(-0.4, 0.4)
            dist = random.uniform(-300, 300)
            x = milky_cx + dist * math.cos(angle) + random.gauss(0, 60)
            y = milky_cy + dist * math.sin(angle) + random.gauss(0, 25)
            if 0 < x < self.width and 0 < y < self.height * 0.7:
                r = random.uniform(15, 50)
                alpha = random.uniform(0.01, 0.03)
                shape_params = {"cx": x, "cy": y, "radius": r, "fill": _color_with_alpha((180, 200, 255), alpha), "stroke": "transparent"}
                self._add_shape("circle", shape_params, layer=0)

        # 背景小星星（密密麻麻）
        for _ in range(120):
            x = random.uniform(0, self.width)
            y = random.uniform(0, self.height * 0.75)
            r = random.uniform(0.3, 1.5)
            alpha = random.uniform(0.3, 0.8)
            shape_params = {"cx": x, "cy": y, "radius": r, "fill": _color_with_alpha((255, 255, 240), alpha), "stroke": "transparent"}
            self._add_shape("circle", shape_params, layer=1)

        # 中等亮度星星
        for _ in range(30):
            x = random.uniform(0, self.width)
            y = random.uniform(0, self.height * 0.7)
            r = random.uniform(1.5, 3.0)
            alpha = random.uniform(0.6, 1.0)
            # 偶尔有颜色偏移（偏蓝/偏红）
            c = random.choice([(255, 255, 240), (200, 220, 255), (255, 220, 200)])
            shape_params = {"cx": x, "cy": y, "radius": r, "fill": _color_with_alpha(c, alpha), "stroke": "transparent"}
            self._add_shape("circle", shape_params, layer=2)

        # 大亮星（带光晕）
        for _ in range(6):
            x = random.uniform(50, self.width - 50)
            y = random.uniform(30, self.height * 0.5)
            star_color = random.choice([(200, 220, 255), (255, 240, 220), (220, 200, 255)])
            for r in range(12, 0, -1):
                alpha = 0.02 + (12 - r) / 12 * 0.12
                shape_params = {"cx": x, "cy": y, "radius": r, "fill": _color_with_alpha(star_color, alpha), "stroke": "transparent"}
                self._add_shape("circle", shape_params, layer=3)
            # 核心亮点
            shape_params = {"cx": x, "cy": y, "radius": 2, "fill": "rgb(255,255,255)", "stroke": "transparent"}
            self._add_shape("circle", shape_params, layer=4)

        # 月亮（带大气光晕）
        mx, my = self.width * 0.82, self.height * 0.12
        for r in range(40, 0, -1):
            alpha = 0.01 + (40 - r) / 40 * 0.04
            shape_params = {"cx": mx, "cy": my, "radius": r, "fill": _color_with_alpha((255, 250, 220), alpha), "stroke": "transparent"}
            self._add_shape("circle", shape_params, layer=5)
        shape_params = {"cx": mx, "cy": my, "radius": 18, "fill": "rgb(255,250,230)", "stroke": "transparent"}
        self._add_shape("circle", shape_params, layer=6)

        # 流星雨
        for _ in range(8):
            # 起点在右上区域
            sx = random.uniform(self.width * 0.3, self.width * 0.95)
            sy = random.uniform(20, self.height * 0.35)
            # 向左下拖尾
            tail_len = random.uniform(80, 200)
            angle = random.uniform(0.6, 1.0)  # 斜向左下
            ex = sx - tail_len * math.cos(angle)
            ey = sy + tail_len * math.sin(angle)

            # 流星拖尾（渐变线条，从亮到暗）
            segments = 8
            for s in range(segments):
                t1 = s / segments
                t2 = (s + 1) / segments
                x1 = sx + (ex - sx) * t1
                y1 = sy + (ey - sy) * t1
                x2 = sx + (ex - sx) * t2
                y2 = sy + (ey - sy) * t2
                alpha = 0.8 * (1 - t1)  # 头亮尾暗
                width = 2.5 * (1 - t1 * 0.7)  # 头粗尾细
                shape_params = {
                    "x1": x1, "y1": y1, "x2": x2, "y2": y2,
                    "stroke": _color_with_alpha((220, 240, 255), alpha),
                    "strokeWidth": width,
                }
                self._add_shape("line", shape_params, layer=7)

            # 流星头部亮点
            shape_params = {"cx": sx, "cy": sy, "radius": 3, "fill": _color_with_alpha((255, 255, 255), 0.9), "stroke": "transparent"}
            self._add_shape("circle", shape_params, layer=8)
            # 头部光晕
            shape_params = {"cx": sx, "cy": sy, "radius": 8, "fill": _color_with_alpha((200, 220, 255), 0.15), "stroke": "transparent"}
            self._add_shape("circle", shape_params, layer=8)

        instructions.append(DrawingInstruction(action="batch", params={"shapes": self.shapes.copy()}, layer=0))
        return instructions

    def _gen_forest(self, params: Dict) -> List[DrawingInstruction]:
        instructions = []
        self.background = (200, 230, 210)
        instructions.append(DrawingInstruction(action="background", params={"color": _color_str(self.background)}))

        # 简化：用三角形树
        for _ in range(12):
            tx = random.uniform(50, self.width - 50)
            ty = random.uniform(self.height * 0.3, self.height * 0.7)
            h = random.uniform(80, 180)
            c = _color_var((30, 100, 40), 30)

            for j in range(3):
                layer_h = h * (3 - j) / 3
                layer_w = layer_h * 0.6
                pts = [
                    {"x": tx, "y": ty - h + j * h * 0.2},
                    {"x": tx - layer_w / 2, "y": ty - h + j * h * 0.2 + layer_h * 0.5},
                    {"x": tx + layer_w / 2, "y": ty - h + j * h * 0.2 + layer_h * 0.5},
                ]
                shape_params = {"points": pts, "fill": _color_str(_color_var(c, 15)), "stroke": "transparent"}
                self._add_shape("polygon", shape_params, layer=j)

            # 树干
            shape_params = {"x": tx - 5, "y": ty - 20, "width": 10, "height": 30, "fill": "rgb(100,70,40)", "stroke": "transparent"}
            self._add_shape("rect", shape_params, layer=3)

        instructions.append(DrawingInstruction(action="batch", params={"shapes": self.shapes.copy()}, layer=0))
        return instructions

    def _gen_grassland(self, params: Dict) -> List[DrawingInstruction]:
        instructions = []
        self.background = (180, 220, 255)
        instructions.append(DrawingInstruction(action="background", params={"color": _color_str(self.background)}))

        # 草地
        for i in range(40):
            y = self.height * 0.5 + i * (self.height * 0.5 / 40)
            c = _color_var((100, 180, 60), 20)
            shape_params = {"x": 0, "y": y, "width": self.width, "height": self.height * 0.5 / 100 + 1, "fill": _color_str(c), "stroke": "transparent"}
            self._add_shape("rect", shape_params, layer=0)

        # 草叶
        for _ in range(60):
            x = random.uniform(0, self.width)
            y = random.uniform(self.height * 0.55, self.height * 0.95)
            h = random.uniform(15, 40)
            angle = random.uniform(-0.3, 0.3)
            shape_params = {
                "x1": x, "y1": y, "x2": x + math.sin(angle) * h, "y2": y - h,
                "stroke": _color_str(_color_var((80, 160, 40), 20)), "strokeWidth": 2,
            }
            self._add_shape("line", shape_params, layer=1)

        instructions.append(DrawingInstruction(action="batch", params={"shapes": self.shapes.copy()}, layer=0))
        return instructions

    def _gen_desert(self, params: Dict) -> List[DrawingInstruction]:
        instructions = []
        self.background = (240, 220, 190)
        instructions.append(DrawingInstruction(action="background", params={"color": _color_str(self.background)}))

        for i in range(40):
            y = self.height * 0.3 + i * (self.height * 0.7 / 40)
            c = _color_var((220, 190, 140), 15)
            shape_params = {"x": 0, "y": y, "width": self.width, "height": self.height * 0.7 / 100 + 1, "fill": _color_str(c), "stroke": "transparent"}
            self._add_shape("rect", shape_params, layer=0)

        instructions.append(DrawingInstruction(action="batch", params={"shapes": self.shapes.copy()}, layer=0))
        return instructions

    def _gen_snow(self, params: Dict) -> List[DrawingInstruction]:
        instructions = []
        self.background = (220, 230, 245)
        instructions.append(DrawingInstruction(action="background", params={"color": _color_str(self.background)}))

        # 雪山
        pts = self._generate_mountain_points(0.3, 0.2)
        shape_params = {"points": pts, "fill": "rgb(240,245,255)", "stroke": "transparent"}
        self._add_shape("polygon", shape_params, layer=0)

        # 雪花
        for _ in range(60):
            x = random.uniform(0, self.width)
            y = random.uniform(0, self.height)
            r = random.uniform(1, 4)
            shape_params = {"cx": x, "cy": y, "radius": r, "fill": _color_with_alpha((255, 255, 255), 0.8), "stroke": "transparent"}
            self._add_shape("circle", shape_params, layer=1)

        instructions.append(DrawingInstruction(action="batch", params={"shapes": self.shapes.copy()}, layer=0))
        return instructions

    def _gen_spring(self, params: Dict) -> List[DrawingInstruction]:
        instructions = []
        self.background = (230, 245, 255)
        instructions.append(DrawingInstruction(action="background", params={"color": _color_str(self.background)}))

        # 草地
        shape_params = {"x": 0, "y": self.height * 0.6, "width": self.width, "height": self.height * 0.4, "fill": "rgb(150,220,100)", "stroke": "transparent"}
        self._add_shape("rect", shape_params, layer=0)

        # 花朵
        flower_colors = [(255, 150, 180), (255, 200, 100), (200, 150, 255), (255, 120, 120), (255, 180, 200)]
        for _ in range(30):
            x = random.uniform(30, self.width - 30)
            y = random.uniform(self.height * 0.55, self.height * 0.9)
            c = random.choice(flower_colors)
            r = random.uniform(4, 10)
            shape_params = {"cx": x, "cy": y, "radius": r, "fill": _color_with_alpha(c, 0.85), "stroke": "transparent"}
            self._add_shape("circle", shape_params, layer=1)

        instructions.append(DrawingInstruction(action="batch", params={"shapes": self.shapes.copy()}, layer=0))
        return instructions

    # ============ 辅助方法 ============
    def _generate_mountain_points(self, y_ratio: float, amplitude: float) -> List[Dict]:
        """生成山脉轮廓点"""
        pts = [{"x": 0, "y": self.height}]
        y_base = self.height * y_ratio
        steps = 100
        for i in range(steps + 1):
            x = i * self.width / steps
            noise_val = self.noise.noise(x * 0.003, y_ratio * 10)
            y = y_base - abs(noise_val) * self.height * amplitude
            pts.append({"x": x, "y": y})
        pts.append({"x": self.width, "y": self.height})
        return pts

    def _interpolate_gradient(self, t: float, stops: List[Tuple[float, Tuple[int, int, int]]]) -> Tuple[int, int, int]:
        """在渐变色标中插值"""
        t = max(0, min(1, t))
        for i in range(len(stops) - 1):
            if stops[i][0] <= t <= stops[i + 1][0]:
                local_t = (t - stops[i][0]) / (stops[i + 1][0] - stops[i][0])
                c1 = stops[i][1]
                c2 = stops[i + 1][1]
                return (
                    int(c1[0] + (c2[0] - c1[0]) * local_t),
                    int(c1[1] + (c2[1] - c1[1]) * local_t),
                    int(c1[2] + (c2[2] - c1[2]) * local_t),
                )
        return stops[-1][1]

    # ============ 状态管理 ============
    def get_state(self) -> Dict:
        return {
            "width": self.width,
            "height": self.height,
            "background": _color_str(self.background),
            "shape_count": len(self.shapes),
            "shapes": self.shapes[:100],  # 限制返回数量
        }

    def export_instructions(self) -> List[Dict]:
        return [asdict(inst) for inst in self._full_redraw()]
