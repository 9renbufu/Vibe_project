import uuid
from typing import List, Optional, Dict
from .models import Shape, SceneState, Position, Color, ShapeType, DrawingAction


class SceneManager:
    def __init__(self):
        self.scene = SceneState()
        self.shape_name_map: Dict[str, str] = {}  # name -> id

    def get_state(self) -> SceneState:
        return self.scene

    def add_shape(self, shape: Shape) -> Shape:
        if not shape.id:
            shape.id = str(uuid.uuid4())[:8]
        self.scene.shapes.append(shape)
        if shape.name:
            self.shape_name_map[shape.name.lower()] = shape.id
        return shape

    def find_shape_by_name(self, name: str) -> Optional[Shape]:
        shape_id = self.shape_name_map.get(name.lower())
        if shape_id:
            return self.find_shape_by_id(shape_id)
        return None

    def find_shape_by_id(self, shape_id: str) -> Optional[Shape]:
        for shape in self.scene.shapes:
            if shape.id == shape_id:
                return shape
        return None

    def move_shape(self, shape_id: str, position: Position) -> Optional[Shape]:
        shape = self.find_shape_by_id(shape_id)
        if shape:
            shape.position = position
        return shape

    def delete_shape(self, shape_id: str) -> bool:
        shape = self.find_shape_by_id(shape_id)
        if shape:
            self.scene.shapes.remove(shape)
            if shape.name and shape.name.lower() in self.shape_name_map:
                del self.shape_name_map[shape.name.lower()]
            return True
        return False

    def clear_scene(self):
        self.scene.shapes.clear()
        self.shape_name_map.clear()

    def execute_action(self, action: DrawingAction) -> Optional[Shape]:
        if action.action == "create" and action.shape:
            return self.add_shape(action.shape)
        elif action.action == "move":
            target_id = action.shape_id
            if action.target_name and not target_id:
                target_id = self.shape_name_map.get(action.target_name.lower())
            if target_id and action.position:
                return self.move_shape(target_id, action.position)
        elif action.action == "delete":
            target_id = action.shape_id
            if action.target_name and not target_id:
                target_id = self.shape_name_map.get(action.target_name.lower())
            if target_id:
                self.delete_shape(target_id)
        elif action.action == "clear":
            self.clear_scene()
        elif action.action == "modify":
            target_id = action.shape_id
            if action.target_name and not target_id:
                target_id = self.shape_name_map.get(action.target_name.lower())
            if target_id and action.properties:
                shape = self.find_shape_by_id(target_id)
                if shape:
                    for key, value in action.properties.items():
                        if hasattr(shape, key):
                            setattr(shape, key, value)
                    return shape
        return None
