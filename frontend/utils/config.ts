// API Configuration
export const API_CONFIG = {
  // Get the API base URL from environment variables
  API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  
  // Get the WebSocket URL from environment variables
  WS_URL: process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000',
  
  // Environment
  ENV: process.env.NEXT_PUBLIC_ENV || 'development',
  
  // Helper functions
  getApiUrl: (path: string) => {
    const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    return `${baseUrl}${path.startsWith('/') ? path : `/${path}`}`;
  },
  
  getWsUrl: (path: string) => {
    const baseUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';
    return `${baseUrl}${path.startsWith('/') ? path : `/${path}`}`;
  }
};

export default API_CONFIG;
