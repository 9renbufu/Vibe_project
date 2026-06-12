/**
 * Voice Designer - Agent Workspace
 */

import React from 'react';
import { ConversationPanel } from './components/AgentWorkspace/ConversationPanel';
import { DesignWorkspace } from './components/AgentWorkspace/DesignWorkspace';
import { AgentPanel } from './components/AgentWorkspace/AgentPanel';

const App: React.FC = () => {
  return (
    <div style={styles.app}>
      {/* Left: Conversation Panel */}
      <div style={styles.leftPanel}>
        <ConversationPanel />
      </div>

      {/* Center: Design Workspace */}
      <div style={styles.centerPanel}>
        <DesignWorkspace />
      </div>

      {/* Right: Agent Panel */}
      <div style={styles.rightPanel}>
        <AgentPanel />
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
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", sans-serif',
    backgroundColor: '#f3f4f6',
  },
  leftPanel: {
    width: '340px',
    flexShrink: 0,
  },
  centerPanel: {
    flex: 1,
    minWidth: 0,
    padding: '12px',
  },
  rightPanel: {
    width: '280px',
    flexShrink: 0,
  },
};

export default App;
