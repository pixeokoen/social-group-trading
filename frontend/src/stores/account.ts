import { defineStore } from 'pinia'
import axios from '@/plugins/axios'

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
    accounts: [] as Account[]
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
    async fetchActiveAccount() {
      try {
        const response = await axios.get('/api/accounts/active')
        this.activeAccount = response.data
      } catch (error: any) {
        console.error('Error fetching active account:', error)
        // If no active account, try to get the first account
        if (error.response?.status === 404) {
          await this.fetchAccounts()
          if (this.accounts.length > 0) {
            // Activate the first account
            await this.activateAccount(this.accounts[0].id)
          }
        }
      }
    },
    
    async fetchAccounts() {
      try {
        const response = await axios.get('/api/accounts')
        this.accounts = response.data
      } catch (error) {
        console.error('Error fetching accounts:', error)
      }
    },
    
    async activateAccount(accountId: number) {
      try {
        await axios.post(`/api/accounts/${accountId}/activate`)
        await this.fetchActiveAccount()
      } catch (error) {
        console.error('Error activating account:', error)
        throw error
      }
    },
    
    clearActiveAccount() {
      this.activeAccount = null
    }
  }
}) 