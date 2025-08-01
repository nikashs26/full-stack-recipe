// Vite environment variables must be prefixed with VITE_
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5004/api';

// Remove any trailing slashes from the API URL
const cleanApiUrl = API_URL.endsWith('/') ? API_URL.slice(0, -1) : API_URL;

// Ensure the URL ends with /api
const baseURL = cleanApiUrl.endsWith('/api') 
  ? cleanApiUrl 
  : `${cleanApiUrl}/api`;

export const API_BASE_URL = baseURL;