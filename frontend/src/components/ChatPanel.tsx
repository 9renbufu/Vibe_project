import React, { useRef, useEffect } from 'react';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
}

interface ChatPanelProps {
  messages: Message[];
  isProcessing: boolean;
}

export const ChatPanel: React.FC<ChatPanelProps> = ({ messages, isProcessing }) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h3 style={styles.title}>设计对话</h3>
        <span style={styles.badge}>{messages.length} 条消息</span>
      </div>

      <div style={styles.messages}>
        {messages.length === 0 && (
          <div style={styles.empty}>
            <div style={styles.emptyIcon}> </div>
            <p style={styles.emptyText}>开始你的设计之旅</p>
            <p style={styles.emptyHint}>告诉我你想设计什么...</p>
          </div>
        )}

        {messages.map((msg, index) => (
          <div
            key={index}
            style={{
              ...styles.message,
              ...(msg.role === 'user' ? styles.userMessage : styles.assistantMessage),
            }}
          >
            <div style={styles.messageRole}>
              {msg.role === 'user' ? ' ' : ' ️'}
            </div>
            <div style={{
              ...styles.messageContent,
              ...(msg.role === 'user' ? styles.userContent : styles.assistantContent),
            }}>
              {msg.content}
            </div>
          </div>
        ))}

        {isProcessing && (
          <div style={{ ...styles.message, ...styles.assistantMessage }}>
            <div style={styles.messageRole}> ️</div>
            <div style={styles.messageContent}>
              <span style={styles.typing}>思考中...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    height: '300px',
    backgroundColor: '#fff',
    borderRadius: '12px',
    border: '1px solid #e0e0e0',
    overflow: 'hidden',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '12px 16px',
    backgroundColor: '#f8f9fa',
    borderBottom: '1px solid #e0e0e0',
  },
  title: {
    margin: 0,
    fontSize: '14px',
    fontWeight: '600',
    color: '#333',
  },
  badge: {
    fontSize: '11px',
    color: '#666',
    backgroundColor: '#e9ecef',
    padding: '2px 8px',
    borderRadius: '10px',
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
    color: '#999',
  },
  emptyIcon: {
    fontSize: '48px',
    marginBottom: '12px',
  },
  emptyText: {
    margin: '0 0 4px 0',
    fontSize: '16px',
    color: '#666',
  },
  emptyHint: {
    margin: 0,
    fontSize: '12px',
    color: '#999',
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
  messageRole: {
    fontSize: '20px',
    flexShrink: 0,
  },
  messageContent: {
    maxWidth: '80%',
    padding: '10px 14px',
    borderRadius: '12px',
    fontSize: '14px',
    lineHeight: '1.5',
  },
  userContent: {
    backgroundColor: '#667eea',
    color: 'white',
    borderBottomRightRadius: '4px',
  },
  assistantContent: {
    backgroundColor: '#f0f0f0',
    color: '#333',
    borderBottomLeftRadius: '4px',
  },
  typing: {
    animation: 'pulse 1.5s infinite',
  },
};
