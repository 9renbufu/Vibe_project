import React, { useRef, useEffect } from 'react';
import { SceneState, Shape } from '../types';

interface EnhancedCanvasProps {
  scene: SceneState;
}

export const EnhancedCanvas: React.FC<EnhancedCanvasProps> = ({ scene }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // 清空画布
    ctx.fillStyle = `rgb(${scene.background.r}, ${scene.background.g}, ${scene.background.b})`;
    ctx.fillRect(0, 0, scene.width, scene.height);

    // 绘制网格背景（可选）
    drawGrid(ctx, scene.width, scene.height);

    // 按 zIndex 排序并绘制
    const sortedShapes = [...scene.shapes].sort((a, b) => a.zIndex - b.zIndex);
    sortedShapes.forEach(shape => drawShape(ctx, shape));
  }, [scene]);

  return (
    <canvas
      ref={canvasRef}
      width={scene.width}
      height={scene.height}
      style={{
        border: '2px solid #333',
        borderRadius: '8px',
        maxWidth: '100%',
        height: 'auto',
        boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
      }}
    />
  );
};

function drawGrid(ctx: CanvasRenderingContext2D, width: number, height: number) {
  ctx.strokeStyle = 'rgba(0,0,0,0.05)';
  ctx.lineWidth = 1;
  const gridSize = 20;

  for (let x = 0; x <= width; x += gridSize) {
    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x, height);
    ctx.stroke();
  }

  for (let y = 0; y <= height; y += gridSize) {
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(width, y);
    ctx.stroke();
  }
}

function drawShape(ctx: CanvasRenderingContext2D, shape: Shape) {
  ctx.save();

  const { r, g, b, a = 1 } = shape.color;
  const colorStr = `rgba(${r}, ${g}, ${b}, ${a})`;

  ctx.translate(shape.position.x, shape.position.y);
  ctx.rotate((shape.rotation * Math.PI) / 180);
  ctx.scale(shape.scale, shape.scale);

  // 添加阴影效果
  ctx.shadowColor = 'rgba(0,0,0,0.2)';
  ctx.shadowBlur = 4;
  ctx.shadowOffsetX = 2;
  ctx.shadowOffsetY = 2;

  switch (shape.type) {
    case 'circle':
      drawCircle(ctx, shape, colorStr);
      break;
    case 'ellipse':
      drawEllipse(ctx, shape, colorStr);
      break;
    case 'rectangle':
      drawRectangle(ctx, shape, colorStr);
      break;
    case 'triangle':
      drawTriangle(ctx, shape, colorStr);
      break;
    case 'line':
      drawLine(ctx, shape, colorStr);
      break;
    case 'text':
      drawText(ctx, shape, colorStr);
      break;
    case 'polygon':
      drawPolygon(ctx, shape, colorStr);
      break;
    case 'path':
      drawPath(ctx, shape, colorStr);
      break;
  }

  ctx.restore();
}

function drawCircle(ctx: CanvasRenderingContext2D, shape: Shape, color: string) {
  const radius = shape.radius || Math.min(shape.width || 50, shape.height || 50) / 2;

  // 渐变效果
  const gradient = ctx.createRadialGradient(0, 0, 0, 0, 0, radius);
  gradient.addColorStop(0, lightenColor(color, 30));
  gradient.addColorStop(1, color);

  ctx.beginPath();
  ctx.arc(0, 0, radius, 0, Math.PI * 2);

  if (shape.fill) {
    ctx.fillStyle = gradient;
    ctx.fill();
  } else {
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.stroke();
  }
}

function drawEllipse(ctx: CanvasRenderingContext2D, shape: Shape, color: string) {
  const rx = (shape.width || 100) / 2;
  const ry = (shape.height || 60) / 2;

  ctx.beginPath();
  ctx.ellipse(0, 0, rx, ry, 0, 0, Math.PI * 2);

  if (shape.fill) {
    ctx.fillStyle = color;
    ctx.fill();
  } else {
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.stroke();
  }
}

function drawRectangle(ctx: CanvasRenderingContext2D, shape: Shape, color: string) {
  const width = shape.width || 100;
  const height = shape.height || 100;
  const radius = Math.min(10, width / 4, height / 4);

  // 圆角矩形
  ctx.beginPath();
  ctx.roundRect(-width / 2, -height / 2, width, height, radius);

  if (shape.fill) {
    // 渐变效果
    const gradient = ctx.createLinearGradient(0, -height / 2, 0, height / 2);
    gradient.addColorStop(0, lightenColor(color, 20));
    gradient.addColorStop(1, color);
    ctx.fillStyle = gradient;
    ctx.fill();
  } else {
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.stroke();
  }
}

function drawTriangle(ctx: CanvasRenderingContext2D, shape: Shape, color: string) {
  const width = shape.width || 100;
  const height = shape.height || 100;

  ctx.beginPath();
  ctx.moveTo(0, -height / 2);
  ctx.lineTo(width / 2, height / 2);
  ctx.lineTo(-width / 2, height / 2);
  ctx.closePath();

  if (shape.fill) {
    ctx.fillStyle = color;
    ctx.fill();
  } else {
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.stroke();
  }
}

function drawLine(ctx: CanvasRenderingContext2D, shape: Shape, color: string) {
  const width = shape.width || 100;

  ctx.beginPath();
  ctx.moveTo(-width / 2, 0);
  ctx.lineTo(width / 2, 0);
  ctx.strokeStyle = color;
  ctx.lineWidth = 2;
  ctx.stroke();
}

function drawText(ctx: CanvasRenderingContext2D, shape: Shape, color: string) {
  const fontSize = shape.height || 24;
  ctx.font = `bold ${fontSize}px "Microsoft YaHei", Arial, sans-serif`;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';

  // 文字阴影
  ctx.shadowColor = 'rgba(0,0,0,0.3)';
  ctx.shadowBlur = 3;

  if (shape.fill) {
    ctx.fillStyle = color;
    ctx.fillText(shape.text || '', 0, 0);
  } else {
    ctx.strokeStyle = color;
    ctx.lineWidth = 1;
    ctx.strokeText(shape.text || '', 0, 0);
  }
}

function drawPolygon(ctx: CanvasRenderingContext2D, shape: Shape, color: string) {
  if (!shape.points || shape.points.length < 3) return;

  ctx.beginPath();
  ctx.moveTo(shape.points[0].x, shape.points[0].y);
  shape.points.forEach((point, i) => {
    if (i > 0) ctx.lineTo(point.x, point.y);
  });
  ctx.closePath();

  if (shape.fill) {
    ctx.fillStyle = color;
    ctx.fill();
  } else {
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.stroke();
  }
}

function drawPath(ctx: CanvasRenderingContext2D, shape: Shape, color: string) {
  if (!shape.points || shape.points.length < 2) return;

  ctx.beginPath();
  ctx.moveTo(shape.points[0].x, shape.points[0].y);

  for (let i = 1; i < shape.points.length; i++) {
    const prev = shape.points[i - 1];
    const curr = shape.points[i];
    const cpx = (prev.x + curr.x) / 2;
    const cpy = (prev.y + curr.y) / 2;
    ctx.quadraticCurveTo(prev.x, prev.y, cpx, cpy);
  }

  ctx.strokeStyle = color;
  ctx.lineWidth = 2;
  ctx.stroke();
}

// 辅助函数：颜色变亮
function lightenColor(color: string, percent: number): string {
  const match = color.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/);
  if (!match) return color;

  const r = Math.min(255, parseInt(match[1]) + percent);
  const g = Math.min(255, parseInt(match[2]) + percent);
  const b = Math.min(255, parseInt(match[3]) + percent);

  return `rgb(${r}, ${g}, ${b})`;
}
