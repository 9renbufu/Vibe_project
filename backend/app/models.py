from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from enum import Enum


class ShapeType(str, Enum):
    CIRCLE = "circle"
    RECTANGLE = "rectangle"
    LINE = "line"
    TRIANGLE = "triangle"
    POLYGON = "polygon"
    TEXT = "text"
    PATH = "path"


class Color(BaseModel):
    r: int = 0
    g: int = 0
    b: int = 0
    a: float = 1.0


class Position(BaseModel):
    x: float
    y: float


class Shape(BaseModel):
    id: str
    type: ShapeType
    position: Position
    width: Optional[float] = None
    height: Optional[float] = None
    radius: Optional[float] = None
    color: Color = Color(r=0, g=0, b=0)
    fill: bool = True
    text: Optional[str] = None
    points: Optional[List[Position]] = None
    rotation: float = 0
    scale: float = 1.0
    zIndex: int = 0
    name: Optional[str] = None


class SceneState(BaseModel):
    shapes: List[Shape] = []
    background: Color = Color(r=255, g=255, b=255)
    width: int = 800
    height: int = 600


class VoiceCommand(BaseModel):
    text: str
    timestamp: float


class DrawingAction(BaseModel):
    action: str  # "create", "move", "delete", "modify", "clear"
    shape: Optional[Shape] = None
    shape_id: Optional[str] = None
    target_name: Optional[str] = None
    position: Optional[Position] = None
    properties: Optional[Dict[str, Any]] = None


class AIResponse(BaseModel):
    actions: List[DrawingAction]
    explanation: str
    scene_description: Optional[str] = None


class WebSocketMessage(BaseModel):
    type: str  # "voice", "action", "state", "error"
    data: Any
