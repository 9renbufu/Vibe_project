/**
 * Agent 状态管理
 */

import { create } from 'zustand';
import {
  AgentState,
  AgentStep,
  DesignMemory,
  DesignPlan,
  DesignVersion,
  AIEvaluation,
  ChatMessage,
  ThinkingLog,
  UserPreferences,
} from '../types/agent';

interface AgentStore extends AgentState {
  // 对话
  messages: ChatMessage[];
  isProcessing: boolean;
  isGenerating: boolean;
  generatedImage: string | null;
  imagePrompt: string;
  connected: boolean;
  thinkingLogs: ThinkingLog[];
  preferences: UserPreferences | null;
  pendingInputs: string[];

  // Actions
  addMessage: (message: ChatMessage) => void;
  clearMessages: () => void;
  setCurrentTask: (task: string) => void;
  setPhase: (phase: string) => void;
  updateStep: (stepId: string, updates: Partial<AgentStep>) => void;
  addStep: (step: AgentStep) => void;
  resetSteps: () => void;
  updateMemory: (updates: Partial<DesignMemory>) => void;
  addPlan: (plan: DesignPlan) => void;
  selectPlan: (planId: string) => void;
  addVersion: (version: DesignVersion) => void;
  rollbackVersion: (versionId: string) => void;
  setEvaluation: (evaluation: AIEvaluation) => void;
  setIsThinking: (thinking: boolean) => void;
  setCurrentStep: (step: string) => void;
  setIsProcessing: (processing: boolean) => void;
  setIsGenerating: (generating: boolean) => void;
  setGeneratedImage: (image: string | null) => void;
  setImagePrompt: (prompt: string) => void;
  setConnected: (connected: boolean) => void;
  addThinkingLog: (log: ThinkingLog) => void;
  clearThinkingLogs: () => void;
  setPreferences: (preferences: UserPreferences) => void;
  addPendingInput: (text: string) => void;
  shiftPendingInput: () => string | undefined;
  clearPendingInputs: () => void;
  reset: () => void;
}

// 默认设计记忆
const defaultMemory: DesignMemory = {
  brand: '',
  targetUsers: '',
  style: 'modern',
  colors: [],
  keywords: [],
  mood: '',
  industry: '',
};

// 默认 Agent 步骤
const defaultSteps: AgentStep[] = [
  { id: 'intent', name: 'Requirement Analysis', status: 'pending', icon: ' ' },
  { id: 'user', name: 'User Profiling', status: 'pending', icon: ' ' },
  { id: 'plan', name: 'Design Planning', status: 'pending', icon: ' ' },
  { id: 'prompt', name: 'Prompt Generation', status: 'pending', icon: '✍️' },
  { id: 'generate', name: 'Image Generation', status: 'pending', icon: ' ' },
  { id: 'evaluate', name: 'Design Evaluation', status: 'pending', icon: ' ' },
  { id: 'revision', name: 'Auto Optimization', status: 'pending', icon: ' ' },
];

export const useAgentStore = create<AgentStore>((set, get) => ({
  // 初始状态
  currentTask: '',
  phase: 'idle',
  steps: [...defaultSteps],
  memory: { ...defaultMemory },
  plans: [],
  versions: [],
  evaluation: null,
  isThinking: false,
  currentStep: '',
  messages: [],
  isProcessing: false,
  isGenerating: false,
  generatedImage: null,
  imagePrompt: '',
  connected: false,
  thinkingLogs: [],
  preferences: null,
  pendingInputs: [],

  // Actions
  addMessage: (message) =>
    set((state) => ({ messages: [...state.messages, message] })),

  clearMessages: () => set({ messages: [] }),

  setCurrentTask: (task) => set({ currentTask: task }),

  setPhase: (phase) => set({ phase }),

  updateStep: (stepId, updates) =>
    set((state) => ({
      steps: state.steps.map((step) =>
        step.id === stepId ? { ...step, ...updates } : step
      ),
    })),

  addStep: (step) =>
    set((state) => ({ steps: [...state.steps, step] })),

  resetSteps: () =>
    set({ steps: [...defaultSteps] }),

  updateMemory: (updates) =>
    set((state) => ({
      memory: { ...state.memory, ...updates },
    })),

  addPlan: (plan) =>
    set((state) => ({ plans: [...state.plans, plan] })),

  selectPlan: (planId) =>
    set((state) => ({
      plans: state.plans.map((p) => ({
        ...p,
        selected: p.id === planId,
      })),
    })),

  addVersion: (version) =>
    set((state) => ({ versions: [...state.versions, version] })),

  rollbackVersion: (versionId) => {
    const state = get();
    const version = state.versions.find((v) => v.id === versionId);
    if (version) {
      set({
        generatedImage: version.imageUrl,
        imagePrompt: version.prompt,
      });
    }
  },

  setEvaluation: (evaluation) => set({ evaluation }),

  setIsThinking: (thinking) => set({ isThinking: thinking }),

  setCurrentStep: (step) => set({ currentStep: step }),

  setIsProcessing: (processing) => set({ isProcessing: processing }),

  setIsGenerating: (generating) => set({ isGenerating: generating }),

  setGeneratedImage: (image) => set({ generatedImage: image }),

  setImagePrompt: (prompt) => set({ imagePrompt: prompt }),

  setConnected: (connected) => set({ connected }),

  addThinkingLog: (log) =>
    set((state) => ({
      thinkingLogs: [...state.thinkingLogs, log].slice(-50), // 保留最近50条
    })),

  clearThinkingLogs: () => set({ thinkingLogs: [] }),

  setPreferences: (preferences) => set({ preferences }),

  addPendingInput: (text) =>
    set((state) => ({ pendingInputs: [...state.pendingInputs, text] })),

  shiftPendingInput: () => {
    const state = get();
    const first = state.pendingInputs[0];
    set({ pendingInputs: state.pendingInputs.slice(1) });
    return first;
  },

  clearPendingInputs: () => set({ pendingInputs: [] }),

  reset: () =>
    set({
      currentTask: '',
      phase: 'idle',
      steps: [...defaultSteps],
      memory: { ...defaultMemory },
      plans: [],
      versions: [],
      evaluation: null,
      isThinking: false,
      currentStep: '',
      messages: [],
      isProcessing: false,
      isGenerating: false,
      generatedImage: null,
      imagePrompt: '',
      thinkingLogs: [],
      preferences: null,
      pendingInputs: [],
    }),
}));
