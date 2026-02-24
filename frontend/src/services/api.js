
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

export const chatWithAssistant = async (message, potentialCommands = null) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/chat`, {
      message,
      potential_commands: potentialCommands
    });
    return response.data;
  } catch (error) {
    console.error("Error chatting with assistant:", error);
    return { type: 'error', text: '无法连接到服务器' };
  }
};

export const getDeviceState = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/state`);
    return response.data;
  } catch (error) {
    console.error("Error getting device state:", error);
    return null;
  }
};

export const controlDevice = async (type, action, device = null) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/control`, {
      type,
      action,
      device
    });
    return response.data;
  } catch (error) {
    console.error("Error controlling device:", error);
    return { status: 'error', message: '操作失败' };
  }
};
