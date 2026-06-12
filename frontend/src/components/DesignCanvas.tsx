import React, { useState } from 'react';

interface DesignCanvasProps {
  imageUrl?: string;
  isGenerating: boolean;
  prompt?: string;
}

export const DesignCanvas: React.FC<DesignCanvasProps> = ({
  imageUrl,
  isGenerating,
  prompt,
}) => {
  const [isFullscreen, setIsFullscreen] = useState(false);

  const imageSrc = imageUrl
    ? imageUrl.startsWith('data:') ? imageUrl : `data:image/png;base64,${imageUrl}`
    : null;

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h3 style={styles.title}>设计画布</h3>
        {prompt && (
          <span style={styles.prompt} title={prompt}>
            {prompt.substring(0, 30)}...
          </span>
        )}
      </div>

      <div style={styles.canvas}>
        {isGenerating ? (
          <div style={styles.loading}>
            <div style={styles.loadingIcon}> </div>
            <p style={styles.loadingText}>正在生成设计...</p>
            <p style={styles.loadingHint}>AI 正在创作中，请稍候</p>
          </div>
        ) : imageSrc ? (
          <div style={styles.imageContainer}>
            <img
              src={imageSrc}
              alt="Generated Design"
              style={{
                ...styles.image,
                ...(isFullscreen ? styles.imageFullscreen : {}),
              }}
              onClick={() => setIsFullscreen(!isFullscreen)}
            />
            <div style={styles.imageActions}>
              <button
                style={styles.actionButton}
                onClick={() => setIsFullscreen(!isFullscreen)}
              >
                {isFullscreen ? '退出全屏' : '全屏查看'}
              </button>
              <button
                style={styles.actionButton}
                onClick={() => {
                  const a = document.createElement('a');
                  a.href = imageSrc;
                  a.download = `design-${Date.now()}.png`;
                  a.click();
                }}
              >
                下载图片
              </button>
            </div>
          </div>
        ) : (
          <div style={styles.empty}>
            <div style={styles.emptyIcon}> </div>
            <p style={styles.emptyText}>等待设计生成</p>
            <p style={styles.emptyHint}>描述你想要的设计，AI 将为你生成</p>
          </div>
        )}
      </div>
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  container: {
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
  prompt: {
    fontSize: '11px',
    color: '#666',
    maxWidth: '200px',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap',
  },
  canvas: {
    minHeight: '400px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#fafafa',
  },
  loading: {
    textAlign: 'center',
    padding: '40px',
  },
  loadingIcon: {
    fontSize: '64px',
    marginBottom: '16px',
    animation: 'spin 2s linear infinite',
  },
  loadingText: {
    margin: '0 0 8px 0',
    fontSize: '18px',
    color: '#333',
  },
  loadingHint: {
    margin: 0,
    fontSize: '12px',
    color: '#999',
  },
  imageContainer: {
    width: '100%',
    padding: '16px',
  },
  image: {
    width: '100%',
    height: 'auto',
    borderRadius: '8px',
    cursor: 'pointer',
    transition: 'transform 0.2s',
  },
  imageFullscreen: {
    position: 'fixed',
    top: 0,
    left: 0,
    width: '100vw',
    height: '100vh',
    objectFit: 'contain',
    backgroundColor: 'rgba(0,0,0,0.9)',
    zIndex: 1000,
    borderRadius: 0,
  },
  imageActions: {
    display: 'flex',
    gap: '8px',
    justifyContent: 'center',
    marginTop: '12px',
  },
  actionButton: {
    padding: '8px 16px',
    fontSize: '12px',
    border: '1px solid #ddd',
    borderRadius: '6px',
    backgroundColor: '#fff',
    cursor: 'pointer',
  },
  empty: {
    textAlign: 'center',
    padding: '60px 20px',
  },
  emptyIcon: {
    fontSize: '64px',
    marginBottom: '16px',
    opacity: 0.3,
  },
  emptyText: {
    margin: '0 0 8px 0',
    fontSize: '18px',
    color: '#666',
  },
  emptyHint: {
    margin: 0,
    fontSize: '12px',
    color: '#999',
  },
};
