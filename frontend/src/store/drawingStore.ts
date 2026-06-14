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
  reset: () =>
    set({
      background: 'rgb(255,255,255)',
      shapeCount: 0,
      instructions: [],
      commandHistory: [],
      lastCommand: '',
      transcript: '',
    }),
}));
