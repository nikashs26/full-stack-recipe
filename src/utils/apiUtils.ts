import { API_BASE_URL } from '../config/api';

export const apiCall = async (endpoint: string, options: RequestInit = {}) => {
  const token = localStorage.getItem('auth_token');
  const headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'X-Requested-With': 'XMLHttpRequest',
    ...options.headers,
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  // Handle absolute URLs (starting with http:// or https://)
  const url = endpoint.startsWith('http') ? endpoint : `${API_BASE_URL}${endpoint}`;
  
  console.log('🌐 Making API call to:', url);
  
  const response = await fetch(url, {
    ...options,
    headers,
    credentials: 'include',
  });

  return response;
}; 