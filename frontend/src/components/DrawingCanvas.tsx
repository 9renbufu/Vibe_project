import React, { useRef, useEffect } from 'react';
import { SceneState, Shape } from '../types';

interface DrawingCanvasProps {
  scene: SceneState;
}

export const DrawingCanvas: React.FC<DrawingCanvasProps> = ({ scene }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.fillStyle = `rgb(${scene.background.r}, ${scene.background.g}, ${scene.background.b})`;
    ctx.fillRect(0, 0, scene.width, scene.height);

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
      }}
    />
  );
};

function drawShape(ctx: CanvasRenderingContext2D, shape: Shape) {
  ctx.save();

  const { r, g, b, a = 1 } = shape.color;
  const colorStr = `rgba(${r}, ${g}, ${b}, ${a})`;

  if (shape.fill) {
    ctx.fillStyle = colorStr;
  } else {
    ctx.strokeStyle = colorStr;
    ctx.lineWidth = 2;
  }

  ctx.translate(shape.position.x, shape.position.y);
  ctx.rotate((shape.rotation * Math.PI) / 180);
  ctx.scale(shape.scale, shape.scale);

  switch (shape.type) {
    case 'circle':
      drawCircle(ctx, shape);
      break;
    case 'rectangle':
      drawRectangle(ctx, shape);
      break;
    case 'triangle':
      drawTriangle(ctx, shape);
      break;
    case 'line':
      drawLine(ctx, shape);
      break;
    case 'text':
      drawText(ctx, shape);
      break;
    case 'polygon':
      drawPolygon(ctx, shape);
      break;
    case 'path':
      drawPath(ctx, shape);
      break;
  }

  ctx.restore();
}

function drawCircle(ctx: CanvasRenderingContext2D, shape: Shape) {
  const radius = shape.radius || Math.min(shape.width || 50, shape.height || 50) / 2;
  ctx.beginPath();
  ctx.arc(0, 0, radius, 0, Math.PI * 2);
  shape.fill ? ctx.fill() : ctx.stroke();
}

function drawRectangle(ctx: CanvasRenderingContext2D, shape: Shape) {
  const width = shape.width || 100;
  const height = shape.height || 100;
  if (shape.fill) {
    ctx.fillRect(-width / 2, -height / 2, width, height);
  } else {
    ctx.strokeRect(-width / 2, -height / 2, width, height);
  }
}

function drawTriangle(ctx: CanvasRenderingContext2D, shape: Shape) {
  const width = shape.width || 100;
  const height = shape.height || 100;
  ctx.beginPath();
  ctx.moveTo(0, -height / 2);
  ctx.lineTo(width / 2, height / 2);
  ctx.lineTo(-width / 2, height / 2);
  ctx.closePath();
  shape.fill ? ctx.fill() : ctx.stroke();
}

function drawLine(ctx: CanvasRenderingContext2D, shape: Shape) {
  const width = shape.width || 100;
  ctx.beginPath();
  ctx.moveTo(-width / 2, 0);
  ctx.lineTo(width / 2, 0);
  ctx.stroke();
}

function drawText(ctx: CanvasRenderingContext2D, shape: Shape) {
  const fontSize = shape.height || 24;
  ctx.font = `${fontSize}px Arial, sans-serif`;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  if (shape.fill) {
    ctx.fillText(shape.text || '', 0, 0);
  } else {
    ctx.strokeText(shape.text || '', 0, 0);
  }
}

function drawPolygon(ctx: CanvasRenderingContext2D, shape: Shape) {
  if (!shape.points || shape.points.length < 3) return;
  ctx.beginPath();
  ctx.moveTo(shape.points[0].x, shape.points[0].y);
  shape.points.forEach((point, i) => {
    if (i > 0) ctx.lineTo(point.x, point.y);
  });
  ctx.closePath();
  shape.fill ? ctx.fill() : ctx.stroke();
}

function drawPath(ctx: CanvasRenderingContext2D, shape: Shape) {
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
  ctx.stroke();
}
