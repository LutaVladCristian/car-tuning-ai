import axios from 'axios';

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8001',
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('car_tuning_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('car_tuning_token');
      localStorage.removeItem('car_tuning_username');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
