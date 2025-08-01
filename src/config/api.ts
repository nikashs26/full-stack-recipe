// API Configuration for different environments
export const API_CONFIG = {
  development: {
    baseURL: 'http://localhost:5003/api',
    timeout: 30000
  },
  production: {
    baseURL: import.meta.env.VITE_REACT_APP_API_URL || 'https://your-backend-url.railway.app/api',
    timeout: 30000
  }
};

export const getApiConfig = () => {
  const env = import.meta.env.MODE || 'development';
  console.log('🌍 Environment:', env);
  console.log('🔗 API URL:', API_CONFIG[env as keyof typeof API_CONFIG].baseURL);
  console.log('🔧 VITE_REACT_APP_API_URL:', import.meta.env.VITE_REACT_APP_API_URL || 'Not set');
  return API_CONFIG[env as keyof typeof API_CONFIG];
};

export const API_BASE_URL = getApiConfig().baseURL; 