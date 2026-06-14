/**
 * 程序化绘图画布
 * 支持动画渲染：逐步显示绘图过程
 */

import React, { useRef, useEffect, useCallback } from 'react';
import { useDrawingStore, DrawingInstruction } from '../../store/drawingStore';

const BATCH_SIZE = 8; // 每帧渲染的指令数

const ProceduralCanvas: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animFrameRef = useRef<number>(0);
  const pendingRef = useRef<DrawingInstruction[]>([]);
  const { instructions, background } = useDrawingStore();

  // 渲染单条指令
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

  // 动画渲染循环
  const animate = useCallback((ctx: CanvasRenderingContext2D) => {
    const batch = pendingRef.current.splice(0, BATCH_SIZE);
    for (const inst of batch) {
      renderInstruction(ctx, inst);
    }
    if (pendingRef.current.length > 0) {
      animFrameRef.current = requestAnimationFrame(() => animate(ctx));
    }
  }, [renderInstruction]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // 取消之前的动画
    if (animFrameRef.current) {
      cancelAnimationFrame(animFrameRef.current);
    }

    // 检查是否是增量更新（只有新增指令）
    const isIncremental = instructions.length > 0 && instructions[0].action !== 'clear';

    if (!isIncremental) {
      // 全量重绘
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.fillStyle = background;
      ctx.fillRect(0, 0, canvas.width, canvas.height);
    }

    // 按 layer 排序
    const sorted = [...instructions].sort((a, b) => (a.layer || 0) - (b.layer || 0));

    // 分离背景指令和绘制指令
    const bgInstructions = sorted.filter(i => i.action === 'background' || i.action === 'clear');
    const drawInstructions = sorted.filter(i => i.action === 'create' || i.action === 'batch');

    // 立即渲染背景
    for (const inst of bgInstructions) {
      renderInstruction(ctx, inst);
    }

    // 动画渲染绘制指令
    if (drawInstructions.length > 20) {
      // 指令多时用动画
      pendingRef.current = drawInstructions;
      animate(ctx);
    } else {
      // 指令少时直接渲染
      for (const inst of drawInstructions) {
        renderInstruction(ctx, inst);
      }
    }

    return () => {
      if (animFrameRef.current) {
        cancelAnimationFrame(animFrameRef.current);
      }
    };
  }, [instructions, background, renderInstruction, animate]);

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
