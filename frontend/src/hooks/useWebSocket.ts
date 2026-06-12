import { useCallback, useEffect, useRef, useState } from 'react';
import { SceneState, AIResponse, WebSocketMessage } from '../types';

export function useWebSocket() {
  const ws = useRef<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const [scene, setScene] = useState<SceneState>({
    shapes: [],
    background: { r: 255, g: 255, b: 255 },
    width: 800,
    height: 600,
  });
  const [lastResponse, setLastResponse] = useState<AIResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const connect = useCallback(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;

    ws.current = new WebSocket(wsUrl);

    ws.current.onopen = () => {
      setConnected(true);
      setError(null);
      ws.current?.send(JSON.stringify({ type: 'get_state' }));
    };

    ws.current.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);

        switch (message.type) {
          case 'state':
            setScene(message.data as SceneState);
            break;
          case 'action':
            setLastResponse(message.data as AIResponse);
            break;
          case 'error':
            setError((message.data as { message: string }).message);
            break;
        }
      } catch (e) {
        console.error('Failed to parse message:', e);
      }
    };

    ws.current.onclose = () => {
      setConnected(false);
      setTimeout(connect, 3000);
    };

    ws.current.onerror = () => {
      setError('WebSocket connection error');
    };
  }, []);

  useEffect(() => {
    connect();
    return () => {
      ws.current?.close();
    };
  }, [connect]);

  const sendVoiceCommand = useCallback((text: string) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({
        type: 'voice',
        data: { text },
      }));
    }
  }, []);

  const clearScene = useCallback(async () => {
    try {
      await fetch('/api/scene/clear', { method: 'POST' });
      ws.current?.send(JSON.stringify({ type: 'get_state' }));
    } catch (e) {
      console.error('Failed to clear scene:', e);
    }
  }, []);

  return {
    connected,
    scene,
    lastResponse,
    error,
    sendVoiceCommand,
    clearScene,
  };
}
