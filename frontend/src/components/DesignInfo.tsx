import React from 'react';

interface DesignElement {
  name: string;
  description: string;
  position: string;
  size: string;
}

interface DesignInfoProps {
  phase: string;
  style: string;
  elements: DesignElement[];
  colorPalette: string[];
  imageCount: number;
}

export const DesignInfo: React.FC<DesignInfoProps> = ({
  phase,
  style,
  elements,
  colorPalette,
  imageCount,
}) => {
  const phaseLabels: Record<string, string> = {
    idle: '等待指令',
    requirement: '需求收集',
    discussion: '设计讨论',
    planning: '方案规划',
    generating: '图像生成',
    reviewing: '方案评审',
    refining: '修改优化',
    exporting: '导出作品',
  };

  const styleLabels: Record<string, string> = {
    flat: '扁平化',
    gradient: '渐变风',
    neon: '霓虹风',
    minimal: '极简风',
    realistic: '写实风',
    cartoon: '卡通风',
    cyberpunk: '赛博朋克',
    watercolor: '水彩风',
  };

  return (
    <div style={styles.container}>
      <h3 style={styles.title}>设计信息</h3>

      <div style={styles.section}>
        <div style={styles.row}>
          <span style={styles.label}>当前阶段</span>
          <span style={styles.badge}>{phaseLabels[phase] || phase}</span>
        </div>
        <div style={styles.row}>
          <span style={styles.label}>设计风格</span>
          <span style={styles.badge}>{styleLabels[style] || style}</span>
        </div>
        <div style={styles.row}>
          <span style={styles.label}>生成次数</span>
          <span style={styles.badge}>{imageCount} 次</span>
        </div>
      </div>

      {colorPalette.length > 0 && (
        <div style={styles.section}>
          <span style={styles.sectionTitle}>配色方案</span>
          <div style={styles.colorPalette}>
            {colorPalette.map((color, index) => (
              <div
                key={index}
                style={{
                  ...styles.colorSwatch,
                  backgroundColor: color,
                }}
                title={color}
              />
            ))}
          </div>
        </div>
      )}

      {elements.length > 0 && (
        <div style={styles.section}>
          <span style={styles.sectionTitle}>设计元素 ({elements.length})</span>
          <div style={styles.elementsList}>
            {elements.map((elem, index) => (
              <div key={index} style={styles.element}>
                <span style={styles.elementName}>{elem.name}</span>
                <span style={styles.elementDesc}>{elem.description}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  container: {
    padding: '16px',
    backgroundColor: '#fff',
    borderRadius: '12px',
    border: '1px solid #e0e0e0',
  },
  title: {
    margin: '0 0 16px 0',
    fontSize: '14px',
    fontWeight: '600',
    color: '#333',
  },
  section: {
    marginBottom: '16px',
  },
  sectionTitle: {
    display: 'block',
    fontSize: '12px',
    color: '#666',
    marginBottom: '8px',
  },
  row: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '8px',
  },
  label: {
    fontSize: '12px',
    color: '#666',
  },
  badge: {
    fontSize: '12px',
    color: '#333',
    backgroundColor: '#e9ecef',
    padding: '2px 8px',
    borderRadius: '10px',
  },
  colorPalette: {
    display: 'flex',
    gap: '6px',
    flexWrap: 'wrap',
  },
  colorSwatch: {
    width: '28px',
    height: '28px',
    borderRadius: '6px',
    border: '2px solid #fff',
    boxShadow: '0 1px 3px rgba(0,0,0,0.2)',
  },
  elementsList: {
    maxHeight: '150px',
    overflowY: 'auto',
  },
  element: {
    padding: '8px',
    backgroundColor: '#f8f9fa',
    borderRadius: '6px',
    marginBottom: '6px',
  },
  elementName: {
    display: 'block',
    fontSize: '12px',
    fontWeight: '600',
    color: '#333',
    marginBottom: '2px',
  },
  elementDesc: {
    fontSize: '11px',
    color: '#666',
  },
};
