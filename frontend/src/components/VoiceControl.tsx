import React from 'react';

interface VoiceControlProps {
  isListening: boolean;
  isSupported: boolean;
  transcript: string;
  explanation: string;
  onToggle: () => void;
  onClear: () => void;
}

export const VoiceControl: React.FC<VoiceControlProps> = ({
  isListening,
  isSupported,
  transcript,
  explanation,
  onToggle,
  onClear,
}) => {
  return (
    <div style={styles.container}>
      <h2 style={styles.title}>🎤 语音控制</h2>

      {!isSupported && (
        <div style={styles.warning}>
          ⚠️ 您的浏览器不支持语音识别，请使用 Chrome
        </div>
      )}

      <button
        onClick={onToggle}
        disabled={!isSupported}
        style={{
          ...styles.button,
          ...(isListening ? styles.buttonActive : styles.buttonInactive),
          ...(!isSupported && styles.buttonDisabled),
        }}
      >
        {isListening ? '⏹ 停止录音' : '🎙️ 开始说话'}
      </button>

      <button onClick={onClear} style={styles.clearButton}>
        🗑️ 清空画布
      </button>

      {isListening && (
        <div style={styles.listeningIndicator}>
          <span style={styles.pulse}>🔴</span> 正在聆听...
        </div>
      )}

      {transcript && (
        <div style={styles.transcriptBox}>
          <div style={styles.label}>识别到的语音:</div>
          <div style={styles.transcript}>{transcript}</div>
        </div>
      )}

      {explanation && (
        <div style={styles.explanationBox}>
          <div style={styles.label}>AI 解释:</div>
          <div style={styles.explanation}>{explanation}</div>
        </div>
      )}

      <div style={styles.instructions}>
        <h3>💡 使用说明</h3>
        <ul style={styles.list}>
          <li>点击"开始说话"按钮</li>
          <li>说出你想画的内容</li>
          <li>例如："画一个红色的太阳"</li>
          <li>或者："画一个海边日落场景"</li>
          <li>可以指定移动物体："把太阳移到左边"</li>
        </ul>
      </div>
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  container: {
    padding: '20px',
    backgroundColor: '#f5f5f5',
    borderRadius: '12px',
    width: '300px',
  },
  title: {
    margin: '0 0 20px 0',
    fontSize: '20px',
    textAlign: 'center',
  },
  button: {
    width: '100%',
    padding: '15px',
    fontSize: '18px',
    border: 'none',
    borderRadius: '8px',
    cursor: 'pointer',
    marginBottom: '10px',
    transition: 'all 0.3s',
  },
  buttonActive: {
    backgroundColor: '#ff4444',
    color: 'white',
  },
  buttonInactive: {
    backgroundColor: '#4CAF50',
    color: 'white',
  },
  buttonDisabled: {
    backgroundColor: '#ccc',
    cursor: 'not-allowed',
  },
  clearButton: {
    width: '100%',
    padding: '10px',
    fontSize: '14px',
    border: '1px solid #ddd',
    borderRadius: '8px',
    cursor: 'pointer',
    backgroundColor: 'white',
    marginBottom: '15px',
  },
  listeningIndicator: {
    textAlign: 'center',
    padding: '10px',
    color: '#ff4444',
    fontWeight: 'bold',
  },
  pulse: {
    animation: 'pulse 1s infinite',
  },
  transcriptBox: {
    backgroundColor: 'white',
    padding: '12px',
    borderRadius: '8px',
    marginBottom: '10px',
  },
  label: {
    fontSize: '12px',
    color: '#666',
    marginBottom: '5px',
  },
  transcript: {
    fontSize: '16px',
    color: '#333',
  },
  explanationBox: {
    backgroundColor: '#e8f5e9',
    padding: '12px',
    borderRadius: '8px',
    marginBottom: '15px',
  },
  explanation: {
    fontSize: '14px',
    color: '#2e7d32',
  },
  instructions: {
    backgroundColor: 'white',
    padding: '15px',
    borderRadius: '8px',
  },
  list: {
    paddingLeft: '20px',
    margin: '10px 0 0 0',
    fontSize: '14px',
    lineHeight: '1.8',
  },
  warning: {
    backgroundColor: '#fff3cd',
    color: '#856404',
    padding: '10px',
    borderRadius: '8px',
    marginBottom: '15px',
    textAlign: 'center',
  },
};
