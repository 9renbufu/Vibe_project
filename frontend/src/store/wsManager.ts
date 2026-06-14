/**
 * 共享 WebSocket 管理器
 * 让 VoicePanel 和 StatusPanel 都能发送指令
 */

let wsRef: WebSocket | null = null;

export function setWs(ws: WebSocket | null) {
  wsRef = ws;
}

export function getWs(): WebSocket | null {
  return wsRef;
}

export function sendCommand(text: string) {
  if (!wsRef || wsRef.readyState !== WebSocket.OPEN) return false;
  wsRef.send(JSON.stringify({
    type: 'voice_input',
    data: { text: text.trim() },
  }));
  return true;
}

export function sendMessage(type: string, data?: any) {
  if (!wsRef || wsRef.readyState !== WebSocket.OPEN) return false;
  wsRef.send(JSON.stringify({ type, data }));
  return true;
}

export function sendCreateRecord(title?: string) {
  return sendMessage('create_record', { title });
}

export function sendSwitchRecord(recordId: string) {
  return sendMessage('switch_record', { record_id: recordId });
}

export function sendListRecords() {
  return sendMessage('list_records');
}
