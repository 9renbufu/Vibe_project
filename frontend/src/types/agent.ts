/**
 * Agent 相关类型定义
 */

// Agent 执行步骤
export interface AgentStep {
  id: string;
  name: string;
  status: 'pending' | 'running' | 'completed' | 'error';
  startTime?: string;
  endTime?: string;
  output?: string;
  icon: string;
}

// 设计记忆
export interface DesignMemory {
  brand: string;
  targetUsers: string;
  style: string;
  colors: string[];
  keywords: string[];
  mood: string;
  industry: string;
}

// 设计方案
export interface DesignPlan {
  id: string;
  name: string;
  description: string;
  elements: string[];
  preview?: string;
  score?: number;
  selected?: boolean;
}

// 版本记录
export interface DesignVersion {
  id: string;
  version: string;
  timestamp: string;
  imageUrl: string;
  prompt: string;
  plan: string;
  changes: string[];
}

// AI 评估
export interface AIEvaluation {
  brandConsistency: number;
  creativity: number;
  commercialValue: number;
  aesthetics: number;
  overall: number;
  feedback: string;
}

// Agent 状态
export interface AgentState {
  currentTask: string;
  phase: string;
  steps: AgentStep[];
  memory: DesignMemory;
  plans: DesignPlan[];
  versions: DesignVersion[];
  evaluation: AIEvaluation | null;
  isThinking: boolean;
  currentStep: string;
}

// 用户偏好
export interface UserPreferences {
  favorite_style: string;
  favorite_styles: string[];
  favorite_colors: string[];
  industry: string;
  brand_name: string;
  target_audience: string;
  total_designs: number;
  average_score: number;
}

// 对话消息
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  type?: 'text' | 'image' | 'plan' | 'evaluation';
  metadata?: Record<string, any>;
}

// 思考日志
export interface ThinkingLog {
  agent: string;
  content: string;
  timestamp: string;
}

// WebSocket 消息
export interface WSMessage {
  type: string;
  data: any;
}
