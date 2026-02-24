
import React, { useState, useEffect } from 'react';
import DeviceStatus from './components/DeviceStatus';
import ChatInterface from './components/ChatInterface';
import { chatWithAssistant, getDeviceState, controlDevice } from './services/api';
import './SmartHome.css';

const SmartHome = () => {
  const [deviceState, setDeviceState] = useState(null);
  const [messages, setMessages] = useState([
    { sender: 'assistant', text: '您好！我是您的智能家居助手。您可以让我控制灯光、空调、窗户，或者查询温度。' }
  ]);
  const [potentialCommands, setPotentialCommands] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);

  // Poll device state every 2 seconds
  useEffect(() => {
    const fetchState = async () => {
      const state = await getDeviceState();
      if (state) setDeviceState(state);
    };
    
    fetchState();
    const interval = setInterval(fetchState, 2000);
    return () => clearInterval(interval);
  }, []);

  const handleControl = async (type, action) => {
    const result = await controlDevice(type, action);
    if (result.status === 'success') {
      const state = await getDeviceState();
      if (state) setDeviceState(state);
      // Optional: Add log to chat
      // setMessages(prev => [...prev, { sender: 'assistant', text: `手动操作: ${result.message}` }]);
    } else {
      setMessages(prev => [...prev, { sender: 'assistant', text: `操作失败: ${result.message}` }]);
    }
  };

  const handleSendMessage = async (text) => {
    // Add user message
    const userMsg = { sender: 'user', text };
    setMessages(prev => [...prev, userMsg]);
    setIsProcessing(true);

    // Call API
    const response = await chatWithAssistant(text, potentialCommands);
    
    // Handle response
    let assistantMsg = { sender: 'assistant', text: response.text, type: response.type, data: response.data };
    
    if (response.type === 'question') {
      setPotentialCommands(response.data); // Store context for next reply
    } else {
      setPotentialCommands(null); // Clear context if resolved or new command
    }
    
    // Add assistant message
    setMessages(prev => [...prev, assistantMsg]);
    setIsProcessing(false);
    
    // Refresh state immediately after command execution
    if (response.type === 'success') {
      const state = await getDeviceState();
      if (state) setDeviceState(state);
    }
  };

  return (
    <div className="smart-home-app">
      <header className="app-header">
        <h1>智能家居中控系统</h1>
      </header>
      <main className="app-main">
        <section className="left-panel">
          <DeviceStatus state={deviceState} onControl={handleControl} />
        </section>
        <section className="right-panel">
          <ChatInterface 
            messages={messages} 
            onSendMessage={handleSendMessage} 
            isProcessing={isProcessing}
          />
        </section>
      </main>
    </div>
  );
};


export default SmartHome;
