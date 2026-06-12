import { useCallback } from 'react';

interface VoiceCommandHandler {
  onDraw: (text: string) => void;
  onUndo: () => void;
  onRedo: () => void;
  onClear: () => void;
  onStartRecording: () => void;
  onStopRecording: () => void;
  onPlayRecording: () => void;
}

export function useVoiceCommands(handler: VoiceCommandHandler) {
  const processCommand = useCallback((text: string) => {
    const lower = text.toLowerCase().trim();

    // 撤销命令
    if (
      lower.includes('撤销') ||
      lower.includes('undo') ||
      lower.includes('返回上一步') ||
      lower.includes('撤回')
    ) {
      handler.onUndo();
      return;
    }

    // 重做命令
    if (
      lower.includes('重做') ||
      lower.includes('redo') ||
      lower.includes('恢复')
    ) {
      handler.onRedo();
      return;
    }

    // 清空命令
    if (
      lower.includes('清空') ||
      lower.includes('清除') ||
      lower.includes('clear') ||
      lower.includes('全部删除') ||
      lower.includes('重新开始')
    ) {
      handler.onClear();
      return;
    }

    // 录制命令
    if (
      lower.includes('开始录制') ||
      lower.includes('开始记录') ||
      lower.includes('start recording')
    ) {
      handler.onStartRecording();
      return;
    }

    if (
      lower.includes('停止录制') ||
      lower.includes('停止记录') ||
      lower.includes('stop recording')
    ) {
      handler.onStopRecording();
      return;
    }

    // 回放命令
    if (
      lower.includes('回放') ||
      lower.includes('播放') ||
      lower.includes('replay') ||
      lower.includes('play')
    ) {
      handler.onPlayRecording();
      return;
    }

    // 其他命令作为绘图指令
    handler.onDraw(text);
  }, [handler]);

  return { processCommand };
}
