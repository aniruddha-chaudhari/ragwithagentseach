import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
});

// Session management
export const getSessions = async () => {
  const response = await api.get('/sessions');
  return response.data;
};

export const createSession = async (sessionName) => {
  const response = await api.post('/sessions', { session_name: sessionName });
  return response.data;
};

export const getSession = async (sessionId) => {
  const response = await api.get(`/sessions/${sessionId}`);
  return response.data;
};

export const deleteSession = async (sessionId) => {
  const response = await api.delete(`/sessions/${sessionId}`);
  return response.data;
};

// Document processing
export const processDocument = async (file, sessionId = null) => {
  const formData = new FormData();
  formData.append('file', file);
  if (sessionId) {
    formData.append('session_id', sessionId);
  }
  const response = await api.post('/process/document', formData);
  return response.data;
};

export const processUrl = async (url, sessionId = null) => {
  const response = await api.post('/process/url', { url, session_id: sessionId });
  return response.data;
};

export const getSessionSources = async (sessionId) => {
  const response = await api.get(`/sources/${sessionId}`);
  return response.data;
};

// Chat functionality
export const sendMessage = async (content, sessionId = null, forceWebSearch = false) => {
  const response = await api.post('/chat', {
    content,
    session_id: sessionId,
    force_web_search: forceWebSearch,
  });
  return response.data;
};

export default api;
