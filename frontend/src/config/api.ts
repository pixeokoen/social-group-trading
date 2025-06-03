// API Configuration
export const API_BASE_URL = import.meta.env.VITE_API_URL || ''

// Helper to get full API URL for external use (like webhook URLs)
export const getFullApiUrl = () => {
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL
  }
  // In development without explicit API URL, assume localhost
  if (import.meta.env.DEV) {
    return 'http://localhost:8000'
  }
  // In production, use the current origin
  return window.location.origin
}

// For production, the API URL should be set via environment variable
// In Render, set VITE_API_URL to your backend service URL 