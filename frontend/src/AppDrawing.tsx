/**
 * 语音绘图工具 - 主布局
 */

import React from 'react';
import VoicePanel from './components/DrawingWorkspace/VoicePanel';
import ProceduralCanvas from './components/DrawingCanvas/ProceduralCanvas';
import StatusPanel from './components/DrawingWorkspace/StatusPanel';

const AppDrawing: React.FC = () => {
  return (
    <div style={styles.app}>
      <div style={styles.leftPanel}>
        <VoicePanel />
      </div>
      <div style={styles.centerPanel}>
        <ProceduralCanvas />
      </div>
      <div style={styles.rightPanel}>
        <StatusPanel />
      </div>
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  app: {
    display: 'flex',
    height: '100vh',
    width: '100vw',
    overflow: 'hidden',
    backgroundColor: '#f3f4f6',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", sans-serif',
  },
  leftPanel: {
    width: '340px',
    flexShrink: 0,
    overflow: 'hidden',
  },
  centerPanel: {
    flex: 1,
    padding: '12px',
    minWidth: 0,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  rightPanel: {
    width: '280px',
    flexShrink: 0,
    overflow: 'hidden',
  },
};

export default AppDrawing;
