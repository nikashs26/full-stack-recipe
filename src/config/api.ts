// API Configuration for different environments
export const API_CONFIG = {
  development: {
    baseURL: 'http://localhost:5003/api',
    timeout: 30000
  },
  production: {
    baseURL: process.env.REACT_APP_API_URL || 'https://your-backend-url.railway.app/api',
    timeout: 30000
  }
};

export const getApiConfig = () => {
  const env = process.env.NODE_ENV || 'development';
  return API_CONFIG[env as keyof typeof API_CONFIG];
};

export const API_BASE_URL = getApiConfig().baseURL; 