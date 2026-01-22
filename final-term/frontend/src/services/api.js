import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 60000, // 60秒超时
});

// 添加请求拦截器，实现请求去重（防止重复请求）
const pendingRequests = new Map();

api.interceptors.request.use(
  (config) => {
    // 为每个请求生成唯一键
    const requestKey = `${config.method}_${config.url}_${JSON.stringify(config.data || config.params)}`;
    
    // 如果相同的请求正在进行，取消新请求
    if (pendingRequests.has(requestKey)) {
      const cancelToken = pendingRequests.get(requestKey);
      cancelToken.cancel('重复请求已取消');
    }
    
    // 创建新的取消令牌
    const cancelToken = axios.CancelToken.source();
    config.cancelToken = cancelToken.token;
    pendingRequests.set(requestKey, cancelToken);
    
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 添加响应拦截器，清除已完成的请求
api.interceptors.response.use(
  (response) => {
    const requestKey = `${response.config.method}_${response.config.url}_${JSON.stringify(response.config.data || response.config.params)}`;
    pendingRequests.delete(requestKey);
    return response;
  },
  (error) => {
    if (error.config) {
      const requestKey = `${error.config.method}_${error.config.url}_${JSON.stringify(error.config.data || error.config.params)}`;
      pendingRequests.delete(requestKey);
    }
    return Promise.reject(error);
  }
);

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
  generateByTheme: (theme, emotion, length, userIdea, userId) => 
    api.post('/generation/by-theme', { theme, emotion, length, user_idea: userIdea, user_id: userId }),
  
  generateByContext: (previousLines, emotion, length, theme, style, userIdea, userId) => 
    api.post('/generation/by-context', { 
      previous_lines: previousLines, 
      emotion, 
      length, 
      theme,
      style,
      user_idea: userIdea,
      user_id: userId 
    }),
  
  generateFullSong: (style, theme, emotion, userIdea, length, userId) => 
    api.post('/generation/full-song', { style, theme, emotion, user_idea: userIdea, length, user_id: userId }),
  
  convertStyle: (lyrics, targetStyle, userId) => 
    api.post('/generation/convert-style', { lyrics, target_style: targetStyle, user_id: userId }),
  
  continueConversation: (previousLyrics, userFeedback, userId) => 
    api.post('/generation/continue', { previous_lyrics: previousLyrics, user_feedback: userFeedback, user_id: userId }),
  
  getHistory: (userId, limit) => 
    api.get('/generation/history', { params: { user_id: userId, limit } }),
  
  // 歌曲生成API（使用 Suno API）
  generateSong: (lyrics, title, tags, style, voice, makeInstrumental, asyncMode, maxWaitTime, userId) => 
    api.post('/generation/song', { 
      lyrics, 
      title, 
      tags, 
      style,
      voice,
      make_instrumental: makeInstrumental, 
      async_mode: asyncMode,
      max_wait_time: maxWaitTime,
      user_id: userId 
    }),
  
  querySongStatus: (taskId) => 
    api.get('/generation/song/status', { params: { task_id: taskId } }),
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
  
  refreshMusicUrl: (songmid, platform = 'qq', quality = '128') => 
    api.post('/recommendation/refresh-music-url', { songmid, platform, quality }),
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



