/**
 * Design Workspace - 设计工作区（中间面板）
 */

import React, { useState } from 'react';
import { useAgentStore } from '../../store/agentStore';

export const DesignWorkspace: React.FC = () => {
  const {
    generatedImage,
    isGenerating,
    imagePrompt,
    versions,
    currentTask,
  } = useAgentStore();

  const [zoom, setZoom] = useState(1);
  const [showVersions, setShowVersions] = useState(false);

  const handleZoomIn = () => setZoom((z) => Math.min(z + 0.25, 3));
  const handleZoomOut = () => setZoom((z) => Math.max(z - 0.25, 0.25));
  const handleZoomReset = () => setZoom(1);

  const handleDownload = () => {
    if (!generatedImage) return;
    const link = document.createElement('a');
    link.href = generatedImage;
    link.download = `design-${Date.now()}.png`;
    link.click();
  };

  return (
    <div style={styles.container}>
      {/* Header */}
      <div style={styles.header}>
        <div style={styles.headerLeft}>
          <span style={styles.title}>Design Canvas</span>
          {currentTask && (
            <span style={styles.taskBadge}>{currentTask.slice(0, 30)}...</span>
          )}
        </div>
        <div style={styles.headerRight}>
          {generatedImage && (
            <>
              <button style={styles.toolBtn} onClick={handleZoomOut}>
                -
              </button>
              <span style={styles.zoomLabel}>{Math.round(zoom * 100)}%</span>
              <button style={styles.toolBtn} onClick={handleZoomIn}>
                +
              </button>
              <button style={styles.toolBtn} onClick={handleZoomReset}>
                Fit
              </button>
              <div style={styles.divider} />
              <button style={styles.toolBtn} onClick={handleDownload}>
                Download
              </button>
            </>
          )}
          <button
            style={{
              ...styles.toolBtn,
              ...(showVersions ? styles.toolBtnActive : {}),
            }}
            onClick={() => setShowVersions(!showVersions)}
          >
            History ({versions.length})
          </button>
        </div>
      </div>

      {/* Canvas Area */}
      <div style={styles.canvasArea}>
        {isGenerating ? (
          <div style={styles.generatingState}>
            <div style={styles.spinner} />
            <p style={styles.generatingText}>Generating design...</p>
            <p style={styles.generatingSubtext}>This may take 30-120 seconds</p>
            {imagePrompt && (
              <p style={styles.promptPreview}>
                Prompt: {imagePrompt.slice(0, 80)}...
              </p>
            )}
          </div>
        ) : generatedImage ? (
          <div style={styles.imageContainer}>
            <img
              src={generatedImage}
              alt="Generated design"
              style={{
                ...styles.image,
                transform: `scale(${zoom})`,
              }}
            />
          </div>
        ) : (
          <div style={styles.emptyState}>
            <div style={styles.emptyIcon}> </div>
            <h3 style={styles.emptyTitle}>Design Canvas</h3>
            <p style={styles.emptyText}>
              Describe your design idea in the conversation panel
            </p>
            <div style={styles.hints}>
              <div style={styles.hintItem}>
                <span style={styles.hintIcon}> </span>
                <span>Use voice or text input</span>
              </div>
              <div style={styles.hintItem}>
                <span style={styles.hintIcon}> </span>
                <span>Describe style and elements</span>
              </div>
              <div style={styles.hintItem}>
                <span style={styles.hintIcon}> </span>
                <span>Request modifications anytime</span>
              </div>
            </div>
          </div>
        )}

        {/* Version History Sidebar */}
        {showVersions && versions.length > 0 && (
          <div style={styles.versionPanel}>
            <div style={styles.versionHeader}>
              <span style={styles.versionTitle}>Version History</span>
              <button
                style={styles.closeBtn}
                onClick={() => setShowVersions(false)}
              >
                x
              </button>
            </div>
            <div style={styles.versionList}>
              {versions.map((v) => (
                <div
                  key={v.id}
                  style={styles.versionItem}
                  onClick={() => {
                    useAgentStore.getState().rollbackVersion(v.id);
                    setShowVersions(false);
                  }}
                >
                  <div style={styles.versionThumb}>
                    <img src={v.imageUrl} alt={v.version} style={styles.versionImg} />
                  </div>
                  <div style={styles.versionInfo}>
                    <span style={styles.versionName}>{v.version}</span>
                    <span style={styles.versionTime}>
                      {new Date(v.timestamp).toLocaleTimeString()}
                    </span>
                    {v.changes.length > 0 && (
                      <span style={styles.versionChanges}>
                        {v.changes[0]}
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Footer with prompt */}
      {imagePrompt && !isGenerating && (
        <div style={styles.footer}>
          <span style={styles.footerLabel}>Prompt:</span>
          <span style={styles.footerText}>{imagePrompt}</span>
        </div>
      )}
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    height: '100%',
    backgroundColor: '#f9fafb',
    borderRadius: '12px',
    border: '1px solid #e5e7eb',
    overflow: 'hidden',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '10px 16px',
    borderBottom: '1px solid #e5e7eb',
    backgroundColor: '#fff',
  },
  headerLeft: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  title: {
    fontSize: '13px',
    fontWeight: '600',
    color: '#111827',
  },
  taskBadge: {
    fontSize: '11px',
    color: '#6b7280',
    backgroundColor: '#f3f4f6',
    padding: '2px 8px',
    borderRadius: '4px',
  },
  headerRight: {
    display: 'flex',
    alignItems: 'center',
    gap: '4px',
  },
  toolBtn: {
    padding: '4px 10px',
    fontSize: '11px',
    border: '1px solid #d1d5db',
    borderRadius: '4px',
    backgroundColor: '#fff',
    cursor: 'pointer',
    color: '#374151',
  },
  toolBtnActive: {
    backgroundColor: '#eff6ff',
    borderColor: '#3b82f6',
    color: '#3b82f6',
  },
  zoomLabel: {
    fontSize: '11px',
    color: '#6b7280',
    minWidth: '36px',
    textAlign: 'center',
  },
  divider: {
    width: '1px',
    height: '16px',
    backgroundColor: '#e5e7eb',
    margin: '0 4px',
  },
  canvasArea: {
    flex: 1,
    position: 'relative',
    overflow: 'hidden',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  imageContainer: {
    width: '100%',
    height: '100%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    overflow: 'auto',
    padding: '20px',
  },
  image: {
    maxWidth: '100%',
    maxHeight: '100%',
    objectFit: 'contain',
    borderRadius: '8px',
    boxShadow: '0 4px 20px rgba(0,0,0,0.1)',
    transition: 'transform 0.2s',
  },
  emptyState: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '40px',
    textAlign: 'center',
  },
  emptyIcon: {
    fontSize: '64px',
    marginBottom: '16px',
  },
  emptyTitle: {
    margin: '0 0 8px 0',
    fontSize: '20px',
    fontWeight: '600',
    color: '#111827',
  },
  emptyText: {
    margin: '0 0 24px 0',
    fontSize: '14px',
    color: '#6b7280',
  },
  hints: {
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
  },
  hintItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    fontSize: '13px',
    color: '#9ca3af',
  },
  hintIcon: {
    fontSize: '16px',
  },
  generatingState: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '40px',
    textAlign: 'center',
  },
  spinner: {
    width: '48px',
    height: '48px',
    border: '3px solid #e5e7eb',
    borderTopColor: '#6366f1',
    borderRadius: '50%',
    animation: 'spin 1s linear infinite',
    marginBottom: '16px',
  },
  generatingText: {
    margin: '0 0 4px 0',
    fontSize: '16px',
    fontWeight: '500',
    color: '#111827',
  },
  generatingSubtext: {
    margin: '0 0 12px 0',
    fontSize: '12px',
    color: '#9ca3af',
  },
  promptPreview: {
    margin: 0,
    fontSize: '12px',
    color: '#9ca3af',
    maxWidth: '400px',
  },
  versionPanel: {
    position: 'absolute',
    right: 0,
    top: 0,
    bottom: 0,
    width: '240px',
    backgroundColor: '#fff',
    borderLeft: '1px solid #e5e7eb',
    display: 'flex',
    flexDirection: 'column',
    zIndex: 10,
  },
  versionHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '12px',
    borderBottom: '1px solid #e5e7eb',
  },
  versionTitle: {
    fontSize: '13px',
    fontWeight: '600',
    color: '#111827',
  },
  closeBtn: {
    background: 'none',
    border: 'none',
    fontSize: '16px',
    cursor: 'pointer',
    color: '#6b7280',
    padding: '2px 6px',
  },
  versionList: {
    flex: 1,
    overflowY: 'auto',
    padding: '8px',
  },
  versionItem: {
    display: 'flex',
    gap: '8px',
    padding: '8px',
    borderRadius: '6px',
    cursor: 'pointer',
    marginBottom: '4px',
  },
  versionThumb: {
    width: '48px',
    height: '48px',
    borderRadius: '4px',
    overflow: 'hidden',
    flexShrink: 0,
  },
  versionImg: {
    width: '100%',
    height: '100%',
    objectFit: 'cover',
  },
  versionInfo: {
    display: 'flex',
    flexDirection: 'column',
    gap: '2px',
    minWidth: 0,
  },
  versionName: {
    fontSize: '12px',
    fontWeight: '500',
    color: '#111827',
  },
  versionTime: {
    fontSize: '10px',
    color: '#9ca3af',
  },
  versionChanges: {
    fontSize: '10px',
    color: '#6b7280',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap',
  },
  footer: {
    padding: '8px 16px',
    borderTop: '1px solid #e5e7eb',
    backgroundColor: '#fff',
    display: 'flex',
    gap: '8px',
    alignItems: 'flex-start',
  },
  footerLabel: {
    fontSize: '11px',
    fontWeight: '600',
    color: '#6b7280',
    flexShrink: 0,
  },
  footerText: {
    fontSize: '11px',
    color: '#9ca3af',
    lineHeight: '1.4',
  },
};
