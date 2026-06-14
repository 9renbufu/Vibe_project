/**
 * 状态面板 - 右侧面板
 * 显示画布记录、用户偏好、预设画廊
 */

import React from 'react';
import { useDrawingStore } from '../../store/drawingStore';
import { sendCommand, sendCreateRecord, sendSwitchRecord } from '../../store/wsManager';
import EvaluationPanel from './EvaluationPanel';

const StatusPanel: React.FC = () => {
  const {
    background, shapeCount, lastCommand, connected, isProcessing,
    preferences, records, activeRecordId, setIsProcessing,
  } = useDrawingStore();

  const presets = [
    { id: 'flow_field', name: '流场', icon: ' ', desc: 'Perlin noise 粒子流', cmd: '画一幅流场艺术' },
    { id: 'fractal_tree', name: '分形树', icon: ' ', desc: '递归 L-system', cmd: '画一棵分形树' },
    { id: 'watercolor', name: '水彩', icon: ' ', desc: '半透明叠层', cmd: '画一幅水彩画' },
    { id: 'mandala', name: '曼陀罗', icon: ' ', desc: '径向对称图案', cmd: '画一个曼陀罗' },
    { id: 'spirograph', name: '螺线', icon: ' ', desc: '数学外旋轮线', cmd: '画一个螺线' },
    { id: 'voronoi', name: '沃罗诺伊', icon: ' ', desc: '区域划分图案', cmd: '画一个沃罗诺伊图' },
    { id: 'sunset', name: '日落', icon: ' ', desc: '夕阳海景', cmd: '画一幅日落风景' },
    { id: 'starry_sky', name: '星空', icon: ' ', desc: '繁星点点', cmd: '画一幅星空' },
    { id: 'mountain', name: '山脉', icon: '⛰️', desc: '层峦叠嶂', cmd: '画一幅山脉风景' },
    { id: 'ocean', name: '海洋', icon: ' ', desc: '碧海蓝天', cmd: '画一幅海洋风景' },
    { id: 'forest', name: '森林', icon: ' ', desc: '郁郁葱葱', cmd: '画一幅森林风景' },
    { id: 'snow', name: '雪景', icon: '❄️', desc: '银装素裹', cmd: '画一幅雪景' },
  ];

  // 点击预设：创建新记录 → 发送绘图命令
  const handlePresetClick = (cmd: string, title: string) => {
    sendCreateRecord(title);
    // 延迟一下等记录创建完成再发送命令
    setTimeout(() => {
      if (sendCommand(cmd)) {
        setIsProcessing(true);
      }
    }, 100);
  };

  // 点击已有记录：切换到该记录
  const handleRecordClick = (recordId: string) => {
    if (recordId !== activeRecordId) {
      sendSwitchRecord(recordId);
    }
  };

  // 新建空白画布
  const handleNewCanvas = () => {
    sendCreateRecord();
  };

  const handleExport = () => {
    const canvas = document.querySelector('canvas');
    if (canvas) {
      const link = document.createElement('a');
      link.download = 'voice-drawing.png';
      link.href = canvas.toDataURL('image/png');
      link.click();
    }
  };

  const formatTime = (iso: string) => {
    try {
      return new Date(iso).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
    } catch {
      return '';
    }
  };

  return (
    <div style={styles.container}>
      {/* Header */}
      <div style={styles.header}>
        <span style={styles.title}>状态</span>
        <div style={{ ...styles.statusBadge, backgroundColor: connected ? '#dcfce7' : '#fef2f2', color: connected ? '#166534' : '#991b1b' }}>
          {connected ? '已连接' : '未连接'}
        </div>
      </div>

      {/* Canvas Info */}
      <div style={styles.section}>
        <div style={styles.sectionTitle}>当前画布</div>
        <div style={styles.infoRow}>
          <span style={styles.infoLabel}>尺寸</span>
          <span style={styles.infoValue}>1200 × 800</span>
        </div>
        <div style={styles.infoRow}>
          <span style={styles.infoLabel}>图形数</span>
          <span style={styles.infoValue}>{shapeCount}</span>
        </div>
        <div style={styles.infoRow}>
          <span style={styles.infoLabel}>背景</span>
          <div style={{ ...styles.colorSwatch, backgroundColor: background }} />
        </div>
        {activeRecordId && (
          <div style={styles.infoRow}>
            <span style={styles.infoLabel}>记录ID</span>
            <span style={styles.infoValue}>{activeRecordId}</span>
          </div>
        )}
      </div>

      {/* AI 评估 */}
      <EvaluationPanel />

      {/* Current Status */}
      {lastCommand && (
        <div style={styles.section}>
          <div style={styles.sectionTitle}>最近操作</div>
          <div style={styles.statusText}>{lastCommand}</div>
        </div>
      )}

      {isProcessing && (
        <div style={styles.section}>
          <div style={styles.processingBadge}>⏳ 正在生成...</div>
        </div>
      )}

      {/* User Preferences */}
      {preferences && preferences.total_commands > 0 && (
        <div style={styles.section}>
          <div style={styles.sectionTitle}>用户偏好</div>
          <div style={styles.infoRow}>
            <span style={styles.infoLabel}>总指令数</span>
            <span style={styles.infoValue}>{preferences.total_commands}</span>
          </div>
          {preferences.favorite_colors.length > 0 && (
            <div style={styles.prefGroup}>
              <span style={styles.prefLabel}>常用颜色</span>
              <div style={styles.colorChips}>
                {preferences.favorite_colors.map((c, i) => (
                  <div key={i} style={{ ...styles.colorChip, backgroundColor: c }} title={c} />
                ))}
              </div>
            </div>
          )}
          {preferences.favorite_styles.length > 0 && (
            <div style={styles.prefGroup}>
              <span style={styles.prefLabel}>常用风格</span>
              <div style={styles.tagChips}>
                {preferences.favorite_styles.map((s, i) => (
                  <span key={i} style={styles.tagChip}>{s}</span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Canvas Records */}
      <div style={{ ...styles.section, flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
        <div style={styles.sectionHeader}>
          <div style={styles.sectionTitle}>画布记录</div>
          <button style={styles.newCanvasBtn} onClick={handleNewCanvas}>
            + 新建
          </button>
        </div>
        <div style={styles.recordsList}>
          {records.length === 0 && (
            <div style={styles.emptyHint}>点击预设或新建画布开始创作</div>
          )}
          {records.slice().reverse().map((r) => (
            <div
              key={r.id}
              style={{
                ...styles.recordItem,
                ...(r.id === activeRecordId ? styles.recordItemActive : {}),
              }}
              onClick={() => handleRecordClick(r.id)}
              onMouseEnter={(e) => {
                if (r.id !== activeRecordId) {
                  (e.currentTarget as HTMLDivElement).style.backgroundColor = '#f3f4f6';
                }
                (e.currentTarget as HTMLDivElement).style.cursor = 'pointer';
              }}
              onMouseLeave={(e) => {
                if (r.id !== activeRecordId) {
                  (e.currentTarget as HTMLDivElement).style.backgroundColor = 'transparent';
                }
              }}
            >
              <div style={styles.recordHeader}>
                <span style={styles.recordTitle}>{r.title}</span>
                {r.id === activeRecordId && <span style={styles.activeTag}>当前</span>}
              </div>
              <div style={styles.recordMeta}>
                <span style={styles.recordShapeCount}>{r.shape_count} 图形</span>
                <span style={styles.recordTime}>{formatTime(r.created_at)}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Presets Gallery */}
      <div style={{ ...styles.section, maxHeight: '240px', overflow: 'auto' }}>
        <div style={styles.sectionTitle}>预设画廊</div>
        <div style={styles.presetsGrid}>
          {presets.map((p) => (
            <div
              key={p.id}
              style={styles.presetCard}
              onClick={() => handlePresetClick(p.cmd, p.name)}
              onMouseEnter={(e) => {
                (e.currentTarget as HTMLDivElement).style.borderColor = '#6366f1';
                (e.currentTarget as HTMLDivElement).style.backgroundColor = '#eef2ff';
                (e.currentTarget as HTMLDivElement).style.cursor = 'pointer';
              }}
              onMouseLeave={(e) => {
                (e.currentTarget as HTMLDivElement).style.borderColor = '#e5e7eb';
                (e.currentTarget as HTMLDivElement).style.backgroundColor = '#f9fafb';
              }}
            >
              <div style={styles.presetIcon}>{p.icon}</div>
              <div style={styles.presetName}>{p.name}</div>
              <div style={styles.presetDesc}>{p.desc}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Export */}
      <div style={{ ...styles.section, flexShrink: 0 }}>
        <button style={styles.exportBtn} onClick={handleExport}>
           导出 PNG
        </button>
      </div>
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: 'flex', flexDirection: 'column', height: '100vh',
    backgroundColor: '#ffffff', borderLeft: '1px solid #e5e7eb',
    overflow: 'hidden',
  },
  header: {
    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
    padding: '12px 16px', borderBottom: '1px solid #e5e7eb', backgroundColor: '#fafafa',
  },
  title: { fontSize: '14px', fontWeight: '600', color: '#111827' },
  statusBadge: {
    padding: '2px 8px', fontSize: '11px', borderRadius: '10px', fontWeight: '500',
  },
  section: { padding: '12px 16px', borderBottom: '1px solid #e5e7eb' },
  sectionHeader: {
    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
    marginBottom: '8px',
  },
  sectionTitle: {
    fontSize: '12px', fontWeight: '600', color: '#6b7280', marginBottom: '8px',
    textTransform: 'uppercase', letterSpacing: '0.5px',
  },
  infoRow: {
    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
    padding: '4px 0',
  },
  infoLabel: { fontSize: '12px', color: '#6b7280' },
  infoValue: { fontSize: '12px', color: '#111827', fontWeight: '500' },
  colorSwatch: {
    width: '20px', height: '20px', borderRadius: '4px', border: '1px solid #d1d5db',
  },
  statusText: { fontSize: '12px', color: '#22c55e', fontWeight: '500' },
  processingBadge: {
    fontSize: '12px', color: '#6366f1', fontWeight: '500',
    padding: '6px 12px', backgroundColor: '#eef2ff', borderRadius: '6px', textAlign: 'center',
  },
  prefGroup: { marginTop: '8px' },
  prefLabel: { fontSize: '11px', color: '#9ca3af', marginBottom: '4px', display: 'block' },
  colorChips: { display: 'flex', gap: '4px', flexWrap: 'wrap' },
  colorChip: { width: '18px', height: '18px', borderRadius: '4px', border: '1px solid #d1d5db' },
  tagChips: { display: 'flex', gap: '4px', flexWrap: 'wrap' },
  tagChip: {
    padding: '2px 8px', fontSize: '10px', backgroundColor: '#f3f4f6',
    borderRadius: '10px', color: '#4b5563',
  },
  newCanvasBtn: {
    padding: '4px 10px', fontSize: '11px', fontWeight: '500',
    border: '1px solid #6366f1', borderRadius: '6px',
    backgroundColor: '#fff', color: '#6366f1', cursor: 'pointer',
  },
  recordsList: { overflowY: 'auto', flex: 1 },
  emptyHint: { fontSize: '12px', color: '#9ca3af', textAlign: 'center', padding: '16px 0' },
  recordItem: {
    padding: '8px 10px', borderBottom: '1px solid #f3f4f6',
    borderRadius: '6px', marginBottom: '4px',
  },
  recordItemActive: {
    backgroundColor: '#eef2ff',
    border: '1px solid #c7d2fe',
    borderBottom: '1px solid #c7d2fe',
  },
  recordHeader: {
    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
    marginBottom: '2px',
  },
  recordTitle: { fontSize: '13px', fontWeight: '500', color: '#111827' },
  activeTag: {
    fontSize: '10px', color: '#6366f1', backgroundColor: '#e0e7ff',
    padding: '1px 6px', borderRadius: '8px', fontWeight: '500',
  },
  recordMeta: {
    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
  },
  recordShapeCount: { fontSize: '11px', color: '#6b7280' },
  recordTime: { fontSize: '10px', color: '#9ca3af' },
  presetsGrid: {
    display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '8px',
    overflowY: 'auto', maxHeight: '100%',
  },
  presetCard: {
    padding: '10px 8px', border: '1px solid #e5e7eb', borderRadius: '8px',
    backgroundColor: '#f9fafb', textAlign: 'center',
  },
  presetIcon: { fontSize: '24px', marginBottom: '4px' },
  presetName: { fontSize: '12px', fontWeight: '600', color: '#111827', marginBottom: '2px' },
  presetDesc: { fontSize: '10px', color: '#9ca3af' },
  exportBtn: {
    width: '100%', padding: '10px', fontSize: '13px', fontWeight: '500',
    border: '1px solid #d1d5db', borderRadius: '8px', backgroundColor: '#fff',
    cursor: 'pointer', color: '#374151',
  },
};

export default StatusPanel;
