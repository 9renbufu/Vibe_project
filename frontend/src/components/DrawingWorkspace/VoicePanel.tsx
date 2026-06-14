/**
 * 语音绘图面板 - 左侧面板
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useDrawingStore } from '../../store/drawingStore';

const VoicePanel: React.FC = () => {
  const [inputText, setInputText] = useState('');
  const [isError, setIsError] = useState(false);
  const {
    isListening, transcript, connected, isProcessing,
    commandHistory, lastCommand,
    setIsListening, setTranscript, setConnected, setIsProcessing,
    setLastCommand, addCommandRecord, applyInstructions, reset,
    setPreferences, setDrawingHistory,
  } = useDrawingStore();

  const recognitionRef = useRef<any>(null);
  const isListeningRef = useRef(false);
  const wsRef = useRef<WebSocket | null>(null);

  // WebSocket 连接
  useEffect(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const socket = new WebSocket(`${protocol}//${host}/ws/draw`);

    socket.onopen = () => {
      setConnected(true);
      wsRef.current = socket;
    };

    socket.onmessage = (event) => {
      const message = JSON.parse(event.data);
      switch (message.type) {
        case 'drawing_update':
          setIsProcessing(false);
          // 只在有新指令时更新画布（空指令表示识别失败，保留原画布）
          if (message.data.instructions && message.data.instructions.length > 0) {
            applyInstructions(message.data.instructions, message.data.state);
            setIsError(false);
          } else if (message.data.error) {
            setIsError(true);
          }
          setLastCommand(message.data.response || '');
          // 记录所有指令（包括失败的）
          if (message.data.parsed) {
            addCommandRecord({
              text: message.data.parsed.raw || message.data.parsed.text || '',
              type: message.data.parsed.type || '',
              confidence: message.data.parsed.confidence || 0,
              timestamp: new Date().toISOString(),
            });
          }
          // 更新偏好和历史
          if (message.data.preferences) {
            setPreferences(message.data.preferences);
          }
          if (message.data.drawing_history) {
            setDrawingHistory(message.data.drawing_history);
          }
          break;
        case 'canvas_state':
          applyInstructions([], message.data);
          break;
        case 'error':
          setIsProcessing(false);
          setLastCommand(`错误: ${message.data.message}`);
          break;
      }
    };

    socket.onclose = () => {
      setConnected(false);
      wsRef.current = null;
      setTimeout(() => {
        // 自动重连
      }, 3000);
    };

    return () => {
      socket.close();
    };
  }, []);

  // 发送指令
  const sendCommand = useCallback((text: string) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
    if (!text.trim()) return;

    setIsProcessing(true);
    wsRef.current.send(JSON.stringify({
      type: 'voice_input',
      data: { text: text.trim() },
    }));
  }, [setIsProcessing]);

  // 语音识别
  useEffect(() => {
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) return;

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
        sendCommand(final);
        setTimeout(() => setTranscript(''), 1000);
      }
    };

    recognition.onerror = (event: any) => {
      if (event.error !== 'no-speech' && event.error !== 'aborted') {
        console.error('Speech error:', event.error);
        setIsListening(false);
      }
    };

    recognition.onend = () => {
      if (isListeningRef.current) {
        try { recognition.start(); } catch (e) {}
      }
    };

    recognitionRef.current = recognition;
  }, [sendCommand]);

  const toggleListening = () => {
    if (!recognitionRef.current) return;
    if (isListening) {
      isListeningRef.current = false;
      recognitionRef.current.stop();
      setIsListening(false);
    } else {
      isListeningRef.current = true;
      recognitionRef.current.start();
      setIsListening(true);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputText.trim()) {
      sendCommand(inputText);
      setInputText('');
    }
  };

  const handleReset = () => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'reset' }));
      reset();
    }
  };

  const quickCommands = [
    { label: '  流场', cmd: '画一幅流场艺术' },
    { label: '  分形树', cmd: '画一棵分形树' },
    { label: '  曼陀罗', cmd: '画一个曼陀罗' },
    { label: '  日落', cmd: '画一幅日落风景' },
    { label: '  星空', cmd: '画一幅星空' },
    { label: '  水彩', cmd: '画一幅水彩' },
    { label: '  螺线', cmd: '画一个螺线' },
    { label: '  沃罗诺伊', cmd: '画一个沃罗诺伊' },
  ];

  const isSupported = typeof window !== 'undefined' &&
    ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window);

  return (
    <div style={styles.container}>
      {/* Header */}
      <div style={styles.header}>
        <div style={styles.headerLeft}>
          <span style={styles.logo}> </span>
          <span style={styles.title}>Voice Drawing</span>
        </div>
        <div style={styles.headerRight}>
          <div style={{ ...styles.statusDot, backgroundColor: connected ? '#22c55e' : '#ef4444' }} />
          <button style={styles.resetBtn} onClick={handleReset}>重置</button>
        </div>
      </div>

      {/* Voice Control */}
      <div style={styles.voiceSection}>
        <button
          onClick={toggleListening}
          disabled={!isSupported}
          style={{
            ...styles.micBtn,
            ...(isListening ? styles.micBtnActive : {}),
            ...(!isSupported ? styles.micBtnDisabled : {}),
          }}
        >
          {isListening ? '⏹' : ' '}
        </button>
        {!isSupported && (
          <div style={styles.warning}>浏览器不支持语音识别，请使用 Chrome</div>
        )}
        {transcript && (
          <div style={styles.transcript}>{transcript}</div>
        )}
        {isProcessing && (
          <div style={styles.processing}>⏳ 处理中...</div>
        )}
        {lastCommand && !isProcessing && (
          <div style={isError ? styles.errorMessage : styles.lastCommand}>{lastCommand}</div>
        )}
      </div>

      {/* Quick Commands */}
      <div style={styles.section}>
        <div style={styles.sectionTitle}>快捷指令</div>
        <div style={styles.quickGrid}>
          {quickCommands.map((qc) => (
            <button
              key={qc.label}
              style={styles.quickBtn}
              onClick={() => sendCommand(qc.cmd)}
              onMouseEnter={(e) => {
                (e.currentTarget as HTMLButtonElement).style.borderColor = '#6366f1';
                (e.currentTarget as HTMLButtonElement).style.backgroundColor = '#eef2ff';
              }}
              onMouseLeave={(e) => {
                (e.currentTarget as HTMLButtonElement).style.borderColor = '#e5e7eb';
                (e.currentTarget as HTMLButtonElement).style.backgroundColor = '#f9fafb';
              }}
            >
              {qc.label}
            </button>
          ))}
        </div>
      </div>

      {/* Command History */}
      <div style={{ ...styles.section, flex: 1, overflow: 'hidden' }}>
        <div style={styles.sectionTitle}>指令历史</div>
        <div style={styles.historyList}>
          {commandHistory.length === 0 && (
            <div style={styles.emptyHint}>使用语音或点击快捷指令开始绘图</div>
          )}
          {commandHistory.slice().reverse().map((cmd, i) => (
            <div key={i} style={styles.historyItem}>
              <div style={styles.historyText}>{cmd.text}</div>
              <div style={styles.historyMeta}>
                <span style={styles.historyType}>{cmd.type}</span>
                <span style={styles.historyTime}>
                  {new Date(cmd.timestamp).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Input */}
      <div style={styles.inputArea}>
        <form style={styles.inputForm} onSubmit={handleSubmit}>
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="输入绘图指令..."
            style={styles.input}
          />
          <button
            type="submit"
            disabled={!inputText.trim()}
            style={{
              ...styles.sendBtn,
              ...(!inputText.trim() ? styles.sendBtnDisabled : {}),
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
    display: 'flex', flexDirection: 'column', height: '100%',
    backgroundColor: '#ffffff', borderRight: '1px solid #e5e7eb',
  },
  header: {
    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
    padding: '12px 16px', borderBottom: '1px solid #e5e7eb', backgroundColor: '#fafafa',
  },
  headerLeft: { display: 'flex', alignItems: 'center', gap: '8px' },
  logo: { fontSize: '20px' },
  title: { fontSize: '14px', fontWeight: '600', color: '#111827' },
  headerRight: { display: 'flex', alignItems: 'center', gap: '8px' },
  statusDot: { width: '8px', height: '8px', borderRadius: '50%' },
  resetBtn: {
    padding: '4px 8px', fontSize: '11px', border: '1px solid #d1d5db',
    borderRadius: '4px', backgroundColor: '#fff', cursor: 'pointer', color: '#6b7280',
  },
  voiceSection: {
    display: 'flex', flexDirection: 'column', alignItems: 'center',
    padding: '16px', borderBottom: '1px solid #e5e7eb', gap: '8px',
  },
  micBtn: {
    width: '56px', height: '56px', border: '2px solid #d1d5db', borderRadius: '50%',
    backgroundColor: '#fff', cursor: 'pointer', fontSize: '24px',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    transition: 'all 0.2s',
  },
  micBtnActive: { backgroundColor: '#fef2f2', borderColor: '#ef4444', boxShadow: '0 0 12px rgba(239,68,68,0.3)' },
  micBtnDisabled: { backgroundColor: '#f3f4f6', cursor: 'not-allowed', opacity: 0.5 },
  warning: { padding: '6px 12px', fontSize: '11px', color: '#92400e', backgroundColor: '#fef3c7', borderRadius: '6px' },
  transcript: { padding: '6px 12px', fontSize: '13px', color: '#4b5563', backgroundColor: '#f3f4f6', borderRadius: '6px', width: '100%', textAlign: 'center' },
  processing: { fontSize: '12px', color: '#6366f1', fontWeight: '500' },
  lastCommand: { fontSize: '12px', color: '#22c55e', fontWeight: '500' },
  errorMessage: { fontSize: '12px', color: '#ef4444', fontWeight: '500', backgroundColor: '#fef2f2', padding: '4px 8px', borderRadius: '4px' },
  section: { padding: '12px 16px', borderBottom: '1px solid #e5e7eb' },
  sectionTitle: { fontSize: '12px', fontWeight: '600', color: '#6b7280', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.5px' },
  quickGrid: { display: 'flex', flexWrap: 'wrap', gap: '6px' },
  quickBtn: {
    padding: '6px 12px', fontSize: '12px', border: '1px solid #e5e7eb',
    borderRadius: '16px', backgroundColor: '#f9fafb', cursor: 'pointer',
    color: '#374151', transition: 'all 0.15s', whiteSpace: 'nowrap',
  },
  historyList: { overflowY: 'auto', maxHeight: '100%' },
  emptyHint: { fontSize: '12px', color: '#9ca3af', textAlign: 'center', padding: '20px 0' },
  historyItem: {
    padding: '8px 0', borderBottom: '1px solid #f3f4f6',
  },
  historyText: { fontSize: '13px', color: '#111827', marginBottom: '2px' },
  historyMeta: { display: 'flex', justifyContent: 'space-between', alignItems: 'center' },
  historyType: { fontSize: '10px', color: '#6366f1', backgroundColor: '#eef2ff', padding: '1px 6px', borderRadius: '8px' },
  historyTime: { fontSize: '10px', color: '#9ca3af' },
  inputArea: { padding: '12px 16px', borderTop: '1px solid #e5e7eb', backgroundColor: '#fafafa' },
  inputForm: { display: 'flex', gap: '8px' },
  input: {
    flex: 1, padding: '10px 14px', fontSize: '13px', border: '1px solid #d1d5db',
    borderRadius: '8px', outline: 'none', backgroundColor: '#fff',
  },
  sendBtn: {
    width: '40px', height: '40px', border: 'none', borderRadius: '8px',
    backgroundColor: '#6366f1', color: '#fff', cursor: 'pointer', fontSize: '16px',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
  },
  sendBtnDisabled: { backgroundColor: '#d1d5db', cursor: 'not-allowed' },
};

export default VoicePanel;
