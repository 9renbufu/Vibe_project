import { useState, useCallback } from 'react';
import { SceneState } from '../types';

interface HistoryState {
  past: SceneState[];
  present: SceneState;
  future: SceneState[];
}

export function useHistory(initialState: SceneState) {
  const [history, setHistory] = useState<HistoryState>({
    past: [],
    present: initialState,
    future: [],
  });

  const pushState = useCallback((newState: SceneState) => {
    setHistory(prev => ({
      past: [...prev.past, prev.present].slice(-50), // 最多保存50步
      present: newState,
      future: [],
    }));
  }, []);

  const undo = useCallback(() => {
    setHistory(prev => {
      if (prev.past.length === 0) return prev;

      const previous = prev.past[prev.past.length - 1];
      const newPast = prev.past.slice(0, -1);

      return {
        past: newPast,
        present: previous,
        future: [prev.present, ...prev.future],
      };
    });
  }, []);

  const redo = useCallback(() => {
    setHistory(prev => {
      if (prev.future.length === 0) return prev;

      const next = prev.future[0];
      const newFuture = prev.future.slice(1);

      return {
        past: [...prev.past, prev.present],
        present: next,
        future: newFuture,
      };
    });
  }, []);

  const canUndo = history.past.length > 0;
  const canRedo = history.future.length > 0;

  return {
    state: history.present,
    pushState,
    undo,
    redo,
    canUndo,
    canRedo,
    historyLength: history.past.length,
  };
}
