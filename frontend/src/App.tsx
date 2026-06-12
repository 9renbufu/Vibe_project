import React, { useCallback, useEffect } from 'react';
import { EnhancedCanvas } from './components/EnhancedCanvas';
import { VoiceControl } from './components/VoiceControl';
import { ControlPanel } from './components/ControlPanel';
import { useWebSocket } from './hooks/useWebSocket';
import { useVoiceRecognition } from './hooks/useVoiceRecognition';
import { useHistory } from './hooks/useHistory';
import { useRecording } from './hooks/useRecording';
import { useVoiceCommands } from './hooks/useVoiceCommands';
import { SceneState } from './types';

const defaultScene: SceneState = {
  shapes: [],
  background: { r: 255, g: 255, b: 255 },
  width: 800,
  height: 600,
};

const App: React.FC = () => {
  const { connected, scene, lastResponse, error, sendVoiceCommand, clearScene } = useWebSocket();
  const { state: currentScene, pushState, undo, redo, canUndo, canRedo, historyLength } = useHistory(defaultScene);
  const { isRecording, isPlaying, startRecording, stopRecording, recordFrame, playRecording, exportRecording } = useRecording();

  // 同步 WebSocket 场景到历史记录
  useEffect(() => {
    if (scene.shapes.length > 0 || scene.shapes.length !== currentScene.shapes.length) {
      pushState(scene);
    }
  }, [scene]);

  // 录制帧
  useEffect(() => {
    if (isRecording && lastResponse) {
      recordFrame(currentScene, lastResponse?.explanation);
    }
  }, [currentScene, lastResponse, isRecording]);

  const handleDraw = useCallback((text: string) => {
    sendVoiceCommand(text);
  }, [sendVoiceCommand]);

  const handleClear = useCallback(() => {
    clearScene();
    pushState(defaultScene);
  }, [clearScene, pushState]);

  const handlePlayRecording = useCallback(() => {
    playRecording((frameScene, _explanation) => {
      pushState(frameScene);
    });
  }, [playRecording, pushState]);

  const handleExportRecording = useCallback(() => {
    const data = exportRecording();
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `voicesketch-recording-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [exportRecording]);

  const { processCommand } = useVoiceCommands({
    onDraw: handleDraw,
    onUndo: undo,
    onRedo: redo,
    onClear: handleClear,
    onStartRecording: startRecording,
    onStopRecording: stopRecording,
    onPlayRecording: handlePlayRecording,
  });

  const {
    isListening,
    transcript,
    isSupported,
    toggleListening,
  } = useVoiceRecognition(processCommand);

  return (
    <div style={styles.app}>
      <header style={styles.header}>
        <h1 style={styles.title}>VoiceSketch AI</h1>
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
          {error}
        </div>
      )}

      <main style={styles.main}>
        <div style={styles.canvasSection}>
          <EnhancedCanvas scene={currentScene} />
          {lastResponse?.explanation && (
            <div style={styles.explanation}>
              {lastResponse.explanation}
            </div>
          )}
        </div>

        <div style={styles.sidebar}>
          <VoiceControl
            isListening={isListening}
            isSupported={isSupported}
            transcript={transcript}
            explanation={lastResponse?.explanation || ''}
            onToggle={toggleListening}
            onClear={handleClear}
          />

          <div style={{ marginTop: '15px' }}>
            <ControlPanel
              canUndo={canUndo}
              canRedo={canRedo}
              isRecording={isRecording}
              isPlaying={isPlaying}
              historyLength={historyLength}
              onUndo={undo}
              onRedo={redo}
              onClear={handleClear}
              onStartRecording={startRecording}
              onStopRecording={stopRecording}
              onPlayRecording={handlePlayRecording}
              onExportRecording={handleExportRecording}
            />
          </div>
        </div>
      </main>

      <footer style={styles.footer}>
        <p>VoiceSketch AI - 使用自然语言创建艺术 | 毕业设计作品</p>
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
    fontFamily: '-apple-system, BlinkMacSystemFont, "Microsoft YaHei", "Segoe UI", Roboto, sans-serif',
  },
  header: {
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    color: 'white',
    padding: '20px',
    textAlign: 'center',
  },
  title: {
    margin: '0 0 5px 0',
    fontSize: '28px',
    fontWeight: 'bold',
  },
  subtitle: {
    margin: '0 0 10px 0',
    fontSize: '14px',
    opacity: 0.9,
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
    gap: '20px',
    padding: '20px',
    flexWrap: 'wrap',
  },
  canvasSection: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
  },
  explanation: {
    marginTop: '12px',
    padding: '10px 20px',
    backgroundColor: '#e3f2fd',
    borderRadius: '8px',
    color: '#1565c0',
    fontSize: '14px',
    maxWidth: '800px',
    textAlign: 'center',
  },
  sidebar: {
    display: 'flex',
    flexDirection: 'column',
    width: '320px',
  },
  footer: {
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    color: 'white',
    padding: '15px',
    textAlign: 'center',
    fontSize: '12px',
  },
};

export default App;
