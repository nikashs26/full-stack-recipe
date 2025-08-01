import { API_BASE_URL } from '../config/api';

export const apiCall = async (endpoint: string, options: RequestInit = {}) => {
  const token = localStorage.getItem('auth_token');
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    ...(options.headers || {}) as Record<string, string>,
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  // Handle absolute URLs (starting with http:// or https://)
  const url = endpoint.startsWith('http') ? endpoint : `${API_BASE_URL}${endpoint}`;
  
  const response = await fetch(url, {
    ...options,
    headers,
    credentials: 'include',
  });

  return response;
}; 