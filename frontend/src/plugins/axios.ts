import axios from 'axios'
import { useAuthStore } from '@/stores/auth'
import { useErrorStore } from '@/stores/error'
import router from '@/router'

// In development, use relative URLs to work with Vite proxy
// In production, use the full API URL
const isDevelopment = import.meta.env.DEV
const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Set base URL - use empty string in development to use Vite proxy
axios.defaults.baseURL = isDevelopment ? '' : apiUrl

// Request interceptor to add auth token
axios.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore()
    if (authStore.token) {
      config.headers.Authorization = `Bearer ${authStore.token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor to handle errors
axios.interceptors.response.use(
  (response) => response,
  (error) => {
    const errorStore = useErrorStore()
    
    if (error.response) {
      // Server responded with error status
      const status = error.response.status
      const data = error.response.data
      
      if (status === 401) {
        // Unauthorized - clear auth and redirect to login
        const authStore = useAuthStore()
        authStore.logout()
        router.push('/login')
        errorStore.addError('Session expired. Please login again.')
      } else if (status === 403) {
        // Forbidden
        errorStore.addError('Access denied. Please check your API credentials.', data)
      } else if (status === 404) {
        // Not found
        errorStore.addError('Resource not found.', data)
      } else if (status >= 500) {
        // Server error
        errorStore.addError('Server error. Please try again later.', data)
      } else {
        // Other errors
        const message = data?.detail || data?.message || 'An error occurred'
        errorStore.addError(message, data)
      }
    } else if (error.request) {
      // Request made but no response
      errorStore.addError('Network error. Please check your connection.')
    } else {
      // Something else happened
      errorStore.addError('An unexpected error occurred.', error.message)
    }
    
    return Promise.reject(error)
  }
)

export default axios 