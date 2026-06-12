export interface Position {
  x: number;
  y: number;
}

export interface Color {
  r: number;
  g: number;
  b: number;
  a?: number;
}

export type ShapeType = 'circle' | 'rectangle' | 'line' | 'triangle' | 'polygon' | 'text' | 'path';

export interface Shape {
  id: string;
  type: ShapeType;
  position: Position;
  width?: number;
  height?: number;
  radius?: number;
  color: Color;
  fill: boolean;
  text?: string;
  points?: Position[];
  rotation: number;
  scale: number;
  zIndex: number;
  name?: string;
}

export interface SceneState {
  shapes: Shape[];
  background: Color;
  width: number;
  height: number;
}

export interface DrawingAction {
  action: 'create' | 'move' | 'delete' | 'modify' | 'clear';
  shape?: Shape;
  shape_id?: string;
  target_name?: string;
  position?: Position;
  properties?: Record<string, unknown>;
}

export interface AIResponse {
  actions: DrawingAction[];
  explanation: string;
  scene_description?: string;
}

export interface WebSocketMessage {
  type: 'voice' | 'action' | 'state' | 'error';
  data: unknown;
}
