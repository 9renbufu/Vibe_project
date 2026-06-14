/**
 * 程序化绘图画布
 * 渲染后端发来的绘图指令
 */

import React, { useRef, useEffect, useCallback } from 'react';
import { useDrawingStore, DrawingInstruction } from '../../store/drawingStore';

const ProceduralCanvas: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const { instructions, background } = useDrawingStore();

  const renderInstruction = useCallback((ctx: CanvasRenderingContext2D, inst: DrawingInstruction) => {
    const { action, shape_type, params } = inst;

    if (action === 'clear') {
      ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
      return;
    }

    if (action === 'background') {
      ctx.fillStyle = params.color || 'rgb(255,255,255)';
      ctx.fillRect(0, 0, ctx.canvas.width, ctx.canvas.height);
      return;
    }

    if (action === 'batch' && params.shapes) {
      for (const shape of params.shapes) {
        renderShape(ctx, shape.type, shape.params);
      }
      return;
    }

    if (action === 'create' && shape_type) {
      renderShape(ctx, shape_type, params);
    }
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // 清空并绘制背景
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = background;
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // 按 layer 排序后渲染
    const sorted = [...instructions].sort((a, b) => (a.layer || 0) - (b.layer || 0));
    for (const inst of sorted) {
      renderInstruction(ctx, inst);
    }
  }, [instructions, background, renderInstruction]);

  return (
    <canvas
      ref={canvasRef}
      width={1200}
      height={800}
      style={styles.canvas}
    />
  );
};

function renderShape(ctx: CanvasRenderingContext2D, type: string, params: Record<string, any>) {
  ctx.save();

  // 设置样式
  if (params.fill && params.fill !== 'transparent') {
    ctx.fillStyle = params.fill;
  }
  if (params.stroke && params.stroke !== 'transparent') {
    ctx.strokeStyle = params.stroke;
  }
  if (params.strokeWidth) {
    ctx.lineWidth = params.strokeWidth;
  }

  switch (type) {
    case 'circle':
      ctx.beginPath();
      ctx.arc(params.cx, params.cy, params.radius, 0, Math.PI * 2);
      if (params.fill && params.fill !== 'transparent') ctx.fill();
      if (params.stroke && params.stroke !== 'transparent') ctx.stroke();
      break;

    case 'ellipse':
      ctx.beginPath();
      ctx.ellipse(params.cx, params.cy, params.radiusX, params.radiusY, 0, 0, Math.PI * 2);
      if (params.fill && params.fill !== 'transparent') ctx.fill();
      if (params.stroke && params.stroke !== 'transparent') ctx.stroke();
      break;

    case 'rect':
      if (params.radius) {
        roundRect(ctx, params.x, params.y, params.width, params.height, params.radius);
        if (params.fill && params.fill !== 'transparent') ctx.fill();
        if (params.stroke && params.stroke !== 'transparent') ctx.stroke();
      } else {
        if (params.fill && params.fill !== 'transparent') {
          ctx.fillRect(params.x, params.y, params.width, params.height);
        }
        if (params.stroke && params.stroke !== 'transparent') {
          ctx.strokeRect(params.x, params.y, params.width, params.height);
        }
      }
      break;

    case 'line':
      ctx.beginPath();
      ctx.moveTo(params.x1, params.y1);
      ctx.lineTo(params.x2, params.y2);
      ctx.stroke();
      break;

    case 'polygon':
      if (params.points && params.points.length > 0) {
        ctx.beginPath();
        ctx.moveTo(params.points[0].x, params.points[0].y);
        for (let i = 1; i < params.points.length; i++) {
          ctx.lineTo(params.points[i].x, params.points[i].y);
        }
        ctx.closePath();
        if (params.fill && params.fill !== 'transparent') ctx.fill();
        if (params.stroke && params.stroke !== 'transparent') ctx.stroke();
      }
      break;

    case 'path':
      if (params.points && params.points.length > 1) {
        ctx.beginPath();
        ctx.moveTo(params.points[0].x, params.points[0].y);
        for (let i = 1; i < params.points.length; i++) {
          ctx.lineTo(params.points[i].x, params.points[i].y);
        }
        if (params.stroke && params.stroke !== 'transparent') ctx.stroke();
      }
      break;
  }

  ctx.restore();
}

function roundRect(ctx: CanvasRenderingContext2D, x: number, y: number, w: number, h: number, r: number) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.lineTo(x + w - r, y);
  ctx.quadraticCurveTo(x + w, y, x + w, y + r);
  ctx.lineTo(x + w, y + h - r);
  ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
  ctx.lineTo(x + r, y + h);
  ctx.quadraticCurveTo(x, y + h, x, y + h - r);
  ctx.lineTo(x, y + r);
  ctx.quadraticCurveTo(x, y, x + r, y);
  ctx.closePath();
}

const styles: Record<string, React.CSSProperties> = {
  canvas: {
    width: '100%',
    height: '100%',
    objectFit: 'contain',
    borderRadius: '8px',
    boxShadow: '0 2px 12px rgba(0,0,0,0.08)',
  },
};

export default ProceduralCanvas;
