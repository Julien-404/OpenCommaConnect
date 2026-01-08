import axios from 'axios';
import { useAuthStore } from '../store/authStore';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = useAuthStore.getState().accessToken;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to handle errors
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Token expired, logout
      useAuthStore.getState().logout();
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  register: (email: string, password: string, name?: string) =>
    api.post('/auth/register', { email, password, name }),

  login: (email: string, password: string) =>
    api.post('/auth/login', { email, password }),

  logout: () => api.post('/auth/logout'),

  getCurrentUser: () => api.get('/auth/me'),

  refreshToken: (refreshToken: string) =>
    api.post('/auth/refresh', { refresh_token: refreshToken }),
};

// Devices API
export const devicesAPI = {
  list: () => api.get('/devices'),

  get: (dongleId: string) => api.get(`/devices/${dongleId}`),

  create: (data: { dongle_id: string; alias?: string }) =>
    api.post('/devices', data),

  update: (dongleId: string, data: { alias?: string }) =>
    api.put(`/devices/${dongleId}`, data),

  delete: (dongleId: string) => api.delete(`/devices/${dongleId}`),

  getStatus: (dongleId: string) => api.get(`/devices/${dongleId}/status`),

  getLocation: (dongleId: string) => api.get(`/devices/${dongleId}/location`),
};

// Routes API
export const routesAPI = {
  list: (page = 1, pageSize = 20, deviceId?: string) =>
    api.get('/routes', { params: { page, page_size: pageSize, device_id: deviceId } }),

  get: (routeName: string) => api.get(`/routes/${routeName}`),

  delete: (routeName: string) => api.delete(`/routes/${routeName}`),

  getSegments: (routeName: string) => api.get(`/routes/${routeName}/segments`),

  getEvents: (routeName: string) => api.get(`/routes/${routeName}/events`),

  getVideoUrl: (routeName: string, segment?: number) => {
    const params = segment ? `?segment=${segment}` : '';
    return `${API_URL}/api/v1/routes/${routeName}/video${params}`;
  },

  getThumbnailUrl: (routeName: string, segment?: number) => {
    const params = segment ? `?segment=${segment}` : '';
    return `${API_URL}/api/v1/routes/${routeName}/thumbnail${params}`;
  },
};

export default api;
