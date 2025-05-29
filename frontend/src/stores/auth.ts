import { defineStore } from 'pinia'
import axios from '@/plugins/axios'
import router from '@/router'
import { useAccountStore } from './account'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null as any,
    token: localStorage.getItem('token')
  }),

  getters: {
    isAuthenticated(): boolean {
      return !!this.token
    }
  },

  actions: {
    async login(username: string, password: string) {
      try {
        const response = await axios.post('/api/auth/login', {
          username,
          password
        })
        this.token = response.data.access_token
        if (this.token) {
          localStorage.setItem('token', this.token)
          axios.defaults.headers.common['Authorization'] = `Bearer ${this.token}`
        }
        
        // Fetch account data after login
        const accountStore = useAccountStore()
        await accountStore.fetchActiveAccount()
        await accountStore.fetchAccounts()
        
        router.push('/')
      } catch (error) {
        console.error('Login failed:', error)
        throw error
      }
    },

    logout() {
      this.user = null
      this.token = null
      localStorage.removeItem('token')
      delete axios.defaults.headers.common['Authorization']
    }
  }
}) 