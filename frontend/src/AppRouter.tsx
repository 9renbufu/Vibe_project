/**
 * 模式切换器 - Agent 模式 / 绘图模式
 */

import React, { useState } from 'react';
import App from './App';
import AppDrawing from './AppDrawing';

const AppRouter: React.FC = () => {
  const [mode, setMode] = useState<'agent' | 'drawing'>('drawing');

  return (
    <>
      <div style={styles.modeBar}>
        <button
          style={{
            ...styles.modeBtn,
            ...(mode === 'drawing' ? styles.modeBtnActive : {}),
          }}
          onClick={() => setMode('drawing')}
        >
           语音绘图
        </button>
        <button
          style={{
            ...styles.modeBtn,
            ...(mode === 'agent' ? styles.modeBtnActive : {}),
          }}
          onClick={() => setMode('agent')}
        >
           AI Designer
        </button>
      </div>
      {mode === 'agent' ? <App /> : <AppDrawing />}
    </>
  );
};

const styles: Record<string, React.CSSProperties> = {
  modeBar: {
    position: 'fixed',
    top: '8px',
    left: '50%',
    transform: 'translateX(-50%)',
    display: 'flex',
    gap: '4px',
    backgroundColor: '#1f2937',
    borderRadius: '8px',
    padding: '3px',
    zIndex: 1000,
    boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
  },
  modeBtn: {
    padding: '6px 16px',
    fontSize: '12px',
    fontWeight: '500',
    border: 'none',
    borderRadius: '6px',
    backgroundColor: 'transparent',
    color: '#9ca3af',
    cursor: 'pointer',
    transition: 'all 0.2s',
    whiteSpace: 'nowrap',
  },
  modeBtnActive: {
    backgroundColor: '#6366f1',
    color: '#ffffff',
  },
};

export default AppRouter;
