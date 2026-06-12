/**
 * Conversation Panel - 对话面板
 */

import React, { useRef, useEffect, useState } from 'react';
import { useAgentStore } from '../../store/agentStore';

export const ConversationPanel: React.FC = () => {
  const {
    messages,
    isProcessing,
    connected,
  } = useAgentStore();

  const [inputText, setInputText] = useState('');
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [isSupported, setIsSupported] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const recognitionRef = useRef<any>(null);
  const isListeningRef = useRef(false);
  const handleSendRef = useRef<(text: string) => void>();

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // 同步 isListening 到 ref
  useEffect(() => {
    isListeningRef.current = isListening;
  }, [isListening]);

  // WebSocket 连接
  useEffect(() => {
    let ws: WebSocket | null = null;
    let reconnectTimeout: ReturnType<typeof setTimeout> | null = null;
    let isMounted = true;

    const connect = () => {
      if (!isMounted) return;

      // 使用相对路径，通过 Vite 代理连接后端
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/ws`;

      ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        if (isMounted) {
          useAgentStore.getState().setConnected(true);
        }
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          handleMessage(message);
        } catch (e) {
          console.error('Parse error:', e);
        }
      };

      ws.onclose = () => {
        if (isMounted) {
          useAgentStore.getState().setConnected(false);
          reconnectTimeout = setTimeout(connect, 3000);
        }
      };

      ws.onerror = (err) => {
        console.error('WebSocket error:', err);
      };

      wsRef.current = ws;
    };

    // 延迟连接，避免 StrictMode 双重挂载
    const connectTimeout: ReturnType<typeof setTimeout> = setTimeout(connect, 100);

    return () => {
      isMounted = false;
      clearTimeout(connectTimeout);
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
      if (ws) {
        ws.onclose = null; // 防止触发重连
        ws.close();
      }
    };
  }, []);

  // handleSend 函数
  const handleSend = (text: string) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
    if (!text.trim()) return;

    const store = useAgentStore.getState();

    store.addMessage({
      id: Date.now().toString(),
      role: 'user',
      content: text,
      timestamp: new Date().toISOString(),
      type: 'text',
    });

    store.setIsProcessing(true);
    store.setCurrentTask(text);

    wsRef.current.send(JSON.stringify({
      type: 'voice_input',
      data: { text },
    }));
  };

  // 保持 handleSend 引用
  useEffect(() => {
    handleSendRef.current = handleSend;
  });

  // 语音识别
  useEffect(() => {
    const SpeechRecognition =
      (window as any).SpeechRecognition ||
      (window as any).webkitSpeechRecognition;

    if (SpeechRecognition) {
      setIsSupported(true);
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = 'zh-CN';

      recognition.onresult = (event: any) => {
        let interim = '';
        let final = '';

        for (let i = event.resultIndex; i < event.results.length; i++) {
          if (event.results[i].isFinal) {
            final += event.results[i][0].transcript;
          } else {
            interim += event.results[i][0].transcript;
          }
        }

        setTranscript(interim || final);

        if (final) {
          handleSendRef.current?.(final);
          setTimeout(() => setTranscript(''), 1000);
        }
      };

      recognition.onerror = (event: any) => {
        // 忽略 no-speech 和 aborted 错误，这些是正常的
        if (event.error !== 'no-speech' && event.error !== 'aborted') {
          console.error('Speech recognition error:', event.error);
          setIsListening(false);
        }
      };

      recognition.onend = () => {
        // 如果还在监听状态，自动重启
        if (isListeningRef.current) {
          try {
            recognition.start();
          } catch (e) {
            // 忽略重启错误
          }
        }
      };

      recognitionRef.current = recognition;
    }

    return () => {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.abort();
        } catch (e) {}
      }
    };
  }, []);

  const handleMessage = (message: any) => {
    const store = useAgentStore.getState();

    switch (message.type) {
      case 'status':
        if (message.data.status === 'processing') {
          store.setIsProcessing(true);
          store.setIsThinking(true);
        } else if (message.data.status === 'generating') {
          store.setIsGenerating(true);
        }
        break;

      case 'thinking':
        // 思考过程更新
        store.setIsThinking(true);
        store.setCurrentStep(message.data.content || '');
        store.addThinkingLog({
          agent: message.data.agent,
          content: message.data.content,
          timestamp: new Date().toISOString(),
        });
        break;

      case 'stage_update':
        // 更新阶段
        const stage = message.data.stage;
        store.setPhase(stage);
        store.setIsThinking(true);
        // 更新步骤状态
        const stageStepMap: Record<string, string> = {
          'requirement': 'intent',
          'planning': 'plan',
          'prompt': 'prompt',
          'generating': 'generate',
          'evaluating': 'evaluate',
          'revising': 'prompt',
        };
        const stepId = stageStepMap[stage];
        if (stepId) {
          store.updateStep(stepId, { status: 'running' });
        }
        break;

      case 'agent_update':
        // Agent 执行结果更新
        const agentName = message.data.agent;
        const agentStepMap: Record<string, string> = {
          'RequirementAgent': 'intent',
          'PlanningAgent': 'plan',
          'PromptAgent': 'prompt',
          'GenerationAgent': 'generate',
          'CriticAgent': 'evaluate',
          'RevisionAgent': 'prompt',
        };
        const agentStepId = agentStepMap[agentName];
        if (agentStepId) {
          store.updateStep(agentStepId, {
            status: message.data.success ? 'completed' : 'error',
            output: message.data.message,
          });
        }
        // 更新评估结果（如果是CriticAgent）
        if (agentName === 'CriticAgent' && message.data.data?.evaluation) {
          const evalData = message.data.data.evaluation;
          store.setEvaluation({
            brandConsistency: evalData.brand_consistency || 0,
            creativity: evalData.creativity || 0,
            commercialValue: evalData.commercial_value || 0,
            aesthetics: evalData.visual_impact || evalData.aesthetics || 0,
            overall: evalData.overall || 0,
            feedback: evalData.feedback || '',
          });
        }
        // 更新设计方案（如果是PlanningAgent）
        if (agentName === 'PlanningAgent' && message.data.data?.plans) {
          message.data.data.plans.forEach((plan: any) => {
            store.addPlan({
              id: plan.id || Date.now().toString(),
              name: plan.name || 'Design Plan',
              description: plan.description || '',
              elements: plan.elements || [],
              score: plan.score,
              selected: plan.selected || false,
            });
          });
        }
        break;

      case 'agent_response':
        store.setIsProcessing(false);
        store.setIsThinking(false);
        store.setCurrentStep('');
        store.addMessage({
          id: Date.now().toString(),
          role: 'assistant',
          content: message.data.response || '',
          timestamp: new Date().toISOString(),
          type: 'text',
        });
        // 更新 phase
        if (message.data.stage) {
          store.setPhase(message.data.stage);
        }
        // 处理评估数据
        if (message.data.data?.evaluation) {
          const evalData = message.data.data.evaluation;
          store.setEvaluation({
            brandConsistency: evalData.brand_consistency || 0,
            creativity: evalData.creativity || 0,
            commercialValue: evalData.commercial_value || 0,
            aesthetics: evalData.visual_impact || evalData.aesthetics || 0,
            overall: evalData.overall || 0,
            feedback: evalData.feedback || '',
          });
        }
        // 处理用户偏好更新
        if (message.data.data?.preferences) {
          store.setPreferences(message.data.data.preferences);
        }
        // 处理优化建议
        if (message.data.data?.suggestions) {
          // 可以显示在UI中
        }
        // 重置步骤状态
        setTimeout(() => store.resetSteps(), 3000);
        break;

      case 'plans_result':
        // 接收设计方案
        const plans = message.data.plans || [];
        plans.forEach((plan: any) => {
          store.addPlan({
            id: plan.id || Date.now().toString(),
            name: plan.name || 'Design Plan',
            description: plan.description || '',
            elements: plan.elements || [],
            score: plan.score,
            selected: plan.selected || false,
          });
        });
        break;

      case 'evaluation_result':
        // 接收评估结果
        store.setEvaluation({
          brandConsistency: message.data.brand_consistency || 0,
          creativity: message.data.creativity || 0,
          commercialValue: message.data.commercial_value || 0,
          aesthetics: message.data.visual_impact || message.data.aesthetics || 0,
          overall: message.data.overall || 0,
          feedback: message.data.feedback || '',
        });
        break;

      case 'image_result':
        store.setIsGenerating(false);
        store.setIsThinking(false);
        // 确保图片有正确的 data URL 前缀
        const imageData = message.data.image;
        const imageUrl = imageData.startsWith('data:')
          ? imageData
          : `data:image/png;base64,${imageData}`;
        store.setGeneratedImage(imageUrl);
        store.setImagePrompt(message.data.prompt || '');
        // 添加版本记录
        store.addVersion({
          id: Date.now().toString(),
          version: `v${message.data.version || store.versions.length + 1}`,
          timestamp: new Date().toISOString(),
          imageUrl: imageUrl,
          prompt: message.data.prompt || '',
          plan: store.currentTask,
          changes: [],
        });
        break;

      case 'state_update':
        // 完整状态更新
        if (message.data.stage) {
          store.setPhase(message.data.stage);
        }
        break;

      case 'error':
        store.setIsProcessing(false);
        store.setIsThinking(false);
        store.setCurrentStep('');
        store.addMessage({
          id: Date.now().toString(),
          role: 'system',
          content: `Error: ${message.data.message}`,
          timestamp: new Date().toISOString(),
          type: 'text',
        });
        break;
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputText.trim()) {
      handleSend(inputText);
      setInputText('');
    }
  };

  const toggleListening = () => {
    if (!recognitionRef.current) return;

    if (isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    } else {
      try {
        recognitionRef.current.start();
        setIsListening(true);
      } catch (e) {
        console.error('Failed to start:', e);
      }
    }
  };

  const handleReset = () => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
    wsRef.current.send(JSON.stringify({ type: 'reset' }));
    useAgentStore.getState().reset();
  };

  return (
    <div style={styles.container}>
      {/* Header */}
      <div style={styles.header}>
        <div style={styles.headerLeft}>
          <span style={styles.logo}> </span>
          <span style={styles.title}>Voice Designer</span>
        </div>
        <div style={styles.headerRight}>
          <span style={{
            ...styles.statusDot,
            backgroundColor: connected ? '#10b981' : '#ef4444',
          }} />
          <button style={styles.resetBtn} onClick={handleReset}>
            Reset
          </button>
        </div>
      </div>

      {/* Messages */}
      <div style={styles.messages}>
        {messages.length === 0 && (
          <div style={styles.empty}>
            <div style={styles.emptyIcon}> </div>
            <h3 style={styles.emptyTitle}>Start Creating</h3>
            <p style={styles.emptyText}>
              Describe your design needs, I'll help you create
            </p>
            <div style={styles.suggestions}>
              {[
                'Design a tech startup logo',
                'Create a cyberpunk poster',
                'Design a cute milk tea shop IP',
              ].map((s, i) => (
                <button
                  key={i}
                  style={styles.suggestionBtn}
                  onClick={() => handleSend(s)}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <div
            key={msg.id}
            style={{
              ...styles.message,
              ...(msg.role === 'user' ? styles.userMessage : styles.assistantMessage),
            }}
          >
            <div style={styles.messageAvatar}>
              {msg.role === 'user' ? ' ' : ' '}
            </div>
            <div style={{
              ...styles.messageBubble,
              ...(msg.role === 'user' ? styles.userBubble : styles.assistantBubble),
            }}>
              {msg.content}
            </div>
          </div>
        ))}

        {isProcessing && (
          <div style={{ ...styles.message, ...styles.assistantMessage }}>
            <div style={styles.messageAvatar}> </div>
            <div style={{ ...styles.messageBubble, ...styles.assistantBubble }}>
              <div style={styles.thinking}>
                <span style={styles.thinkingDot}>●</span>
                <span style={styles.thinkingDot}>●</span>
                <span style={styles.thinkingDot}>●</span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div style={styles.inputArea}>
        {!isSupported && (
          <div style={styles.warning}>
            Browser does not support speech recognition, please use Chrome
          </div>
        )}
        {transcript && (
          <div style={styles.transcript}>{transcript}</div>
        )}
        <form style={styles.inputForm} onSubmit={handleSubmit}>
          <button
            type="button"
            onClick={toggleListening}
            disabled={!isSupported || isProcessing}
            style={{
              ...styles.micBtn,
              ...(isListening ? styles.micBtnActive : {}),
              ...((!isSupported || isProcessing) ? styles.micBtnDisabled : {}),
            }}
          >
            {isListening ? '⏹' : ' '}
          </button>
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="Describe your design..."
            style={styles.input}
            disabled={isProcessing}
          />
          <button
            type="submit"
            disabled={!inputText.trim() || isProcessing}
            style={{
              ...styles.sendBtn,
              ...((!inputText.trim() || isProcessing) ? styles.sendBtnDisabled : {}),
            }}
          >
            ➤
          </button>
        </form>
      </div>
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    height: '100%',
    backgroundColor: '#ffffff',
    borderRight: '1px solid #e5e7eb',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '12px 16px',
    borderBottom: '1px solid #e5e7eb',
    backgroundColor: '#fafafa',
  },
  headerLeft: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  logo: {
    fontSize: '20px',
  },
  title: {
    fontSize: '14px',
    fontWeight: '600',
    color: '#111827',
  },
  headerRight: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  statusDot: {
    width: '8px',
    height: '8px',
    borderRadius: '50%',
  },
  resetBtn: {
    padding: '4px 8px',
    fontSize: '11px',
    border: '1px solid #d1d5db',
    borderRadius: '4px',
    backgroundColor: '#fff',
    cursor: 'pointer',
    color: '#6b7280',
  },
  messages: {
    flex: 1,
    overflowY: 'auto',
    padding: '16px',
  },
  empty: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    height: '100%',
    padding: '20px',
  },
  emptyIcon: {
    fontSize: '48px',
    marginBottom: '16px',
  },
  emptyTitle: {
    margin: '0 0 8px 0',
    fontSize: '18px',
    fontWeight: '600',
    color: '#111827',
  },
  emptyText: {
    margin: '0 0 20px 0',
    fontSize: '13px',
    color: '#6b7280',
    textAlign: 'center',
  },
  suggestions: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
    width: '100%',
  },
  suggestionBtn: {
    padding: '10px 14px',
    fontSize: '12px',
    border: '1px solid #e5e7eb',
    borderRadius: '8px',
    backgroundColor: '#f9fafb',
    cursor: 'pointer',
    textAlign: 'left',
    color: '#374151',
    transition: 'all 0.2s',
  },
  message: {
    display: 'flex',
    gap: '8px',
    marginBottom: '12px',
  },
  userMessage: {
    flexDirection: 'row-reverse',
  },
  assistantMessage: {
    flexDirection: 'row',
  },
  messageAvatar: {
    width: '28px',
    height: '28px',
    borderRadius: '50%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '14px',
    flexShrink: 0,
  },
  messageBubble: {
    maxWidth: '80%',
    padding: '10px 14px',
    borderRadius: '12px',
    fontSize: '13px',
    lineHeight: '1.5',
  },
  userBubble: {
    backgroundColor: '#6366f1',
    color: '#ffffff',
    borderBottomRightRadius: '4px',
  },
  assistantBubble: {
    backgroundColor: '#f3f4f6',
    color: '#111827',
    borderBottomLeftRadius: '4px',
  },
  thinking: {
    display: 'flex',
    gap: '4px',
  },
  thinkingDot: {
    animation: 'pulse 1.4s infinite',
    fontSize: '10px',
    color: '#9ca3af',
  },
  inputArea: {
    padding: '12px 16px',
    borderTop: '1px solid #e5e7eb',
    backgroundColor: '#fafafa',
  },
  transcript: {
    padding: '8px 12px',
    marginBottom: '8px',
    backgroundColor: '#fef3c7',
    borderRadius: '6px',
    fontSize: '12px',
    color: '#92400e',
  },
  inputForm: {
    display: 'flex',
    gap: '8px',
  },
  warning: {
    padding: '8px 12px',
    marginBottom: '8px',
    backgroundColor: '#fef3c7',
    borderRadius: '6px',
    fontSize: '11px',
    color: '#92400e',
    textAlign: 'center',
  },
  micBtn: {
    width: '40px',
    height: '40px',
    border: '1px solid #d1d5db',
    borderRadius: '8px',
    backgroundColor: '#fff',
    cursor: 'pointer',
    fontSize: '16px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  micBtnActive: {
    backgroundColor: '#fef2f2',
    borderColor: '#ef4444',
  },
  micBtnDisabled: {
    backgroundColor: '#f3f4f6',
    cursor: 'not-allowed',
    opacity: 0.5,
  },
  input: {
    flex: 1,
    padding: '10px 14px',
    fontSize: '13px',
    border: '1px solid #d1d5db',
    borderRadius: '8px',
    outline: 'none',
    backgroundColor: '#fff',
  },
  sendBtn: {
    width: '40px',
    height: '40px',
    border: 'none',
    borderRadius: '8px',
    backgroundColor: '#6366f1',
    color: '#fff',
    cursor: 'pointer',
    fontSize: '16px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  sendBtnDisabled: {
    backgroundColor: '#d1d5db',
    cursor: 'not-allowed',
  },
};
