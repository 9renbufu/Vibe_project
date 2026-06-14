/**
 * 绘图工具状态管理
 */

import { create } from 'zustand';

export interface DrawingInstruction {
  action: string;
  shape_type?: string;
  params: Record<string, any>;
  layer?: number;
}

interface CommandRecord {
  text: string;
  type: string;
  confidence: number;
  timestamp: string;
}

interface UserPreferences {
  favorite_colors: string[];
  favorite_styles: string[];
  favorite_shapes: string[];
  total_commands: number;
}

interface DrawingHistoryRecord {
  command: string;
  response: string;
  shape_count: number;
  background: string;
  timestamp: string;
}

export interface CanvasRecord {
  id: string;
  title: string;
  created_at: string;
  command_count: number;
  shape_count: number;
}

interface DrawingState {
  // 画布状态
  canvasWidth: number;
  canvasHeight: number;
  background: string;
  shapeCount: number;

  // 当前工具
  currentColor: string;
  currentSize: number;

  // 语音状态
  isListening: boolean;
  transcript: string;
  lastCommand: string;
  commandHistory: CommandRecord[];

  // 连接
  connected: boolean;
  isProcessing: boolean;

  // 绘图指令（最新一批）
  instructions: DrawingInstruction[];

  // 用户偏好
  preferences: UserPreferences | null;

  // 绘图历史
  drawingHistory: DrawingHistoryRecord[];

  // 画布记录
  records: CanvasRecord[];
  activeRecordId: string | null;

  // Actions
  setBackground: (color: string) => void;
  setShapeCount: (count: number) => void;
  setCurrentColor: (color: string) => void;
  setCurrentSize: (size: number) => void;
  setIsListening: (listening: boolean) => void;
  setTranscript: (transcript: string) => void;
  setLastCommand: (command: string) => void;
  addCommandRecord: (record: CommandRecord) => void;
  setConnected: (connected: boolean) => void;
  setIsProcessing: (processing: boolean) => void;
  applyInstructions: (instructions: DrawingInstruction[], state?: any) => void;
  appendInstructions: (instructions: DrawingInstruction[]) => void;
  setPreferences: (prefs: UserPreferences) => void;
  setDrawingHistory: (history: DrawingHistoryRecord[]) => void;
  setRecords: (records: CanvasRecord[]) => void;
  setActiveRecordId: (id: string | null) => void;
  reset: () => void;
}

export const useDrawingStore = create<DrawingState>((set) => ({
  canvasWidth: 1200,
  canvasHeight: 800,
  background: 'rgb(255,255,255)',
  shapeCount: 0,
  currentColor: '#323232',
  currentSize: 80,
  isListening: false,
  transcript: '',
  lastCommand: '',
  commandHistory: [],
  connected: false,
  isProcessing: false,
  instructions: [],
  preferences: null,
  drawingHistory: [],
  records: [],
  activeRecordId: null,

  setBackground: (color) => set({ background: color }),
  setShapeCount: (count) => set({ shapeCount: count }),
  setCurrentColor: (color) => set({ currentColor: color }),
  setCurrentSize: (size) => set({ currentSize: size }),
  setIsListening: (listening) => set({ isListening: listening }),
  setTranscript: (transcript) => set({ transcript }),
  setLastCommand: (command) => set({ lastCommand: command }),
  addCommandRecord: (record) =>
    set((s) => ({ commandHistory: [...s.commandHistory, record].slice(-30) })),
  setConnected: (connected) => set({ connected }),
  setIsProcessing: (processing) => set({ isProcessing: processing }),
  applyInstructions: (instructions, state) =>
    set({
      instructions,
      background: state?.background || 'rgb(255,255,255)',
      shapeCount: state?.shape_count || 0,
    }),
  appendInstructions: (newInstructions) =>
    set((s) => ({ instructions: [...s.instructions, ...newInstructions] })),
  setPreferences: (prefs) => set({ preferences: prefs }),
  setDrawingHistory: (history) => set({ drawingHistory: history }),
  setRecords: (records) => set({ records }),
  setActiveRecordId: (id) => set({ activeRecordId: id }),
  reset: () =>
    set({
      background: 'rgb(255,255,255)',
      shapeCount: 0,
      instructions: [],
      commandHistory: [],
      lastCommand: '',
      transcript: '',
      preferences: null,
      drawingHistory: [],
      records: [],
      activeRecordId: null,
    }),
}));
