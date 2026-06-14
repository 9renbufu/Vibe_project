/**
 * 画作评估面板 - 显示 LLM 评分、反馈和修改建议
 */

import React from 'react';
import { useDrawingStore } from '../../store/drawingStore';
import { sendAcceptSuggestion, sendRejectSuggestion, sendEvaluate } from '../../store/wsManager';

const EvaluationPanel: React.FC = () => {
  const { evaluation } = useDrawingStore();

  if (!evaluation) {
    return (
      <div style={styles.container}>
        <div style={styles.header}>
          <span style={styles.title}>AI 评估</span>
        </div>
        <div style={styles.empty}>
          <span style={styles.emptyIcon}>✨</span>
          <span>绘图后自动评估</span>
          <button style={styles.evalBtn} onClick={() => sendEvaluate()}>
            手动评估
          </button>
        </div>
      </div>
    );
  }

  const scoreColor = evaluation.score >= 85 ? '#22c55e' :
                     evaluation.score >= 75 ? '#6366f1' :
                     evaluation.score >= 60 ? '#f59e0b' : '#ef4444';

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <span style={styles.title}>AI 评估</span>
        <button style={styles.refreshBtn} onClick={() => sendEvaluate()}>刷新</button>
      </div>

      {/* 评分 */}
      <div style={styles.scoreSection}>
        <div style={{ ...styles.scoreCircle, borderColor: scoreColor }}>
          <span style={{ ...styles.scoreNum, color: scoreColor }}>{evaluation.score}</span>
          <span style={styles.scoreLabel}>分</span>
        </div>
        <div style={styles.scoreFeedback}>{evaluation.feedback}</div>
      </div>

      {/* 详细评价 */}
      <div style={styles.detailSection}>
        {evaluation.color_feedback && (
          <div style={styles.detailItem}>
            <span style={styles.detailLabel}>配色</span>
            <span style={styles.detailText}>{evaluation.color_feedback}</span>
          </div>
        )}
        {evaluation.composition_feedback && (
          <div style={styles.detailItem}>
            <span style={styles.detailLabel}>构图</span>
            <span style={styles.detailText}>{evaluation.composition_feedback}</span>
          </div>
        )}
      </div>

      {/* 修改建议 */}
      {evaluation.suggestions && evaluation.suggestions.length > 0 && (
        <div style={styles.suggestionSection}>
          <div style={styles.suggestionTitle}>修改建议</div>
          {evaluation.suggestions.map((s, i) => (
            <div
              key={i}
              style={styles.suggestionItem}
              onClick={() => sendAcceptSuggestion(i)}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = '#eef2ff';
                e.currentTarget.style.borderColor = '#6366f1';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = '#f9fafb';
                e.currentTarget.style.borderColor = '#e5e7eb';
              }}
            >
              <span style={styles.suggestionIcon}> </span>
              <span style={styles.suggestionText}>{s.text}</span>
            </div>
          ))}
          <div style={styles.suggestionActions}>
            <button
              style={styles.acceptBtn}
              onClick={() => sendAcceptSuggestion(0)}
            >
              ✓ 接受第一个
            </button>
            <button
              style={styles.rejectBtn}
              onClick={() => sendRejectSuggestion()}
            >
              ✗ 忽略
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  container: {
    padding: '12px 16px',
    borderBottom: '1px solid #e5e7eb',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '12px',
  },
  title: {
    fontSize: '12px',
    fontWeight: '600',
    color: '#6b7280',
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
  },
  refreshBtn: {
    padding: '2px 8px',
    fontSize: '10px',
    border: '1px solid #d1d5db',
    borderRadius: '4px',
    backgroundColor: '#fff',
    cursor: 'pointer',
    color: '#6b7280',
  },
  empty: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '8px',
    padding: '16px 0',
    color: '#9ca3af',
    fontSize: '12px',
  },
  emptyIcon: {
    fontSize: '24px',
  },
  evalBtn: {
    padding: '6px 16px',
    fontSize: '11px',
    border: '1px solid #6366f1',
    borderRadius: '6px',
    backgroundColor: '#fff',
    cursor: 'pointer',
    color: '#6366f1',
    fontWeight: '500',
  },
  scoreSection: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    marginBottom: '12px',
  },
  scoreCircle: {
    width: '52px',
    height: '52px',
    borderRadius: '50%',
    border: '3px solid',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
  },
  scoreNum: {
    fontSize: '18px',
    fontWeight: '700',
    lineHeight: 1,
  },
  scoreLabel: {
    fontSize: '9px',
    color: '#9ca3af',
  },
  scoreFeedback: {
    fontSize: '13px',
    color: '#374151',
    lineHeight: '1.4',
    flex: 1,
  },
  detailSection: {
    display: 'flex',
    flexDirection: 'column',
    gap: '6px',
    marginBottom: '12px',
  },
  detailItem: {
    display: 'flex',
    gap: '8px',
    fontSize: '11px',
  },
  detailLabel: {
    color: '#6366f1',
    fontWeight: '600',
    flexShrink: 0,
    minWidth: '28px',
  },
  detailText: {
    color: '#6b7280',
    lineHeight: '1.3',
  },
  suggestionSection: {
    borderTop: '1px solid #f3f4f6',
    paddingTop: '10px',
  },
  suggestionTitle: {
    fontSize: '11px',
    fontWeight: '600',
    color: '#6b7280',
    marginBottom: '8px',
  },
  suggestionItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    padding: '8px 10px',
    marginBottom: '4px',
    border: '1px solid #e5e7eb',
    borderRadius: '6px',
    backgroundColor: '#f9fafb',
    cursor: 'pointer',
    transition: 'all 0.15s',
  },
  suggestionIcon: {
    fontSize: '12px',
    flexShrink: 0,
  },
  suggestionText: {
    fontSize: '12px',
    color: '#374151',
    lineHeight: '1.3',
  },
  suggestionActions: {
    display: 'flex',
    gap: '8px',
    marginTop: '8px',
  },
  acceptBtn: {
    flex: 1,
    padding: '6px 0',
    fontSize: '11px',
    border: '1px solid #22c55e',
    borderRadius: '6px',
    backgroundColor: '#f0fdf4',
    color: '#22c55e',
    cursor: 'pointer',
    fontWeight: '500',
  },
  rejectBtn: {
    flex: 1,
    padding: '6px 0',
    fontSize: '11px',
    border: '1px solid #d1d5db',
    borderRadius: '6px',
    backgroundColor: '#fff',
    color: '#6b7280',
    cursor: 'pointer',
  },
};

export default EvaluationPanel;
