import { defineStore } from 'pinia'

interface ErrorMessage {
  id: number
  message: string
  type: 'error' | 'warning' | 'info'
  timestamp: Date
  details?: any
}

export const useErrorStore = defineStore('error', {
  state: () => ({
    errors: [] as ErrorMessage[],
    nextId: 1
  }),

  actions: {
    addError(message: string, details?: any) {
      const error: ErrorMessage = {
        id: this.nextId++,
        message,
        type: 'error',
        timestamp: new Date(),
        details
      }
      this.errors.push(error)
      
      // Auto-remove after 10 seconds
      setTimeout(() => {
        this.removeError(error.id)
      }, 10000)
    },

    addWarning(message: string, details?: any) {
      const warning: ErrorMessage = {
        id: this.nextId++,
        message,
        type: 'warning',
        timestamp: new Date(),
        details
      }
      this.errors.push(warning)
      
      // Auto-remove after 8 seconds
      setTimeout(() => {
        this.removeError(warning.id)
      }, 8000)
    },

    addInfo(message: string, details?: any) {
      const info: ErrorMessage = {
        id: this.nextId++,
        message,
        type: 'info',
        timestamp: new Date(),
        details
      }
      this.errors.push(info)
      
      // Auto-remove after 5 seconds
      setTimeout(() => {
        this.removeError(info.id)
      }, 5000)
    },

    removeError(id: number) {
      const index = this.errors.findIndex(e => e.id === id)
      if (index > -1) {
        this.errors.splice(index, 1)
      }
    },

    clearAll() {
      this.errors = []
    }
  }
}) 