import React, { useState, useCallback, useEffect, useRef } from 'react';

interface VoiceInputProps {
  onResult: (text: string) => void;
  onSendText: (text: string) => void;
  isProcessing: boolean;
}

export const VoiceInput: React.FC<VoiceInputProps> = ({
  onResult,
  onSendText,
  isProcessing,
}) => {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [textInput, setTextInput] = useState('');
  const [isSupported, setIsSupported] = useState(false);
  const recognitionRef = useRef<any>(null);
  const onResultRef = useRef(onResult);
  const isListeningRef = useRef(isListening);

  // 保持 onResult 和 isListening 的引用
  useEffect(() => {
    onResultRef.current = onResult;
  }, [onResult]);

  useEffect(() => {
    isListeningRef.current = isListening;
  }, [isListening]);

  useEffect(() => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (SpeechRecognition) {
      setIsSupported(true);
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = 'zh-CN';

      recognition.onresult = (event: any) => {
        console.log('Speech recognition result:', event);
        let interimTranscript = '';
        let finalTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; i++) {
          const result = event.results[i];
          console.log(`Result ${i}: isFinal=${result.isFinal}, transcript=${result[0].transcript}`);
          if (result.isFinal) {
            finalTranscript += result[0].transcript;
          } else {
            interimTranscript += result[0].transcript;
          }
        }

        const currentTranscript = interimTranscript || finalTranscript;
        console.log('Setting transcript:', currentTranscript);
        setTranscript(currentTranscript);

        if (finalTranscript) {
          console.log('Final transcript, calling onResult:', finalTranscript);
          onResultRef.current(finalTranscript);
          // 清空 transcript 显示
          setTimeout(() => setTranscript(''), 1000);
        }
      };

      recognition.onerror = (event: any) => {
        console.error('Speech recognition error:', event.error);
        if (event.error !== 'no-speech') {
          setIsListening(false);
        }
      };

      recognition.onend = () => {
        if (isListeningRef.current) {
          try {
            recognition.start();
          } catch (e) {
            console.error('Failed to restart recognition:', e);
          }
        }
      };

      recognitionRef.current = recognition;
    }

    return () => {
      recognitionRef.current?.abort();
    };
  }, []);

  const toggleListening = useCallback(() => {
    if (!recognitionRef.current) return;

    if (isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
      setTranscript('');
    } else {
      recognitionRef.current.start();
      setIsListening(true);
    }
  }, [isListening]);

  const handleSendText = useCallback(() => {
    if (textInput.trim() && !isProcessing) {
      onSendText(textInput.trim());
      setTextInput('');
    }
  }, [textInput, isProcessing, onSendText]);

  const handleKeyPress = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendText();
    }
  }, [handleSendText]);

  return (
    <div style={styles.container}>
      {/* 语音输入 */}
      <div style={styles.voiceSection}>
        {!isSupported ? (
          <div style={styles.warning}>
            浏览器不支持语音识别，请使用 Chrome
          </div>
        ) : (
          <>
            <button
              onClick={toggleListening}
              disabled={isProcessing}
              style={{
                ...styles.voiceButton,
                ...(isListening ? styles.voiceButtonActive : {}),
                ...(isProcessing ? styles.voiceButtonDisabled : {}),
              }}
            >
              {isListening ? '⏹ 停止录音' : ' 开始说话'}
            </button>

            {isListening && (
              <div style={styles.listening}>
                <span style={styles.pulse}> </span> 正在聆听...
              </div>
            )}

            {transcript && (
              <div style={styles.transcript}>
                {transcript}
              </div>
            )}
          </>
        )}
      </div>

      {/* 文本输入 */}
      <div style={styles.textSection}>
        <input
          type="text"
          value={textInput}
          onChange={(e) => setTextInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="输入设计需求..."
          disabled={isProcessing}
          style={styles.textInput}
        />
        <button
          onClick={handleSendText}
          disabled={!textInput.trim() || isProcessing}
          style={{
            ...styles.sendButton,
            ...((!textInput.trim() || isProcessing) ? styles.sendButtonDisabled : {}),
          }}
        >
          发送
        </button>
      </div>
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  container: {
    padding: '16px',
    backgroundColor: '#fff',
    borderRadius: '12px',
    border: '1px solid #e0e0e0',
  },
  voiceSection: {
    marginBottom: '12px',
  },
  warning: {
    padding: '12px',
    backgroundColor: '#fff3cd',
    borderRadius: '8px',
    fontSize: '12px',
    color: '#856404',
    textAlign: 'center',
  },
  voiceButton: {
    width: '100%',
    padding: '14px',
    fontSize: '16px',
    fontWeight: '600',
    border: 'none',
    borderRadius: '10px',
    cursor: 'pointer',
    backgroundColor: '#4CAF50',
    color: 'white',
    transition: 'all 0.2s',
  },
  voiceButtonActive: {
    backgroundColor: '#f44336',
  },
  voiceButtonDisabled: {
    backgroundColor: '#ccc',
    cursor: 'not-allowed',
  },
  listening: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '8px',
    padding: '8px',
    color: '#f44336',
    fontSize: '13px',
    fontWeight: '500',
  },
  pulse: {
    animation: 'pulse 1s infinite',
  },
  transcript: {
    padding: '10px',
    backgroundColor: '#f0f0f0',
    borderRadius: '8px',
    fontSize: '13px',
    color: '#333',
    marginTop: '8px',
  },
  textSection: {
    display: 'flex',
    gap: '8px',
  },
  textInput: {
    flex: 1,
    padding: '10px 12px',
    fontSize: '13px',
    border: '1px solid #ddd',
    borderRadius: '8px',
    outline: 'none',
  },
  sendButton: {
    padding: '10px 16px',
    fontSize: '13px',
    border: 'none',
    borderRadius: '8px',
    backgroundColor: '#667eea',
    color: 'white',
    cursor: 'pointer',
  },
  sendButtonDisabled: {
    backgroundColor: '#ccc',
    cursor: 'not-allowed',
  },
};
