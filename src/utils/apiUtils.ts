import { API_BASE_URL } from '../config/api';

export const apiCall = async (endpoint: string, options: RequestInit = {}) => {
  const token = localStorage.getItem('auth_token');
  console.log('🔑 apiCall - Token from localStorage:', token ? 'Present' : 'Missing');
  
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    ...(options.headers || {}) as Record<string, string>,
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
    console.log('🔑 apiCall - Added Authorization header');
  } else {
    console.log('⚠️ apiCall - No token found, request will be unauthenticated');
  }

  // Handle absolute URLs (starting with http:// or https://)
  const url = endpoint.startsWith('http') ? endpoint : `${API_BASE_URL}${endpoint}`;
  
  console.log('🌐 Making API call to:', url);
  console.log('📤 Request headers:', headers);
  
  const response = await fetch(url, {
    ...options,
    headers,
    credentials: 'include',
  });

  // If we get a 401 and have a token, try to refresh it and retry once
  if (response.status === 401 && token && !endpoint.includes('/auth/refresh')) {
    console.log('🔄 Got 401, attempting token refresh...');
    
    try {
      const refreshResponse = await fetch(`${API_BASE_URL}/api/auth/refresh`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        credentials: 'include'
      });

      if (refreshResponse.ok) {
        const refreshData = await refreshResponse.json();
        if (refreshData.token) {
          console.log('🔑 Token refreshed, updating localStorage and retrying request');
          localStorage.setItem('auth_token', refreshData.token);
          
          // Retry the original request with the new token
          const newHeaders = {
            ...headers,
            'Authorization': `Bearer ${refreshData.token}`
          };
          
          console.log('🔄 Retrying request with new token...');
          const retryResponse = await fetch(url, {
            ...options,
            headers: newHeaders,
            credentials: 'include',
          });
          
          return retryResponse;
        }
      }
    } catch (error) {
      console.error('❌ Token refresh failed:', error);
    }
  }

  return response;
}; 