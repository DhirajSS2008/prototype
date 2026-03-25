import axios from 'axios';

const API_BASE = '/api';

const client = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor to attach JWT token
client.interceptors.request.use((config) => {
  const activeEmail = localStorage.getItem('liqui_sense_active_account');
  if (activeEmail) {
    try {
      const accounts = JSON.parse(localStorage.getItem('liqui_sense_accounts') || '[]');
      const acct = accounts.find((a) => a.email === activeEmail);
      if (acct && acct.token) {
        config.headers.Authorization = `Bearer ${acct.token}`;
      }
    } catch {
      // ignore
    }
  }
  return config;
});

// Interceptor to handle 401 responses
client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired — redirect to login
      const activeEmail = localStorage.getItem('liqui_sense_active_account');
      if (activeEmail) {
        // Remove expired account
        try {
          const accounts = JSON.parse(localStorage.getItem('liqui_sense_accounts') || '[]');
          const filtered = accounts.filter((a) => a.email !== activeEmail);
          localStorage.setItem('liqui_sense_accounts', JSON.stringify(filtered));
          localStorage.removeItem('liqui_sense_active_account');
        } catch {
          // ignore
        }
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

// Auth
export const signUp = (data) => client.post('/auth/signup', data);
export const signIn = (data) => client.post('/auth/signin', data);
export const getMe = (token) =>
  axios.get(`${API_BASE}/auth/me`, {
    headers: { Authorization: `Bearer ${token}` },
  });

// Dashboard
export const fetchDashboard = () => client.get('/dashboard');
export const fetchForecast = (days = 30) => client.get(`/dashboard/forecast?days=${days}`);
export const fetchCategories = () => client.get('/dashboard/categories');
export const setBalance = (balance, date) => client.post('/dashboard/balance', null, { params: { balance, date } });

// Upload
export const uploadFile = (file, onProgress) => {
  const formData = new FormData();
  formData.append('file', file);
  return client.post('/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (e) => {
      if (onProgress) onProgress(Math.round((e.loaded * 100) / e.total));
    },
  });
};

// Transactions
export const fetchTransactions = (params = {}) => client.get('/transactions', { params });
export const createTransaction = (data) => client.post('/transactions', data);
export const updateTransaction = (id, data) => client.put(`/transactions/${id}`, data);
export const deleteTransaction = (id) => client.delete(`/transactions/${id}`);
export const clearAllHistory = () => client.delete('/transactions');

// Affordability
export const checkAffordability = (expense) => client.post('/affordability', expense);
export const fetchAffordabilityHistory = (params = {}) => client.get('/affordability/history', { params });
export const generateEmail = (counterparty, deferralDays) =>
  client.post('/affordability/generate-email', null, { params: { counterparty, deferral_days: deferralDays } });

export default client;
