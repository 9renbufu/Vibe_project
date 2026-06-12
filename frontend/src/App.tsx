import React, { useCallback } from 'react';
import { DrawingCanvas } from './components/DrawingCanvas';
import { VoiceControl } from './components/VoiceControl';
import { useWebSocket } from './hooks/useWebSocket';
import { useVoiceRecognition } from './hooks/useVoiceRecognition';

const App: React.FC = () => {
  const { connected, scene, lastResponse, error, sendVoiceCommand, clearScene } = useWebSocket();

  const handleVoiceResult = useCallback((text: string) => {
    sendVoiceCommand(text);
  }, [sendVoiceCommand]);

  const {
    isListening,
    transcript,
    isSupported,
    toggleListening,
  } = useVoiceRecognition(handleVoiceResult);

  return (
    <div style={styles.app}>
      <header style={styles.header}>
        <h1 style={styles.title}>🎨 VoiceSketch AI</h1>
        <p style={styles.subtitle}>语音驱动的 AI 绘图工具</p>
        <div style={styles.status}>
          <span style={{
            ...styles.statusDot,
            backgroundColor: connected ? '#4CAF50' : '#f44336',
          }} />
          {connected ? '已连接' : '连接中...'}
        </div>
      </header>

      {error && (
        <div style={styles.error}>
          ⚠️ {error}
        </div>
      )}

      <main style={styles.main}>
        <div style={styles.canvasContainer}>
          <DrawingCanvas scene={scene} />
          {lastResponse?.explanation && (
            <div style={styles.aiResponse}>
              {lastResponse.explanation}
            </div>
          )}
        </div>

        <VoiceControl
          isListening={isListening}
          isSupported={isSupported}
          transcript={transcript}
          explanation={lastResponse?.explanation || ''}
          onToggle={toggleListening}
          onClear={clearScene}
        />
      </main>

      <footer style={styles.footer}>
        <p>VoiceSketch AI - 使用自然语言创建艺术</p>
      </footer>
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  app: {
    minHeight: '100vh',
    display: 'flex',
    flexDirection: 'column',
    backgroundColor: '#fafafa',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
  },
  header: {
    backgroundColor: '#1a1a2e',
    color: 'white',
    padding: '20px',
    textAlign: 'center',
  },
  title: {
    margin: '0 0 5px 0',
    fontSize: '28px',
  },
  subtitle: {
    margin: '0 0 10px 0',
    fontSize: '14px',
    opacity: 0.8,
  },
  status: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '8px',
    fontSize: '12px',
  },
  statusDot: {
    width: '8px',
    height: '8px',
    borderRadius: '50%',
  },
  error: {
    backgroundColor: '#ffebee',
    color: '#c62828',
    padding: '10px 20px',
    textAlign: 'center',
  },
  main: {
    flex: 1,
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'flex-start',
    gap: '30px',
    padding: '30px',
    flexWrap: 'wrap',
  },
  canvasContainer: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
  },
  aiResponse: {
    marginTop: '15px',
    padding: '10px 20px',
    backgroundColor: '#e3f2fd',
    borderRadius: '8px',
    color: '#1565c0',
    fontSize: '14px',
    maxWidth: '800px',
    textAlign: 'center',
  },
  footer: {
    backgroundColor: '#1a1a2e',
    color: 'white',
    padding: '15px',
    textAlign: 'center',
    fontSize: '12px',
  },
};

export default App;
