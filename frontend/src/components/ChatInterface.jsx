
import React, { useState, useEffect, useRef } from 'react';
import { FaMicrophone, FaStop } from 'react-icons/fa';

const ChatInterface = ({ messages, onSendMessage, isProcessing }) => {
  const [input, setInput] = useState('');
  const [isListening, setIsListening] = useState(false);
  const messagesEndRef = useRef(null);
  const recognitionRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(scrollToBottom, [messages]);

  useEffect(() => {
    // Initialize SpeechRecognition if available
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = false;
      recognitionRef.current.lang = 'zh-CN';

      recognitionRef.current.onstart = () => {
        setIsListening(true);
      };

      recognitionRef.current.onend = () => {
        setIsListening(false);
      };

      recognitionRef.current.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        setInput(prev => {
           // If there is previous text, append with space? Or replace? 
           // Usually replacing or appending depends on UX. Let's append if not empty.
           return prev ? prev + ' ' + transcript : transcript;
        });
        // Optional: Auto-send if confidence is high? Better let user confirm.
      };
      
      recognitionRef.current.onerror = (event) => {
          console.error("Speech recognition error", event.error);
          setIsListening(false);
      };
    }
  }, []);

  const toggleListening = () => {
    if (!recognitionRef.current) {
      alert("您的浏览器不支持语音识别功能，请使用 Chrome 浏览器。");
      return;
    }

    if (isListening) {
      recognitionRef.current.stop();
    } else {
      recognitionRef.current.start();
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!input.trim()) return;
    onSendMessage(input);
    setInput('');
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        <h2>智能助手</h2>
      </div>
      <div className="chat-messages">
        {messages.map((msg, index) => (
          <div key={index} className={`message ${msg.sender}`}>
            <div className="message-content">
              {msg.text}
              {msg.data && msg.type === 'question' && (
                <div className="suggestions">
                  {msg.data.map((cmd, idx) => (
                     <button 
                       key={idx} 
                       className="suggestion-btn"
                       onClick={() => onSendMessage(cmd.suggestion || cmd.action)}
                     >
                       {cmd.suggestion || cmd.action}
                     </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
        {isProcessing && (
          <div className="message assistant">
            <div className="message-content processing">
              <span>正在思考...</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      <form onSubmit={handleSubmit} className="chat-input-form">
        <button 
            type="button" 
            className={`mic-btn ${isListening ? 'listening' : ''}`}
            onClick={toggleListening}
            title={isListening ? "停止录音" : "开始语音输入"}
            disabled={isProcessing}
        >
            {isListening ? <FaStop /> : <FaMicrophone />}
        </button>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={isListening ? "正在聆听..." : "请输入指令 (e.g., 打开空调)"}
          disabled={isProcessing}
        />
        <button type="submit" disabled={isProcessing || !input.trim()}>发送</button>
      </form>
    </div>
  );
};

export default ChatInterface;
