// Vite environment variables must be prefixed with VITE_
const API_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:5003';

// Remove any trailing slashes from the API URL
const cleanApiUrl = API_URL.endsWith('/') ? API_URL.slice(0, -1) : API_URL;

// Don't add /api suffix since backend routes are already registered with /api prefix
export const API_BASE_URL = cleanApiUrl;

// Railway deployment URL (update this with your actual Railway URL)
export const RAILWAY_API_URL = 'https://full-stack-recipe-production.up.railway.app';

// Use Railway URL in production, fallback to localhost for development
export const getApiUrl = () => {
  if (import.meta.env.PROD) {
    return RAILWAY_API_URL;
  }
  return cleanApiUrl;
};