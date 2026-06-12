import { useState, useRef, useCallback } from 'react';
import { SceneState } from '../types';

interface RecordingFrame {
  timestamp: number;
  scene: SceneState;
  explanation?: string;
}

export function useRecording() {
  const [isRecording, setIsRecording] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [frames, setFrames] = useState<RecordingFrame[]>([]);
  const startTimeRef = useRef<number>(0);

  const startRecording = useCallback(() => {
    setFrames([]);
    startTimeRef.current = Date.now();
    setIsRecording(true);
  }, []);

  const stopRecording = useCallback(() => {
    setIsRecording(false);
  }, []);

  const recordFrame = useCallback((scene: SceneState, explanation?: string) => {
    if (!isRecording) return;

    setFrames(prev => [...prev, {
      timestamp: Date.now() - startTimeRef.current,
      scene: JSON.parse(JSON.stringify(scene)),
      explanation,
    }]);
  }, [isRecording]);

  const playRecording = useCallback(async (
    onFrame: (scene: SceneState, explanation?: string) => void,
    speed: number = 1
  ) => {
    if (frames.length === 0) return;

    setIsPlaying(true);

    for (let i = 0; i < frames.length; i++) {
      if (!isPlaying) break;

      const frame = frames[i];
      const nextFrame = frames[i + 1];
      const delay = nextFrame
        ? (nextFrame.timestamp - frame.timestamp) / speed
        : 1000;

      onFrame(frame.scene, frame.explanation);
      await new Promise(resolve => setTimeout(resolve, delay));
    }

    setIsPlaying(false);
  }, [frames, isPlaying]);

  const stopPlaying = useCallback(() => {
    setIsPlaying(false);
  }, []);

  const exportRecording = useCallback(() => {
    return JSON.stringify(frames, null, 2);
  }, [frames]);

  const importRecording = useCallback((data: string) => {
    try {
      const imported = JSON.parse(data);
      setFrames(imported);
      return true;
    } catch {
      return false;
    }
  }, []);

  return {
    isRecording,
    isPlaying,
    frames,
    startRecording,
    stopRecording,
    recordFrame,
    playRecording,
    stopPlaying,
    exportRecording,
    importRecording,
  };
}
