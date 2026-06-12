import React from 'react';

interface ControlPanelProps {
  canUndo: boolean;
  canRedo: boolean;
  isRecording: boolean;
  isPlaying: boolean;
  historyLength: number;
  onUndo: () => void;
  onRedo: () => void;
  onClear: () => void;
  onStartRecording: () => void;
  onStopRecording: () => void;
  onPlayRecording: () => void;
  onExportRecording: () => void;
}

export const ControlPanel: React.FC<ControlPanelProps> = ({
  canUndo,
  canRedo,
  isRecording,
  isPlaying,
  historyLength,
  onUndo,
  onRedo,
  onClear,
  onStartRecording,
  onStopRecording,
  onPlayRecording,
  onExportRecording,
}) => {
  return (
    <div style={styles.container}>
      <h3 style={styles.title}>控制面板</h3>

      <div style={styles.section}>
        <span style={styles.label}>历史记录: {historyLength} 步</span>
        <div style={styles.buttonGroup}>
          <button
            onClick={onUndo}
            disabled={!canUndo}
            style={{
              ...styles.button,
              ...(canUndo ? {} : styles.buttonDisabled),
            }}
          >
            ↩️ 撤销
          </button>
          <button
            onClick={onRedo}
            disabled={!canRedo}
            style={{
              ...styles.button,
              ...(canRedo ? {} : styles.buttonDisabled),
            }}
          >
            ↪️ 重做
          </button>
          <button onClick={onClear} style={styles.buttonDanger}>
            🗑️ 清空
          </button>
        </div>
      </div>

      <div style={styles.section}>
        <span style={styles.label}>录制回放</span>
        <div style={styles.buttonGroup}>
          {!isRecording ? (
            <button
              onClick={onStartRecording}
              disabled={isPlaying}
              style={styles.buttonSuccess}
            >
              ⏺️ 开始录制
            </button>
          ) : (
            <button onClick={onStopRecording} style={styles.buttonDanger}>
              ⏹️ 停止录制
            </button>
          )}
          <button
            onClick={onPlayRecording}
            disabled={isRecording || isPlaying}
            style={{
              ...styles.button,
              ...((isRecording || isPlaying) ? styles.buttonDisabled : {}),
            }}
          >
            ▶️ 回放
          </button>
          <button onClick={onExportRecording} style={styles.button}>
            💾 导出
          </button>
        </div>
      </div>

      {isRecording && (
        <div style={styles.recordingIndicator}>
          <span style={styles.recordingDot}>🔴</span> 录制中...
        </div>
      )}

      {isPlaying && (
        <div style={styles.playingIndicator}>
          <span style={styles.playingIcon}>▶️</span> 回放中...
        </div>
      )}

      <div style={styles.voiceCommands}>
        <h4 style={styles.commandsTitle}>语音命令</h4>
        <ul style={styles.commandsList}>
          <li>"撤销" / "undo" - 撤销上一步</li>
          <li>"重做" / "redo" - 恢复操作</li>
          <li>"清空" / "clear" - 清空画布</li>
          <li>"开始录制" - 开始记录绘图过程</li>
          <li>"停止录制" - 停止记录</li>
          <li>"回放" - 播放录制过程</li>
        </ul>
      </div>
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  container: {
    padding: '15px',
    backgroundColor: '#f8f9fa',
    borderRadius: '12px',
    border: '1px solid #e9ecef',
  },
  title: {
    margin: '0 0 15px 0',
    fontSize: '16px',
    color: '#333',
  },
  section: {
    marginBottom: '15px',
  },
  label: {
    display: 'block',
    fontSize: '12px',
    color: '#666',
    marginBottom: '8px',
  },
  buttonGroup: {
    display: 'flex',
    gap: '8px',
    flexWrap: 'wrap',
  },
  button: {
    padding: '8px 12px',
    fontSize: '12px',
    border: '1px solid #ddd',
    borderRadius: '6px',
    backgroundColor: 'white',
    cursor: 'pointer',
    transition: 'all 0.2s',
  },
  buttonDisabled: {
    opacity: 0.5,
    cursor: 'not-allowed',
  },
  buttonDanger: {
    padding: '8px 12px',
    fontSize: '12px',
    border: '1px solid #dc3545',
    borderRadius: '6px',
    backgroundColor: '#fff5f5',
    color: '#dc3545',
    cursor: 'pointer',
  },
  buttonSuccess: {
    padding: '8px 12px',
    fontSize: '12px',
    border: '1px solid #28a745',
    borderRadius: '6px',
    backgroundColor: '#f0fff4',
    color: '#28a745',
    cursor: 'pointer',
  },
  recordingIndicator: {
    padding: '8px',
    backgroundColor: '#fff5f5',
    borderRadius: '6px',
    textAlign: 'center',
    color: '#dc3545',
    fontSize: '12px',
    fontWeight: 'bold',
    marginBottom: '10px',
  },
  recordingDot: {
    animation: 'pulse 1s infinite',
  },
  playingIndicator: {
    padding: '8px',
    backgroundColor: '#e3f2fd',
    borderRadius: '6px',
    textAlign: 'center',
    color: '#1976d2',
    fontSize: '12px',
    fontWeight: 'bold',
    marginBottom: '10px',
  },
  playingIcon: {
    marginRight: '4px',
  },
  voiceCommands: {
    backgroundColor: 'white',
    padding: '12px',
    borderRadius: '8px',
    marginTop: '10px',
  },
  commandsTitle: {
    margin: '0 0 8px 0',
    fontSize: '14px',
    color: '#333',
  },
  commandsList: {
    margin: 0,
    paddingLeft: '20px',
    fontSize: '12px',
    lineHeight: '1.8',
    color: '#666',
  },
};
