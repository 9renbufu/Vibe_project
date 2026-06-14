/**
 * 程序化绘图画布
 * 支持流式动画渲染：逐步显示绘图过程，模拟真实绘画效果
 */

import React, { useRef, useEffect, useCallback, useState } from 'react';
import { useDrawingStore, DrawingInstruction } from '../../store/drawingStore';

const PAINT_DELAY = 60;  // 每个图形之间的延迟(ms)，模拟真人绘画节奏
const FADE_STEPS = 4;    // 淡入步数
const PATH_BATCH = 2;    // 路径动画每帧画的点数

const ProceduralCanvas: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animFrameRef = useRef<number>(0);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const pendingRef = useRef<DrawingInstruction[]>([]);
  const totalRef = useRef<number>(0);
  const [isPainting, setIsPainting] = useState(false);
  const [paintProgress, setPaintProgress] = useState(0);
  const { instructions, background } = useDrawingStore();

  // 渲染单条指令（带淡入效果）
  const renderInstruction = useCallback((ctx: CanvasRenderingContext2D, inst: DrawingInstruction, alpha: number = 1) => {
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
      ctx.globalAlpha = alpha;
      for (const shape of params.shapes) {
        renderShape(ctx, shape.type, shape.params);
      }
      ctx.globalAlpha = 1;
      return;
    }

    if (action === 'create' && shape_type) {
      ctx.globalAlpha = alpha;
      renderShape(ctx, shape_type, params);
      ctx.globalAlpha = 1;
    }
  }, []);

  // 将 batch 指令展开为单个 create 指令
  const expandBatch = useCallback((inst: DrawingInstruction): DrawingInstruction[] => {
    if (inst.action === 'batch' && inst.params.shapes) {
      return inst.params.shapes.map((shape: any) => ({
        action: 'create',
        shape_type: shape.type,
        params: shape.params,
        layer: inst.layer,
      }));
    }
    return [inst];
  }, []);

  // 流式动画渲染 - 逐个绘制，模拟画笔效果
  const paintNext = useCallback((ctx: CanvasRenderingContext2D) => {
    if (pendingRef.current.length === 0) {
      setIsPainting(false);
      setPaintProgress(0);
      return;
    }

    // 更新进度
    const painted = totalRef.current - pendingRef.current.length;
    setPaintProgress(Math.round((painted / totalRef.current) * 100));

    const inst = pendingRef.current.shift()!;

    // batch 指令展开为单个形状，逐个动画
    const shapes = expandBatch(inst);
    if (shapes.length > 1) {
      // 将展开的形状插入到待处理队列前面
      pendingRef.current = [...shapes, ...pendingRef.current];
      paintNext(ctx);
      return;
    }

    const single = shapes[0];

    // 对于路径类图形，使用逐点动画
    if (single.action === 'create' && single.shape_type === 'path' && single.params.points?.length > 10) {
      animatePath(ctx, single, () => {
        timerRef.current = setTimeout(() => paintNext(ctx), PAINT_DELAY);
      });
    } else {
      // 普通图形：淡入效果
      animateFadeIn(ctx, single, () => {
        timerRef.current = setTimeout(() => paintNext(ctx), PAINT_DELAY);
      });
    }
  }, [expandBatch]);

  // 淡入动画
  const animateFadeIn = useCallback((ctx: CanvasRenderingContext2D, inst: DrawingInstruction, onDone: () => void) => {
    let step = 0;
    const animate = () => {
      step++;
      const alpha = Math.min(step / FADE_STEPS, 1);
      renderInstruction(ctx, inst, alpha);
      if (step < FADE_STEPS) {
        animFrameRef.current = requestAnimationFrame(animate);
      } else {
        onDone();
      }
    };
    animFrameRef.current = requestAnimationFrame(animate);
  }, [renderInstruction]);

  // 路径逐点动画（用于流场线条等）
  const animatePath = useCallback((ctx: CanvasRenderingContext2D, inst: DrawingInstruction, onDone: () => void) => {
    const { params } = inst;
    const points = params.points;
    if (!points || points.length < 2) {
      renderInstruction(ctx, inst);
      onDone();
      return;
    }

    ctx.save();
    if (params.stroke && params.stroke !== 'transparent') {
      ctx.strokeStyle = params.stroke;
    }
    if (params.strokeWidth) {
      ctx.lineWidth = params.strokeWidth;
    }
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';

    let idx = 1;

    const drawBatch = () => {
      ctx.beginPath();
      ctx.moveTo(points[idx - 1].x, points[idx - 1].y);
      const end = Math.min(idx + PATH_BATCH, points.length);
      for (let i = idx; i < end; i++) {
        ctx.lineTo(points[i].x, points[i].y);
      }
      ctx.stroke();
      idx = end;

      if (idx < points.length) {
        animFrameRef.current = requestAnimationFrame(drawBatch);
      } else {
        ctx.restore();
        onDone();
      }
    };

    // 先画第一个点
    ctx.beginPath();
    ctx.moveTo(points[0].x, points[0].y);
    animFrameRef.current = requestAnimationFrame(drawBatch);
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // 取消之前的动画
    if (animFrameRef.current) {
      cancelAnimationFrame(animFrameRef.current);
    }
    if (timerRef.current) {
      clearTimeout(timerRef.current);
    }
    pendingRef.current = [];

    // 检查是否是增量更新
    const isIncremental = instructions.length > 0 && instructions[0].action !== 'clear';

    if (!isIncremental) {
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

    // 流式渲染绘制指令
    if (drawInstructions.length > 5) {
      // 指令多时用流式动画
      setIsPainting(true);
      pendingRef.current = drawInstructions;
      totalRef.current = drawInstructions.length;
      setPaintProgress(0);
      paintNext(ctx);
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
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
    };
  }, [instructions, background, renderInstruction, paintNext]);

  return (
    <div style={styles.wrapper}>
      <canvas
        ref={canvasRef}
        width={1200}
        height={800}
        style={styles.canvas}
      />
      {isPainting && (
        <div style={styles.paintingIndicator}>
          <div style={styles.paintingDot} />
          绘画中... {paintProgress > 0 ? `${paintProgress}%` : ''}
        </div>
      )}
    </div>
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
  ctx.lineCap = 'round';
  ctx.lineJoin = 'round';

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
  wrapper: {
    position: 'relative',
    width: '100%',
    height: '100%',
  },
  canvas: {
    width: '100%',
    height: '100%',
    objectFit: 'contain',
    borderRadius: '8px',
    boxShadow: '0 2px 12px rgba(0,0,0,0.08)',
  },
  paintingIndicator: {
    position: 'absolute',
    top: '12px',
    right: '12px',
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    padding: '6px 12px',
    backgroundColor: 'rgba(99, 102, 241, 0.9)',
    color: '#fff',
    fontSize: '12px',
    fontWeight: '500',
    borderRadius: '16px',
    boxShadow: '0 2px 8px rgba(99, 102, 241, 0.3)',
  },
  paintingDot: {
    width: '8px',
    height: '8px',
    borderRadius: '50%',
    backgroundColor: '#fff',
    animation: 'pulse 1s ease-in-out infinite',
  },
};

export default ProceduralCanvas;
