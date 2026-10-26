import axios from 'axios';

// Resolve and sanitize API Base URL for both development & production
export const getApiBaseUrl = () => {
  let url = (import.meta.env.VITE_API_URL || '').trim();

  // Strip wrapping quotes (in case user added quotes in Vercel UI)
  url = url.replace(/^['"]+|['"]+$/g, '').trim();

  // If no environment variable is provided, default to local FastAPI dev server
  if (!url) {
    return 'http://127.0.0.1:8000/api/v1';
  }

  // Remove trailing slashes
  url = url.replace(/\/+$/, '');

  // If user passed root URL (e.g., https://brandpulse-backend.onrender.com), ensure /api/v1 is appended
  if (!url.endsWith('/api/v1') && !url.endsWith('/api')) {
    url = `${url}/api/v1`;
  } else if (url.endsWith('/api')) {
    url = `${url}/v1`;
  }

  // Ensure same-site origin matching between localhost and 127.0.0.1
  if (typeof window !== 'undefined' && window.location?.hostname) {
    if (window.location.hostname === 'localhost' && url.includes('127.0.0.1')) {
      url = url.replace('127.0.0.1', 'localhost');
    } else if (window.location.hostname === '127.0.0.1' && url.includes('localhost')) {
      url = url.replace('localhost', '127.0.0.1');
    }
  }

  return url;
};

export const API_BASE_URL = getApiBaseUrl();

// Retrieve root URL for direct health checks & static file downloads
export const getBackendRootUrl = () => {
  return API_BASE_URL.replace(/\/api\/v1\/?$/, '').replace(/\/api\/?$/, '');
};

// In-memory access token storage with localStorage persistence fallback
let inMemoryAccessToken = null;

export const setAccessToken = (token) => {
  inMemoryAccessToken = token;
  if (token) {
    try { localStorage.setItem('bp_access_token', token); } catch (_) {}
  } else {
    try { localStorage.removeItem('bp_access_token'); } catch (_) {}
  }
};

export const getAccessToken = () => {
  if (inMemoryAccessToken) return inMemoryAccessToken;
  try {
    return localStorage.getItem('bp_access_token');
  } catch (_) {
    return null;
  }
};

export const setRefreshToken = (token) => {
  if (token) {
    try { localStorage.setItem('bp_refresh_token', token); } catch (_) {}
  } else {
    try { localStorage.removeItem('bp_refresh_token'); } catch (_) {}
  }
};

export const getRefreshToken = () => {
  try {
    return localStorage.getItem('bp_refresh_token');
  } catch (_) {
    return null;
  }
};

const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true, // Sends httpOnly cookies (including refresh_token)
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 35000, // 35s timeout to gracefully allow Render free tier wakeups
});

// Attach JWT access token and fallback refresh token to requests automatically
api.interceptors.request.use(
  (config) => {
    const token = getAccessToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    const rToken = getRefreshToken();
    if (rToken && !config.headers['X-Refresh-Token']) {
      config.headers['X-Refresh-Token'] = rToken;
    }
    if (import.meta.env.DEV) {
      console.debug(`[BrandPulse API Request] ${config.method?.toUpperCase()} ${config.baseURL}${config.url}`);
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor: refresh access token on 401 if refresh cookie or fallback is present
let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

api.interceptors.response.use(
  (response) => {
    if (import.meta.env.DEV) {
      console.debug(`[BrandPulse API Response] ${response.status} ${response.config?.url}`);
    }
    return response;
  },
  async (error) => {
    const originalRequest = error.config;
    if (!originalRequest) {
      return Promise.reject(error);
    }

    const isAuthRoute = originalRequest.url?.includes('/auth/login') ||
      originalRequest.url?.includes('/auth/register') ||
      originalRequest.url?.includes('/auth/refresh') ||
      originalRequest.url?.includes('/auth/logout');

    if (error.response?.status === 401 && !originalRequest._retry && !isAuthRoute) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            return api(originalRequest);
          })
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const rToken = getRefreshToken();
        const refreshRes = await api.post('/auth/refresh', rToken ? { refresh_token: rToken } : {}, {
          headers: rToken ? { 'X-Refresh-Token': rToken } : {}
        });
        const newToken = refreshRes.data?.access_token;
        setAccessToken(newToken);
        if (refreshRes.data?.refresh_token) {
          setRefreshToken(refreshRes.data.refresh_token);
        }
        processQueue(null, newToken);
        originalRequest.headers.Authorization = `Bearer ${newToken}`;
        return api(originalRequest);
      } catch (refreshErr) {
        processQueue(refreshErr, null);
        setAccessToken(null);
        setRefreshToken(null);
        return Promise.reject(refreshErr);
      } finally {
        isRefreshing = false;
      }
    }

    if (import.meta.env.DEV) {
      const url = error.config?.url || 'unknown';
      const status = error.response?.status || 'Network / Unreachable';
      console.warn(
        `[BrandPulse API Error] ${error.config?.method?.toUpperCase()} ${url} -> Status: ${status}`,
        error.response?.data || error.message
      );
    }
    return Promise.reject(error);
  }
);

// Global API service methods
export const authAPI = {
  login: (email, password) => api.post('/auth/login', { email, password }),
  register: (data) => api.post('/auth/register', data),
  demoLogin: (persona = 'brand_manager') => api.post(`/auth/demo-login?persona=${persona}`),
  firebaseLogin: (authPayload) => api.post('/auth/firebase-login', authPayload),
  refreshToken: (token) => {
    const rToken = token || getRefreshToken();
    return api.post('/auth/refresh', rToken ? { refresh_token: rToken } : {}, {
      headers: rToken ? { 'X-Refresh-Token': rToken } : {}
    });
  },
  logout: () => api.post('/auth/logout'),
  getMe: () => api.get('/auth/me'),
  getAuditLogs: (limit = 30) => api.get('/auth/audit-logs', { params: { limit } }),
  getFirewallStatus: () => api.get('/auth/firewall-status'),
  getFirewallLogs: (limit = 20) => api.get('/auth/firewall-logs', { params: { limit } }),
  testFirewall: (payload) => api.post('/auth/firewall-test', payload),
};

export const brandsAPI = {
  list: () => api.get('/brands'),
  create: (data) => api.post('/brands', data),
  get: (id) => api.get(`/brands/${id}`),
  update: (id, data) => api.put(`/brands/${id}`, data),
  delete: (id) => api.delete(`/brands/${id}`),
  seedHistory: (id, days = 7) => api.post(`/brands/${id}/seed?days=${days}`),
  getPresets: () => api.get('/brands/presets'),
  addLocation: (brandId, data) => api.post(`/brands/${brandId}/locations`, data),
  updateLocation: (brandId, locationId, data) => api.put(`/brands/${brandId}/locations/${locationId}`, data),
  deleteLocation: (brandId, locationId) => api.delete(`/brands/${brandId}/locations/${locationId}`),
};

export const businessAPI = brandsAPI;

export const monitoringAPI = {
  getMentions: (params) => api.get('/monitoring/mentions', { params }),
  createMention: (data) => api.post('/monitoring/mentions', data),
  replyToMention: (mentionId, replyText) => api.post(`/monitoring/mentions/${mentionId}/reply`, { reply_text: replyText }),
  simulateMention: (brandId, scenario) => api.post(`/monitoring/simulate?brand_id=${brandId}&scenario=${scenario}`),
  testNLP: (text) => api.post(`/monitoring/test-nlp?text=${encodeURIComponent(text)}`),
  // Monitored Summaries in MongoDB ('summaries' collection)
  getSummaries: (brandId) => api.get('/monitoring/summaries', { params: { brand_id: brandId } }),
  getSummary: (summaryId) => api.get(`/monitoring/summaries/${summaryId}`),
  generateSummary: (brandId) => api.post(`/monitoring/summaries/generate?brand_id=${brandId}`),
  updateSummary: (summaryId, data) => api.patch(`/monitoring/summaries/${summaryId}`, data),
  deleteSummary: (summaryId) => api.delete(`/monitoring/summaries/${summaryId}`),
};

export const analyticsAPI = {
  getOverview: (brandId, timeRange = '7d', isSimulated = undefined) => 
    api.get('/analytics/overview', { params: { brand_id: brandId, time_range: timeRange, is_simulated: isSimulated } }),
  getTrends: (brandId, timeRange = '7d', isSimulated = undefined) => 
    api.get('/analytics/sentiment-trends', { params: { brand_id: brandId, time_range: timeRange, is_simulated: isSimulated } }),
  getEmotions: (brandId) => api.get('/analytics/emotions', { params: { brand_id: brandId } }),
  getTopics: (brandId) => api.get('/analytics/topics', { params: { brand_id: brandId } }),
  getIntent: (brandId) => api.get('/analytics/intent', { params: { brand_id: brandId } }),
  getForecast: (brandId) => api.get('/analytics/forecast', { params: { brand_id: brandId } }),
  getInsights: (brandId) => api.get('/analytics/insights', { params: { brand_id: brandId } }),
};

export const crisisAPI = {
  getAlerts: (brandId, status = 'all', isSimulated = undefined) => 
    api.get('/crisis/alerts', { params: { brand_id: brandId, status, is_simulated: isSimulated } }),
  acknowledgeAlert: (alertId) => api.post(`/crisis/alerts/${alertId}/acknowledge`),
  resolveAlert: (alertId) => api.post(`/crisis/alerts/${alertId}/resolve`),
  getStatus: (brandId) => api.get('/crisis/status', { params: { brand_id: brandId } }),
  simulateCrisis: (brandId, scenarioType = 'outage_disaster') => api.post(`/crisis/simulate-crisis?brand_id=${brandId}&scenario_type=${scenarioType}`),
};

export const competitorsAPI = {
  getBenchmarks: (brandId) => api.get('/competitors/benchmarks', { params: { brand_id: brandId } }),
  getSOV: (brandId) => api.get('/competitors/sov', { params: { brand_id: brandId } }),
  getHeadToHead: (brandId, competitor) => api.get('/competitors/head-to-head', { params: { brand_id: brandId, competitor } }),
  list: (brandId) => api.get('/competitors/list', { params: { brand_id: brandId } }),
  add: (brandId, data) => api.post(`/competitors/?brand_id=${brandId}`, data),
  remove: (brandId, shopName) => api.delete(`/competitors/${encodeURIComponent(shopName)}`, { params: { brand_id: brandId } }),
  importCsv: (brandId, shopName, formData) => api.post(`/competitors/import-csv?brand_id=${brandId}&shop_name=${encodeURIComponent(shopName)}`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
};

export const notificationsAPI = {
  getSettings: (brandId) => api.get('/notifications/settings', { params: { brand_id: brandId } }),
  updateSettings: (brandId, data) => api.put(`/notifications/settings?brand_id=${brandId}`, data),
  sendTest: (data) => api.post('/notifications/test', data),
  triggerDigest: (brandId) => api.post('/notifications/trigger-digest', null, { params: { brand_id: brandId } }),
};

export const billingAPI = {
  getPlans: () => api.get('/billing/plans'),
  getUsage: (brandId) => api.get('/billing/usage', { params: { brand_id: brandId } }),
  createOrder: (data) => api.post('/billing/create-order', data),
  verifyPayment: (data) => api.post('/billing/verify-payment', data),
};

export const reportsAPI = {
  generate: (data) => api.post('/reports/generate', data),
  getHistory: (brandId) => api.get('/reports/history', { params: { brand_id: brandId } }),
  getDownloadUrl: (filename) => {
    const token = getAccessToken();
    return `${API_BASE_URL}/reports/download/${filename}${token ? `?token=${encodeURIComponent(token)}` : ''}`;
  },
  downloadReport: async (filename) => {
    const token = getAccessToken();
    const res = await api.get(`/reports/download/${filename}`, {
      responseType: 'blob',
      params: token ? { token } : {}
    });
    const mimeType = filename.endsWith('.pdf') 
      ? 'application/pdf' 
      : filename.endsWith('.csv') 
      ? 'text/csv' 
      : 'application/json';
    const blob = new Blob([res.data], { type: mimeType });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    link.parentNode.removeChild(link);
    window.URL.revokeObjectURL(url);
    return true;
  },
};

export const googleAPI = {
  getStatus: (brandId) => api.get('/google/status', { params: { brand_id: brandId } }),
  connect: (data) => api.post('/google/connect', data),
  sync: (brandId) => api.post('/google/sync', null, { params: { brand_id: brandId } }),
  reply: (mentionId, replyText, rating = null) => 
    api.post(`/google/reviews/${mentionId}/reply`, { reply_text: replyText, rating }),
};

export const facebookAPI = {
  getStatus: (brandId) => api.get('/facebook/status', { params: { brand_id: brandId } }),
  sync: (brandId) => api.post('/facebook/sync', null, { params: { brand_id: brandId } }),
  reply: (mentionId, replyText) => 
    api.post(`/facebook/reviews/${mentionId}/reply`, { reply_text: replyText }),
};

export const instagramAPI = {
  getAuthUrl: (brandId) => api.get('/instagram/auth-url', { params: { brand_id: brandId } }),
  callback: (brandId, code, state) => api.post('/instagram/callback', { brand_id: brandId, code, state }),
  getStatus: (brandId) => api.get('/instagram/status', { params: { brand_id: brandId } }),
  disconnect: (brandId) => api.post(`/instagram/disconnect?brand_id=${brandId}`),
  sync: (brandId) => api.post(`/instagram/sync?brand_id=${brandId}`),
  getMetrics: (brandId) => api.get('/instagram/metrics', { params: { brand_id: brandId } }),
};

export const systemAPI = {
  getDbStatus: () => api.get('/system/db-status'),
  connectDb: (uri, databaseName = 'brandpulse_ai') => api.post('/system/db-connect', { uri, database_name: databaseName }),
};

export const mlAPI = {
  getDatasetInfo: () => api.get('/ml/dataset-info'),
  getMetrics: () => api.get('/ml/metrics'),
  predict: (text) => api.post('/ml/predict', { text }),
  trainModel: () => api.post('/ml/train'),
  getTrainStatus: (jobId) => api.get(`/ml/train/${jobId}`),
};

export const datasetAPI = {
  previewFile: (formData) => api.post('/dataset/preview', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  uploadFile: (formData) => api.post('/dataset/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  uploadAndIngest: (formData) => api.post('/dataset/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  pasteReviews: (data) => api.post('/dataset/paste-reviews', data),
  getSamples: () => api.get('/dataset/samples'),
  ingestSample: (sampleId, brandId = null, mode = 'append') => api.post(`/dataset/ingest-sample/${sampleId}`, null, {
    params: { brand_id: brandId, mode }
  }),
};



export const assistantAPI = {
  getSuggestedQuestions: (businessId) => api.get('/assistant/suggested-questions', {
    params: { business_id: businessId }
  }),
  getBudgetStatus: (businessId) => api.get('/assistant/budget-status', {
    params: { business_id: businessId }
  }),
  getConversations: (businessId) => api.get('/assistant/conversations', {
    params: { business_id: businessId }
  }),
  getConversation: (conversationId) => api.get(`/assistant/conversations/${conversationId}`),
  deleteConversation: (conversationId) => api.delete(`/assistant/conversations/${conversationId}`),
  streamChat: async ({ businessId, message, conversationId, language = 'en', onToolCall, onDelta, onDone, onError }) => {
    try {
      const token = getAccessToken();
      const response = await fetch(`${API_BASE_URL}/assistant/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        },
        credentials: 'include',
        body: JSON.stringify({
          business_id: businessId,
          message,
          conversation_id: conversationId,
          language
        })
      });

      if (!response.ok) {
        const errJson = await response.json().catch(() => ({}));
        throw new Error(errJson.detail || `Chat request failed (${response.status})`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop(); // keep last unfinished line

        for (const line of lines) {
          const trimmed = line.trim();
          if (trimmed.startsWith('data: ')) {
            const rawJson = trimmed.slice(6);
            try {
              const parsed = JSON.parse(rawJson);
              if (parsed.type === 'tool_call' && onToolCall) {
                onToolCall(parsed.tool, parsed.args);
              } else if (parsed.type === 'text_delta' && onDelta) {
                onDelta(parsed.delta);
              } else if (parsed.type === 'done' || parsed.type === 'completed') {
                if (onDone) onDone(parsed);
              } else if (parsed.type === 'error') {
                if (onError) onError(parsed.detail || 'Assistant error');
              }
            } catch (err) {
              console.warn('SSE Parse error', err, rawJson);
            }
          }
        }
      }
    } catch (err) {
      if (onError) onError(err.message || 'Failed to reach AI assistant');
      else throw err;
    }
  }
};

export const healthAPI = {
  checkHealth: () => api.get('/health'),
};

// Aliases matching standard camelCase naming conventions
export const authApi = authAPI;
export const brandApi = brandsAPI;
export const brandsApi = brandsAPI;
export const listeningApi = monitoringAPI;
export const monitoringApi = monitoringAPI;
export const conversationsApi = monitoringAPI;
export const analyticsApi = analyticsAPI;
export const crisisApi = crisisAPI;
export const competitorApi = competitorsAPI;
export const competitorsApi = competitorsAPI;
export const aiApi = analyticsAPI;
export const aiInsightsApi = analyticsAPI;
export const mediaApi = instagramAPI;
export const instagramApi = instagramAPI;
export const googleApi = googleAPI;
export const facebookApi = facebookAPI;
export const reportsApi = reportsAPI;
export const systemApi = systemAPI;
export const mlApi = mlAPI;
export const datasetApi = datasetAPI;
export const healthApi = healthAPI;


export default api;

