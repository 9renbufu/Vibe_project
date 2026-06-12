import React, { useState, useCallback, useEffect, useRef } from 'react';
import { ChatPanel } from './components/ChatPanel';
import { DesignCanvas } from './components/DesignCanvas';
import { DesignInfo } from './components/DesignInfo';
import { VoiceInput } from './components/VoiceInput';

interface DesignElement {
  name: string;
  description: string;
  position: string;
  size: string;
}

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
}

const AppV2: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedImage, setGeneratedImage] = useState<string | null>(null);
  const [imagePrompt, setImagePrompt] = useState('');
  const [connected, setConnected] = useState(false);

  // 设计状态
  const [phase, setPhase] = useState('idle');
  const [style, setStyle] = useState('flat');
  const [elements, setElements] = useState<DesignElement[]>([]);
  const [colorPalette, setColorPalette] = useState<string[]>([]);
  const [imageCount, setImageCount] = useState(0);

  const wsRef = useRef<WebSocket | null>(null);

  // WebSocket 连接
  useEffect(() => {
    const connect = () => {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/ws`;

      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        setConnected(true);
        console.log('WebSocket connected');
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          handleMessage(message);
        } catch (e) {
          console.error('Failed to parse message:', e);
        }
      };

      ws.onclose = () => {
        setConnected(false);
        setTimeout(connect, 3000);
      };

      ws.onerror = () => {
        setConnected(false);
      };

      wsRef.current = ws;
    };

    connect();

    return () => {
      wsRef.current?.close();
    };
  }, []);

  const handleMessage = useCallback((message: any) => {
    console.log('Received message:', message);
    const { type, data } = message;

    switch (type) {
      case 'agent_response':
        console.log('Agent response:', data);
        setIsProcessing(false);
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: data.response || '',
          timestamp: new Date().toISOString(),
        }]);

        // 更新设计状态
        if (data.phase) setPhase(data.phase);
        if (data.style) setStyle(data.style);
        if (data.elements) setElements(data.elements);
        if (data.color_palette) setColorPalette(data.color_palette);
        break;

      case 'image_result':
        setIsGenerating(false);
        setGeneratedImage(data.image);
        setImagePrompt(data.prompt || '');
        setImageCount(prev => prev + 1);
        break;

      case 'state_update':
        // 更新完整状态
        if (data.phase) setPhase(data.phase);
        if (data.style) setStyle(data.style);
        if (data.elements) setElements(data.elements);
        break;

      case 'status':
        if (data.status === 'processing') {
          setIsProcessing(true);
        } else if (data.status === 'generating') {
          setIsGenerating(true);
        }
        break;

      case 'error':
        setIsProcessing(false);
        setIsGenerating(false);
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: `错误: ${data.message}`,
          timestamp: new Date().toISOString(),
        }]);
        break;
    }
  }, []);

  const sendText = useCallback((text: string) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;

    setMessages(prev => [...prev, {
      role: 'user',
      content: text,
      timestamp: new Date().toISOString(),
    }]);

    setIsProcessing(true);

    wsRef.current.send(JSON.stringify({
      type: 'text_input',
      data: { text },
    }));
  }, []);

  const handleVoiceResult = useCallback((text: string) => {
    console.log('handleVoiceResult called with:', text);
    console.log('WebSocket state:', wsRef.current?.readyState);

    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      console.error('WebSocket not connected');
      return;
    }

    setMessages(prev => [...prev, {
      role: 'user',
      content: text,
      timestamp: new Date().toISOString(),
    }]);

    setIsProcessing(true);

    wsRef.current.send(JSON.stringify({
      type: 'voice_input',
      data: { text },
    }));
  }, []);

  const handleClearChat = useCallback(() => {
    setMessages([]);
  }, []);

  const handleClearCanvas = useCallback(() => {
    setGeneratedImage(null);
    setImagePrompt('');
  }, []);

  const handleReset = useCallback(() => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;

    wsRef.current.send(JSON.stringify({ type: 'reset' }));

    setMessages([]);
    setGeneratedImage(null);
    setImagePrompt('');
    setPhase('idle');
    setStyle('flat');
    setElements([]);
    setColorPalette([]);
    setImageCount(0);
  }, []);

  return (
    <div style={styles.app}>
      {/* 头部 */}
      <header style={styles.header}>
        <div style={styles.headerContent}>
          <h1 style={styles.title}>Voice Designer</h1>
          <p style={styles.subtitle}>AI 驱动的语音设计助手</p>
        </div>
        <div style={styles.headerActions}>
          <span style={{
            ...styles.statusDot,
            backgroundColor: connected ? '#4CAF50' : '#f44336',
          }} />
          <span style={styles.statusText}>
            {connected ? '已连接' : '连接中...'}
          </span>
          <button style={styles.clearButton} onClick={handleClearChat}>
            清除对话
          </button>
          <button style={styles.clearButton} onClick={handleClearCanvas}>
            清除画布
          </button>
          <button style={styles.resetButton} onClick={handleReset}>
            全部重置
          </button>
        </div>
      </header>

      {/* 主内容 */}
      <main style={styles.main}>
        {/* 左侧：对话和语音 */}
        <div style={styles.leftPanel}>
          <ChatPanel messages={messages} isProcessing={isProcessing} />
          <VoiceInput
            onResult={handleVoiceResult}
            onSendText={sendText}
            isProcessing={isProcessing}
          />
        </div>

        {/* 中间：设计画布 */}
        <div style={styles.centerPanel}>
          <DesignCanvas
            imageUrl={generatedImage || undefined}
            isGenerating={isGenerating}
            prompt={imagePrompt}
          />
        </div>

        {/* 右侧：设计信息 */}
        <div style={styles.rightPanel}>
          <DesignInfo
            phase={phase}
            style={style}
            elements={elements}
            colorPalette={colorPalette}
            imageCount={imageCount}
          />
        </div>
      </main>

      {/* 底部提示 */}
      <footer style={styles.footer}>
        <p>提示：说出你想设计的内容，例如"帮我设计一个科技感的海报"</p>
      </footer>
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  app: {
    minHeight: '100vh',
    display: 'flex',
    flexDirection: 'column',
    backgroundColor: '#f5f5f5',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Microsoft YaHei", sans-serif',
  },
  header: {
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    color: 'white',
    padding: '16px 24px',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  headerContent: {},
  title: {
    margin: '0 0 4px 0',
    fontSize: '24px',
    fontWeight: 'bold',
  },
  subtitle: {
    margin: 0,
    fontSize: '12px',
    opacity: 0.9,
  },
  headerActions: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  statusDot: {
    width: '8px',
    height: '8px',
    borderRadius: '50%',
  },
  statusText: {
    fontSize: '12px',
  },
  clearButton: {
    padding: '6px 12px',
    fontSize: '12px',
    border: '1px solid rgba(255,255,255,0.3)',
    borderRadius: '6px',
    backgroundColor: 'rgba(255,255,255,0.1)',
    color: 'white',
    cursor: 'pointer',
  },
  resetButton: {
    padding: '6px 12px',
    fontSize: '12px',
    border: '1px solid rgba(255,255,255,0.5)',
    borderRadius: '6px',
    backgroundColor: 'rgba(255,255,255,0.2)',
    color: 'white',
    cursor: 'pointer',
    fontWeight: '600',
  },
  main: {
    flex: 1,
    display: 'flex',
    gap: '16px',
    padding: '16px',
    overflow: 'hidden',
  },
  leftPanel: {
    width: '320px',
    display: 'flex',
    flexDirection: 'column',
    gap: '16px',
  },
  centerPanel: {
    flex: 1,
    minWidth: 0,
  },
  rightPanel: {
    width: '260px',
  },
  footer: {
    padding: '12px',
    textAlign: 'center',
    fontSize: '12px',
    color: '#666',
    borderTop: '1px solid #e0e0e0',
    backgroundColor: '#fff',
  },
};

export default AppV2;
