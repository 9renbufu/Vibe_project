import React, { useState } from 'react';

interface ImageDisplayProps {
  imageUrl?: string;
  imagePrompt?: string;
}

export const ImageDisplay: React.FC<ImageDisplayProps> = ({ imageUrl, imagePrompt }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  if (!imageUrl) return null;

  const src = imageUrl.startsWith('data:')
    ? imageUrl
    : `data:image/png;base64,${imageUrl}`;

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h3 style={styles.title}>🎨 AI 生成图像</h3>
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          style={styles.toggleButton}
        >
          {isExpanded ? '收起' : '展开'}
        </button>
      </div>

      {imagePrompt && (
        <div style={styles.promptBox}>
          <span style={styles.promptLabel}>提示词:</span>
          <span style={styles.promptText}>{imagePrompt}</span>
        </div>
      )}

      <div style={{
        ...styles.imageContainer,
        ...(isExpanded ? styles.imageExpanded : styles.imageCollapsed),
      }}>
        <img
          src={src}
          alt="AI Generated"
          style={styles.image}
          onClick={() => setIsExpanded(!isExpanded)}
        />
      </div>
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  container: {
    backgroundColor: '#f8f9fa',
    borderRadius: '12px',
    padding: '15px',
    marginTop: '15px',
    border: '1px solid #e9ecef',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '10px',
  },
  title: {
    margin: 0,
    fontSize: '16px',
    color: '#333',
  },
  toggleButton: {
    padding: '4px 12px',
    fontSize: '12px',
    border: '1px solid #ddd',
    borderRadius: '4px',
    backgroundColor: 'white',
    cursor: 'pointer',
  },
  promptBox: {
    backgroundColor: '#fff',
    padding: '8px 12px',
    borderRadius: '6px',
    marginBottom: '10px',
    fontSize: '12px',
  },
  promptLabel: {
    color: '#666',
    marginRight: '8px',
  },
  promptText: {
    color: '#333',
    fontStyle: 'italic',
  },
  imageContainer: {
    overflow: 'hidden',
    borderRadius: '8px',
    transition: 'max-height 0.3s ease',
  },
  imageCollapsed: {
    maxHeight: '200px',
  },
  imageExpanded: {
    maxHeight: '600px',
  },
  image: {
    width: '100%',
    height: 'auto',
    display: 'block',
    cursor: 'pointer',
  },
};
