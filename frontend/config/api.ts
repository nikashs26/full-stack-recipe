// Render deployment URL
export const RENDER_API_URL = 'https://dietary-delight.onrender.com';

// Use Render URL for production (Netlify), localhost for development
export const getApiUrl = () => {
  if (import.meta.env.PROD) {
    // Check if we have a custom backend URL set
    if (import.meta.env.VITE_BACKEND_URL) {
      return import.meta.env.VITE_BACKEND_URL;
    }
    // Fallback to Render URL
    return RENDER_API_URL;
  }
  return 'http://localhost:5003';
};

// For backward compatibility, export the dynamic URL
export const API_BASE_URL = getApiUrl();

// Use Railway only for health checks and basic endpoints
export const getRailwayUrl = () => {
  return RAILWAY_API_URL;
};