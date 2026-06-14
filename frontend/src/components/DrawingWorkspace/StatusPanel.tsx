/**
 * 状态面板 - 右侧面板
 * 显示画布信息、用户偏好、绘图历史
 */

import React from 'react';
import { useDrawingStore } from '../../store/drawingStore';

const StatusPanel: React.FC = () => {
  const {
    background, shapeCount, lastCommand, connected, isProcessing,
    preferences, drawingHistory,
  } = useDrawingStore();

  const presets = [
    { id: 'flow_field', name: '流场', icon: ' ', desc: 'Perlin noise 粒子流' },
    { id: 'fractal_tree', name: '分形树', icon: ' ', desc: '递归 L-system' },
    { id: 'watercolor', name: '水彩', icon: ' ', desc: '半透明叠层' },
    { id: 'mandala', name: '曼陀罗', icon: ' ', desc: '径向对称图案' },
    { id: 'spirograph', name: '螺线', icon: ' ', desc: '数学外旋轮线' },
    { id: 'voronoi', name: '沃罗诺伊', icon: ' ', desc: '区域划分图案' },
    { id: 'sunset', name: '日落', icon: ' ', desc: '夕阳海景' },
    { id: 'starry_sky', name: '星空', icon: ' ', desc: '繁星点点' },
    { id: 'mountain', name: '山脉', icon: '⛰️', desc: '层峦叠嶂' },
    { id: 'ocean', name: '海洋', icon: ' ', desc: '碧海蓝天' },
    { id: 'forest', name: '森林', icon: ' ', desc: '郁郁葱葱' },
    { id: 'snow', name: '雪景', icon: '❄️', desc: '银装素裹' },
  ];

  const handleExport = () => {
    const canvas = document.querySelector('canvas');
    if (canvas) {
      const link = document.createElement('a');
      link.download = 'voice-drawing.png';
      link.href = canvas.toDataURL('image/png');
      link.click();
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
        <div style={styles.sectionTitle}>画布信息</div>
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
      </div>

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
      {preferences && (
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
          {preferences.favorite_shapes.length > 0 && (
            <div style={styles.prefGroup}>
              <span style={styles.prefLabel}>常用形状</span>
              <div style={styles.tagChips}>
                {preferences.favorite_shapes.map((s, i) => (
                  <span key={i} style={styles.tagChip}>{s}</span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Drawing History */}
      {drawingHistory.length > 0 && (
        <div style={{ ...styles.section, flex: 1, overflow: 'hidden' }}>
          <div style={styles.sectionTitle}>绘图历史</div>
          <div style={styles.historyList}>
            {drawingHistory.slice().reverse().map((h, i) => (
              <div key={i} style={styles.historyItem}>
                <div style={styles.historyCmd}>{h.command}</div>
                <div style={styles.historyMeta}>
                  <span style={styles.historyResponse}>{h.response}</span>
                  <span style={styles.historyCount}>{h.shape_count} 图形</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Presets Gallery */}
      <div style={{ ...styles.section, flex: drawingHistory.length > 0 ? undefined : 1, overflow: 'hidden' }}>
        <div style={styles.sectionTitle}>预设画廊</div>
        <div style={styles.presetsGrid}>
          {presets.map((p) => (
            <div key={p.id} style={styles.presetCard}>
              <div style={styles.presetIcon}>{p.icon}</div>
              <div style={styles.presetName}>{p.name}</div>
              <div style={styles.presetDesc}>{p.desc}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Export */}
      <div style={styles.section}>
        <button style={styles.exportBtn} onClick={handleExport}>
           导出 PNG
        </button>
      </div>
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: 'flex', flexDirection: 'column', height: '100%',
    backgroundColor: '#ffffff', borderLeft: '1px solid #e5e7eb',
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
  historyList: { overflowY: 'auto', maxHeight: '200px' },
  historyItem: { padding: '6px 0', borderBottom: '1px solid #f3f4f6' },
  historyCmd: { fontSize: '12px', color: '#111827', marginBottom: '2px' },
  historyMeta: { display: 'flex', justifyContent: 'space-between', alignItems: 'center' },
  historyResponse: { fontSize: '10px', color: '#22c55e' },
  historyCount: { fontSize: '10px', color: '#9ca3af' },
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
