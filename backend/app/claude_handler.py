import os
import json
from typing import List, Dict, Any
from anthropic import Anthropic
from .models import (
    DrawingAction, AIResponse, Shape, ShapeType, Position, Color
)


class ClaudeHandler:
    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        self.client = Anthropic(api_key=api_key) if api_key else None
        self.conversation_history: List[Dict[str, str]] = []

    def _build_system_prompt(self, scene_state: Dict[str, Any]) -> str:
        shapes_desc = ""
        for s in scene_state.get("shapes", []):
            name = s.get("name", s.get("id", "unknown"))
            shapes_desc += f"- {name} ({s['type']}) at ({s['position']['x']}, {s['position']['y']})\n"

        return f"""You are an AI drawing assistant. Convert natural language commands into drawing actions.

Current scene state:
- Canvas size: {scene_state.get('width', 800)}x{scene_state.get('height', 600)}
- Background: rgb({scene_state.get('background', {}).get('r', 255)}, {scene_state.get('background', {}).get('g', 255)}, {scene_state.get('background', {}).get('b', 255)})
- Existing shapes:
{shapes_desc if shapes_desc else "  (empty canvas)"}

Respond with JSON containing:
{{
    "actions": [
        {{
            "action": "create" | "move" | "delete" | "modify" | "clear",
            "shape": {{  // for create
                "type": "circle" | "rectangle" | "line" | "triangle" | "polygon" | "text",
                "position": {{"x": number, "y": number}},
                "name": "descriptive_name",
                "color": {{"r": 0-255, "g": 0-255, "b": 0-255}},
                "fill": true/false,
                "width": number,
                "height": number,
                "radius": number,
                "text": "string",
                "zIndex": number
            }},
            "target_name": "name of existing shape",  // for move/delete/modify
            "position": {{"x": number, "y": number}},  // for move
            "properties": {{}}  // for modify
        }}
    ],
    "explanation": "Brief explanation in Chinese of what you did",
    "scene_description": "Description of the full scene"
}}

Important:
- Use descriptive names like "sun", "house", "tree" so user can reference them later
- Positions should be within canvas bounds (0-800 x, 0-600 y)
- For complex scenes, break into multiple shapes
- Use zIndex for layering (higher = on top)
- Be creative with colors and positioning"""

    async def process_command(
        self, command: str, scene_state: Dict[str, Any]
    ) -> AIResponse:
        system_prompt = self._build_system_prompt(scene_state)

        messages = self.conversation_history.copy()
        messages.append({"role": "user", "content": command})

        try:
            if not self.client:
                return self._fallback_parse(command, scene_state)

            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                system=system_prompt,
                messages=messages,
            )

            response_text = response.content[0].text
            self.conversation_history.append({"role": "user", "content": command})
            self.conversation_history.append(
                {"role": "assistant", "content": response_text}
            )

            if len(self.conversation_history) > 20:
                self.conversation_history = self.conversation_history[-20:]

            return self._parse_response(response_text)

        except Exception as e:
            print(f"Claude API error: {e}")
            return self._fallback_parse(command, scene_state)

    def _parse_response(self, text: str) -> AIResponse:
        try:
            json_start = text.find("{")
            json_end = text.rfind("}") + 1
            if json_start != -1 and json_end > json_start:
                data = json.loads(text[json_start:json_end])
                actions = []
                for a in data.get("actions", []):
                    shape = None
                    if "shape" in a and a["shape"]:
                        s = a["shape"]
                        shape = Shape(
                            id="",
                            type=ShapeType(s.get("type", "circle")),
                            position=Position(**s.get("position", {"x": 400, "y": 300})),
                            name=s.get("name"),
                            color=Color(**s.get("color", {"r": 0, "g": 0, "b": 0})),
                            fill=s.get("fill", True),
                            width=s.get("width"),
                            height=s.get("height"),
                            radius=s.get("radius"),
                            text=s.get("text"),
                            zIndex=s.get("zIndex", 0),
                        )
                    action = DrawingAction(
                        action=a.get("action", "create"),
                        shape=shape,
                        shape_id=a.get("shape_id"),
                        target_name=a.get("target_name"),
                        position=Position(**a["position"]) if "position" in a else None,
                        properties=a.get("properties"),
                    )
                    actions.append(action)

                return AIResponse(
                    actions=actions,
                    explanation=data.get("explanation", ""),
                    scene_description=data.get("scene_description"),
                )
        except Exception as e:
            print(f"Parse error: {e}")

        return AIResponse(actions=[], explanation="无法解析指令")

    def _fallback_parse(self, command: str, scene_state: Dict) -> AIResponse:
        """Simple fallback parser when Claude API is unavailable"""
        actions = []
        explanation = ""
        cmd = command.lower()

        if "太阳" in cmd or "sun" in cmd:
            if "画" in cmd or "draw" in cmd or "创建" in cmd:
                actions.append(DrawingAction(
                    action="create",
                    shape=Shape(
                        id="", type=ShapeType.CIRCLE,
                        position=Position(x=600, y=150),
                        radius=60, name="太阳",
                        color=Color(r=255, g=200, b=0), fill=True, zIndex=1,
                    )
                ))
                explanation = "画了一个黄色太阳"
            elif "移" in cmd or "move" in cmd:
                shape = None
                for s in scene_state.get("shapes", []):
                    if "太阳" in (s.get("name") or ""):
                        shape = s
                        break
                if shape:
                    new_x = 200 if "左" in cmd else 600
                    new_y = 150
                    actions.append(DrawingAction(
                        action="move",
                        target_name=shape.get("name"),
                        position=Position(x=new_x, y=new_y),
                    ))
                    explanation = f"将太阳移到{'左边' if '左' in cmd else '右边'}"

        elif "房子" in cmd or "house" in cmd:
            actions.append(DrawingAction(
                action="create",
                shape=Shape(
                    id="", type=ShapeType.RECTANGLE,
                    position=Position(x=350, y=300),
                    width=200, height=150, name="房子",
                    color=Color(r=139, g=90, b=43), fill=True, zIndex=1,
                )
            ))
            actions.append(DrawingAction(
                action="create",
                shape=Shape(
                    id="", type=ShapeType.TRIANGLE,
                    position=Position(x=450, y=220),
                    width=240, height=100, name="屋顶",
                    color=Color(r=180, g=30, b=30), fill=True, zIndex=2,
                )
            ))
            explanation = "画了一栋房子"

        elif "树" in cmd or "tree" in cmd:
            actions.append(DrawingAction(
                action="create",
                shape=Shape(
                    id="", type=ShapeType.RECTANGLE,
                    position=Position(x=150, y=350),
                    width=30, height=80, name="树干",
                    color=Color(r=101, g=67, b=33), fill=True, zIndex=1,
                )
            ))
            actions.append(DrawingAction(
                action="create",
                shape=Shape(
                    id="", type=ShapeType.CIRCLE,
                    position=Position(x=165, y=300),
                    radius=50, name="树冠",
                    color=Color(r=34, g=139, b=34), fill=True, zIndex=2,
                )
            ))
            explanation = "画了一棵树"

        elif "清除" in cmd or "clear" in cmd or "清空" in cmd:
            actions.append(DrawingAction(action="clear"))
            explanation = "已清空画布"

        else:
            explanation = f"收到指令: {command}（需要 Claude API 进行更复杂的解析）"

        return AIResponse(actions=actions, explanation=explanation)

    def clear_history(self):
        self.conversation_history.clear()
