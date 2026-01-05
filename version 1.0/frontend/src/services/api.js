import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 分析API
export const analysisAPI = {
  analyze: (lyrics, userId) => 
    api.post('/analysis/analyze', { lyrics, user_id: userId }),
  
  getHistory: (userId, limit) => 
    api.get('/analysis/history', { params: { user_id: userId, limit } }),
  
  analyzeSentiment: (lyrics) => 
    api.post('/analysis/sentiment', { lyrics }),
  
  analyzeTheme: (lyrics) => 
    api.post('/analysis/theme', { lyrics }),
  
  analyzeRhythm: (lyrics) => 
    api.post('/analysis/rhythm', { lyrics }),
};

// 生成API
export const generationAPI = {
  generateByTheme: (theme, emotion, length, userId) => 
    api.post('/generation/by-theme', { theme, emotion, length, user_id: userId }),
  
  generateByContext: (previousLines, userId) => 
    api.post('/generation/by-context', { previous_lines: previousLines, user_id: userId }),
  
  generateFullSong: (style, theme, emotion, userIdea, userId) => 
    api.post('/generation/full-song', { style, theme, emotion, user_idea: userIdea, user_id: userId }),
  
  optimizeRhyme: (line, targetRhyme) => 
    api.post('/generation/optimize-rhyme', { line, target_rhyme: targetRhyme }),
  
  convertStyle: (lyrics, targetStyle, userId) => 
    api.post('/generation/convert-style', { lyrics, target_style: targetStyle, user_id: userId }),
  
  continueConversation: (previousLyrics, userFeedback, userId) => 
    api.post('/generation/continue', { previous_lyrics: previousLyrics, user_feedback: userFeedback, user_id: userId }),
  
  getHistory: (userId, limit) => 
    api.get('/generation/history', { params: { user_id: userId, limit } }),
};

// 历史记录详情和删除API
export const getHistoryDetail = (type, historyId) => 
  api.get(`/${type}/history/${historyId}`);

export const deleteHistory = (type, historyId) => 
  api.delete(`/${type}/history/${historyId}`);

// 推荐API
export const recommendationAPI = {
  recommend: (lyrics, topK, userId) => 
    api.post('/recommendation/recommend', { lyrics, top_k: topK, user_id: userId }),
  
  getKnowledgeGraph: (songs) => 
    api.post('/recommendation/knowledge-graph', { songs }),
  
  getPreferences: (userId) => 
    api.get('/recommendation/preferences', { params: { user_id: userId } }),
  
  updatePreferences: (userId, preferences) => 
    api.put('/recommendation/preferences', { user_id: userId, preferences }),
  
  getHistory: (userId, limit) => 
    api.get('/recommendation/history', { params: { user_id: userId, limit } }),
};

// 用户API
export const userAPI = {
  register: (username, email) => 
    api.post('/user/register', { username, email }),
  
  getUser: (userId) => 
    api.get(`/user/${userId}`),
  
  getUserStats: (userId) => 
    api.get(`/user/${userId}/stats`),
};

export default api;



