import { defineStore } from 'pinia'
import axios from '@/plugins/axios'
import { useErrorStore } from '@/stores/error'

interface Account {
  id: number
  name: string
  account_type: 'paper' | 'live'
  broker: string
  is_active: boolean
  is_default: boolean
  created_at: string
}

export const useAccountStore = defineStore('account', {
  state: () => ({
    activeAccount: null as Account | null,
    accounts: [] as Account[],
    accountInfo: null as any,
    loading: false,
    error: null as string | null
  }),

  getters: {
    activeAccountId(): number | null {
      return this.activeAccount?.id || null
    },
    
    activeAccountName(): string {
      return this.activeAccount?.name || 'No Account'
    },
    
    activeAccountType(): string {
      return this.activeAccount?.account_type || ''
    },
    
    hasActiveAccount(): boolean {
      return !!this.activeAccount
    }
  },

  actions: {
    async fetchAccounts() {
      try {
        const response = await axios.get('/api/accounts')
        this.accounts = response.data
      } catch (error) {
        console.error('Failed to fetch accounts:', error)
      }
    },

    async fetchActiveAccount() {
      try {
        const response = await axios.get('/api/accounts/active')
        if (response.data) {
          this.activeAccount = response.data
        }
      } catch (error) {
        console.error('Failed to fetch active account:', error)
      }
    },

    async activateAccount(accountId: number) {
      try {
        await axios.post(`/api/accounts/${accountId}/activate`)
        this.activeAccount = this.accounts.find(a => a.id === accountId) || null
      } catch (error) {
        console.error('Failed to activate account:', error)
      }
    },

    async fetchAccountInfo() {
      const errorStore = useErrorStore()
      
      if (!this.activeAccount) {
        errorStore.addWarning('No active account selected')
        return
      }

      this.loading = true
      this.error = null
      
      try {
        const response = await axios.get(`/api/accounts/${this.activeAccount.id}/info`)
        this.accountInfo = response.data
        
        // Check if account info is empty (which is the issue with live accounts)
        if (response.data && Object.keys(response.data).length === 0) {
          errorStore.addError('Account info returned empty. This may indicate an API credential issue.')
        }
      } catch (error: any) {
        this.error = error.response?.data?.detail || 'Failed to fetch account info'
        
        // More specific error handling for common issues
        if (error.response?.status === 403) {
          errorStore.addError('API credentials rejected by Alpaca. Please verify your API key and secret.')
        } else if (error.response?.data?.detail) {
          errorStore.addError(`Account info error: ${error.response.data.detail}`)
        }
        
        console.error('Failed to fetch account info:', error)
      } finally {
        this.loading = false
      }
    },
    
    clearActiveAccount() {
      this.activeAccount = null
    }
  }
}) 