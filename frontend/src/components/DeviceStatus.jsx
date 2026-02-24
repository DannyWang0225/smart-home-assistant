
import React from 'react';
import { FaLightbulb, FaFan, FaWindowMaximize, FaThermometerHalf } from 'react-icons/fa';

const DeviceStatus = ({ state, onControl }) => {
  if (!state) return <div className="loading">正在加载设备状态...</div>;

  const getStatusColor = (isOn) => isOn ? '#facc15' : '#9ca3af'; // Yellow for on, gray for off
  const getFanColor = (isOn) => isOn ? '#3b82f6' : '#9ca3af'; // Blue for on
  const getWindowColor = (isOpen) => isOpen ? '#22c55e' : '#ef4444'; // Green for open, red for closed

  const isLightOn = state.light?.state === 'on';
  const isAcOn = state.ac?.state === 'on';
  const isWindowOpen = state.window?.state === 'open';
  const tempValue = state.temperature?.last_value || '--';

  return (
    <div className="device-panel">
      <h2>设备状态</h2>
      <div className="device-grid">
        <div 
          className={`device-card ${isLightOn ? 'active' : ''} interactive`}
          onClick={() => onControl('light', isLightOn ? '关' : '开')}
          title={isLightOn ? '点击关灯' : '点击开灯'}
        >
          <FaLightbulb size={40} color={getStatusColor(isLightOn)} />
          <div className="device-info">
            <span className="device-name">灯光</span>
            <span className="device-value">{isLightOn ? '开启' : '关闭'}</span>
          </div>
        </div>
        
        <div 
          className={`device-card ${isAcOn ? 'active' : ''} interactive`}
          onClick={() => onControl('ac', isAcOn ? '关' : '开')}
          title={isAcOn ? '点击关空调' : '点击开空调'}
        >
          <FaFan size={40} color={getFanColor(isAcOn)} className={isAcOn ? 'spin' : ''} />
          <div className="device-info">
            <span className="device-name">空调</span>
            <span className="device-value">{isAcOn ? '开启' : '关闭'}</span>
          </div>
        </div>
        
        <div 
          className={`device-card ${isWindowOpen ? 'active' : ''} interactive`}
          onClick={() => onControl('window', isWindowOpen ? '关' : '开')}
          title={isWindowOpen ? '点击关窗' : '点击开窗'}
        >
          <FaWindowMaximize size={40} color={getWindowColor(isWindowOpen)} />
          <div className="device-info">
            <span className="device-name">窗户</span>
            <span className="device-value">{isWindowOpen ? '开启' : '关闭'}</span>
          </div>
        </div>
        
        <div 
          className="device-card interactive"
          onClick={() => onControl('temperature', '检测')}
          title="点击检测温度"
        >
          <FaThermometerHalf size={40} color="#f97316" />
          <div className="device-info">
            <span className="device-name">温度</span>
            <span className="device-value">{tempValue}°C</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DeviceStatus;
