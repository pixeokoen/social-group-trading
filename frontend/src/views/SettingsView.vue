<template>
  <div class="py-6">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <h1 class="text-2xl font-semibold text-gray-900 mb-6">Settings</h1>
      
      <!-- Tabbed Interface -->
      <div class="bg-white shadow rounded-lg">
        <div class="border-b border-gray-200">
          <nav class="-mb-px flex">
            <button
              @click="activeTab = 'accounts'"
              :class="[
                activeTab === 'accounts'
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300',
                'py-4 px-6 border-b-2 font-medium text-sm transition-colors duration-200'
              ]"
            >
              Trading Accounts
            </button>
            <button
              @click="activeTab = 'sources'"
              :class="[
                activeTab === 'sources'
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300',
                'py-4 px-6 border-b-2 font-medium text-sm transition-colors duration-200'
              ]"
            >
              Signal Sources
            </button>
          </nav>
        </div>
        
        <div class="p-6">
          <!-- Trading Accounts Tab -->
          <div v-if="activeTab === 'accounts'">
            <div class="md:flex md:items-center md:justify-between mb-4">
              <div>
                <h2 class="text-lg font-medium text-gray-900">Trading Accounts</h2>
                <p class="mt-1 text-sm text-gray-600">
                  Manage your Alpaca trading accounts for paper and live trading.
                </p>
              </div>
              <button
                @click="showAddAccount = true"
                class="mt-3 md:mt-0 inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
              >
                Add Account
              </button>
            </div>
            
            <div class="space-y-4">
              <div
                v-for="account in accounts"
                :key="account.id"
                class="border rounded-lg p-4"
                :class="account.id === activeAccountId ? 'border-primary-500 bg-primary-50' : 'border-gray-200'"
              >
                <div class="flex items-start justify-between">
                  <div class="flex-1">
                    <div class="flex items-center space-x-3">
                      <h3 class="text-sm font-medium text-gray-900">{{ account.name }}</h3>
                      <span
                        :class="[
                          'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
                          account.account_type === 'paper' ? 'bg-yellow-100 text-yellow-800' : 'bg-green-100 text-green-800'
                        ]"
                      >
                        {{ account.account_type }}
                      </span>
                      <span
                        v-if="account.is_default"
                        class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                      >
                        Default
                      </span>
                      <span
                        v-if="account.id === activeAccountId"
                        class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-primary-100 text-primary-800"
                      >
                        Active
                      </span>
                    </div>
                    <p class="mt-1 text-sm text-gray-500">
                      Broker: {{ account.broker.toUpperCase() }} • Created: {{ new Date(account.created_at).toLocaleDateString() }}
                    </p>
                  </div>
                  <div class="flex items-center space-x-2 ml-4">
                    <button
                      v-if="account.id !== activeAccountId"
                      @click="activateAccount(account.id)"
                      class="text-sm text-primary-600 hover:text-primary-900"
                    >
                      Activate
                    </button>
                    <button
                      @click="editAccount(account)"
                      class="text-sm text-gray-600 hover:text-gray-900"
                    >
                      Edit
                    </button>
                    <button
                      v-if="accounts.length > 1"
                      @click="deleteAccount(account.id)"
                      class="text-sm text-red-600 hover:text-red-900"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <!-- Signal Sources Tab -->
          <div v-if="activeTab === 'sources'">
            <div class="md:flex md:items-center md:justify-between mb-4">
              <div>
                <h2 class="text-lg font-medium text-gray-900">Signal Sources</h2>
                <p class="mt-1 text-sm text-gray-600">
                  Configure which accounts receive signals from automated sources like WhatsApp groups.
                </p>
              </div>
              <button
                @click="showAddSource = true"
                class="mt-3 md:mt-0 inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
              >
                <svg class="-ml-1 mr-2 h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
                </svg>
                Add Source
              </button>
            </div>
            
            <!-- Sources List -->
            <div v-if="sources.length > 0" class="space-y-4">
              <div
                v-for="source in sources"
                :key="source.id"
                class="border rounded-lg p-4 hover:shadow-md transition-shadow"
              >
                <div class="flex justify-between items-start">
                  <div class="flex-1">
                    <div class="flex items-center space-x-2">
                      <h3 class="text-lg font-medium text-gray-900">{{ source.name }}</h3>
                      <span
                        :class="[
                          source.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800',
                          'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium'
                        ]"
                      >
                        {{ source.is_active ? 'Active' : 'Inactive' }}
                      </span>
                      <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                        {{ source.source_type.toUpperCase() }}
                      </span>
                    </div>
                    <p class="text-sm text-gray-600 mt-1">{{ source.description || 'No description' }}</p>
                    <p class="text-xs text-gray-500 mt-1">Identifier: {{ source.source_identifier }}</p>
                    
                    <!-- Webhook URL -->
                    <div class="mt-2">
                      <p class="text-sm font-medium text-gray-700">Webhook URL:</p>
                      <div class="flex items-center mt-1">
                        <code class="text-xs bg-gray-100 px-2 py-1 rounded flex-1 break-all">
                          {{ `${apiUrl}/api/webhook/whapi/${source.webhook_token}` }}
                        </code>
                        <button
                          @click="copyWebhookUrl(source)"
                          class="ml-2 p-1 text-gray-500 hover:text-gray-700"
                          title="Copy webhook URL"
                        >
                          <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3" />
                          </svg>
                        </button>
                      </div>
                    </div>
                    
                    <!-- Chat Filter -->
                    <div v-if="source.filter_config?.chat_id" class="mt-2">
                      <p class="text-xs text-gray-500">
                        <span class="font-medium">Chat ID Filter:</span> {{ source.filter_config.chat_id }}
                      </p>
                    </div>
                    
                    <!-- Linked Accounts -->
                    <div class="mt-3">
                      <p class="text-sm font-medium text-gray-700 mb-1">Routes signals to:</p>
                      <div class="flex flex-wrap gap-2">
                        <span
                          v-for="account in source.accounts"
                          :key="account.account_id"
                          class="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-medium bg-gray-100 text-gray-800"
                        >
                          {{ account.account_name }}
                          <span v-if="account.auto_approve" class="ml-1 text-green-600">
                            (Auto-approve)
                          </span>
                        </span>
                        <span v-if="source.accounts.length === 0" class="text-sm text-gray-500 italic">
                          No accounts linked
                        </span>
                      </div>
                    </div>
                  </div>
                  
                  <div class="flex items-center space-x-2 ml-4">
                    <button
                      @click="editSource(source)"
                      class="p-2 text-gray-400 hover:text-gray-600"
                      title="Edit source"
                    >
                      <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                      </svg>
                    </button>
                    <button
                      @click="deleteSource(source)"
                      class="p-2 text-red-400 hover:text-red-600"
                      title="Delete source"
                    >
                      <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  </div>
                </div>
              </div>
            </div>
            
            <div v-else class="text-center py-8 text-gray-500">
              No signal sources configured yet. Add a source to automatically route signals to your accounts.
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Add Account Modal -->
    <div v-if="showAddAccount" class="fixed z-10 inset-0 overflow-y-auto">
      <div class="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div class="fixed inset-0 transition-opacity" @click="showAddAccount = false">
          <div class="absolute inset-0 bg-gray-500 opacity-75"></div>
        </div>
        
        <div class="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
          <form @submit.prevent="createAccount">
            <div class="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
              <h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">Add Trading Account</h3>
              
              <div class="space-y-4">
                <div>
                  <label class="block text-sm font-medium text-gray-700">Account Name</label>
                  <input
                    v-model="newAccount.name"
                    type="text"
                    required
                    placeholder="My Alpaca Account"
                    class="mt-1 block w-full px-4 py-3 border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 text-base"
                  />
                </div>
                
                <div>
                  <label class="block text-sm font-medium text-gray-700">Account Type</label>
                  <select
                    v-model="newAccount.account_type"
                    required
                    class="mt-1 block w-full px-4 py-3 border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 text-base"
                  >
                    <option value="paper">Paper Trading</option>
                    <option value="live">Live Trading</option>
                  </select>
                </div>
                
                <div>
                  <label class="block text-sm font-medium text-gray-700">Broker</label>
                  <select
                    v-model="newAccount.broker"
                    required
                    class="mt-1 block w-full px-4 py-3 border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 text-base"
                  >
                    <option value="alpaca">Alpaca</option>
                  </select>
                </div>
                
                <div>
                  <label class="block text-sm font-medium text-gray-700">API Key</label>
                  <input
                    v-model="newAccount.api_key"
                    type="text"
                    required
                    placeholder="Your API Key"
                    class="mt-1 block w-full px-4 py-3 border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 text-base"
                  />
                </div>
                
                <div>
                  <label class="block text-sm font-medium text-gray-700">API Secret</label>
                  <input
                    v-model="newAccount.api_secret"
                    type="password"
                    required
                    placeholder="Your API Secret"
                    class="mt-1 block w-full px-4 py-3 border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 text-base"
                  />
                </div>
                
                <div>
                  <label class="block text-sm font-medium text-gray-700">
                    <input
                      v-model="newAccount.is_default"
                      type="checkbox"
                      class="mr-2"
                    />
                    Set as default account
                  </label>
                </div>
              </div>
            </div>
            
            <div class="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
              <button
                type="submit"
                :disabled="loading"
                class="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-primary-600 text-base font-medium text-white hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:ml-3 sm:w-auto sm:text-sm disabled:opacity-50"
              >
                {{ loading ? 'Creating...' : 'Create Account' }}
              </button>
              <button
                type="button"
                @click="showAddAccount = false"
                :disabled="loading"
                class="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm disabled:opacity-50"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- Add/Edit Source Modal -->
    <div v-if="showAddSource" class="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center p-4 z-50">
      <div class="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div class="px-6 py-4 border-b">
          <h3 class="text-lg font-medium text-gray-900">
            {{ editingSource ? 'Edit Signal Source' : 'Add Signal Source' }}
          </h3>
        </div>
        
        <form @submit.prevent="saveSource" class="p-6">
          <div class="space-y-6">
            <!-- Source Type -->
            <div>
              <label class="block text-sm font-medium text-gray-700">Source Type</label>
              <select
                v-model="sourceForm.source_type"
                :disabled="editingSource"
                required
                class="mt-1 block w-full px-4 py-3 border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 text-base"
              >
                <option value="whapi">WhatsApp (WHAPI)</option>
                <option value="telegram" disabled>Telegram (Coming Soon)</option>
                <option value="discord" disabled>Discord (Coming Soon)</option>
              </select>
            </div>
            
            <!-- Source Identifier -->
            <div>
              <label class="block text-sm font-medium text-gray-700">
                {{ sourceForm.source_type === 'whapi' ? 'Channel/Instance Name' : 'Source Identifier' }}
              </label>
              <div class="mt-1">
                <input
                  v-model="sourceForm.source_identifier"
                  type="text"
                  :disabled="editingSource"
                  placeholder="e.g., My Trading Phone"
                  class="block w-full px-4 py-3 border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 text-base"
                />
                <p class="mt-1 text-sm text-gray-500">
                  A descriptive name for this WhatsApp channel/phone number
                </p>
              </div>
            </div>
            
            <!-- Name -->
            <div>
              <label class="block text-sm font-medium text-gray-700">Display Name</label>
              <input
                v-model="sourceForm.name"
                type="text"
                required
                placeholder="e.g., Trading Signals WhatsApp Group"
                class="mt-1 block w-full px-4 py-3 border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 text-base"
              />
            </div>
            
            <!-- Description -->
            <div>
              <label class="block text-sm font-medium text-gray-700">Description (Optional)</label>
              <textarea
                v-model="sourceForm.description"
                rows="3"
                placeholder="Describe this signal source..."
                class="mt-1 block w-full px-4 py-3 border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 text-base"
              />
            </div>
            
            <!-- Chat ID Filter -->
            <div>
              <label class="block text-sm font-medium text-gray-700">Chat ID Filter (Optional)</label>
              <div class="mt-1">
                <input
                  v-model="sourceForm.filter_config.chat_id"
                  type="text"
                  placeholder="e.g., 120363123456789012@g.us"
                  class="block w-full px-4 py-3 border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 text-base"
                />
                <p class="mt-1 text-sm text-gray-500">
                  Only process messages from this specific WhatsApp chat/group. Leave empty to process all messages.
                </p>
              </div>
            </div>
            
            <!-- Account Selection -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">
                Route Signals to Accounts
              </label>
              <div class="space-y-2 max-h-48 overflow-y-auto border rounded-md p-3">
                <div v-if="accounts.length === 0" class="text-sm text-gray-500 text-center py-2">
                  No accounts available. Create an account first.
                </div>
                <label
                  v-for="account in accounts"
                  :key="account.id"
                  class="flex items-start p-2 hover:bg-gray-50 rounded cursor-pointer"
                >
                  <input
                    type="checkbox"
                    :value="account.id"
                    v-model="sourceForm.account_ids"
                    class="mt-1 h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                  />
                  <div class="ml-3 flex-1">
                    <div class="flex items-center justify-between">
                      <span class="text-sm font-medium text-gray-900">{{ account.name }}</span>
                      <span
                        :class="[
                          account.account_type === 'paper' ? 'bg-yellow-100 text-yellow-800' : 'bg-green-100 text-green-800',
                          'px-2 py-0.5 rounded-full text-xs font-medium'
                        ]"
                      >
                        {{ account.account_type }}
                      </span>
                    </div>
                    <!-- Auto-approve option -->
                    <label
                      v-if="sourceForm.account_ids.includes(account.id)"
                      class="flex items-center mt-1"
                    >
                      <input
                        type="checkbox"
                        v-model="sourceForm.auto_approve[account.id]"
                        class="h-3 w-3 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                      />
                      <span class="ml-2 text-xs text-gray-600">Auto-approve signals</span>
                    </label>
                  </div>
                </label>
              </div>
            </div>
            
            <!-- Active Status -->
            <div>
              <label class="flex items-center">
                <input
                  type="checkbox"
                  v-model="sourceForm.is_active"
                  class="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                />
                <span class="ml-2 text-sm font-medium text-gray-700">Active</span>
              </label>
              <p class="mt-1 text-sm text-gray-500">
                Only active sources will process incoming signals
              </p>
            </div>
          </div>
          
          <div class="mt-6 flex justify-end space-x-3">
            <button
              type="button"
              @click="cancelSourceEdit"
              class="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
            >
              Cancel
            </button>
            <button
              type="submit"
              :disabled="loading"
              class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50"
            >
              <span v-if="loading" class="mr-2">
                <svg class="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
                </svg>
              </span>
              {{ editingSource ? 'Update' : 'Create' }} Source
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import axios from '@/plugins/axios'
import { useAccountStore } from '@/stores/account'

interface Account {
  id: number
  name: string
  account_type: 'paper' | 'live'
  broker: string
  is_active: boolean
  is_default: boolean
  created_at: string
}

interface SignalSource {
  id: number
  source_type: string
  source_identifier: string
  name: string
  description?: string
  is_active: boolean
  accounts: Array<{
    account_id: number
    account_name: string
    account_type: string
    auto_approve: boolean
  }>
  webhook_token: string
  filter_config?: {
    chat_id: string
  }
}

const accountStore = useAccountStore()
const activeTab = ref('accounts')
const accounts = ref<Account[]>([])
const sources = ref<SignalSource[]>([])
const showAddAccount = ref(false)
const showAddSource = ref(false)
const editingSource = ref<SignalSource | null>(null)
const loading = ref(false)

const apiUrl = computed(() => import.meta.env.VITE_API_URL || 'http://localhost:8000')
const activeAccountId = computed(() => accountStore.activeAccount?.id)

const newAccount = ref({
  name: '',
  account_type: 'paper' as 'paper' | 'live',
  broker: 'alpaca',
  api_key: '',
  api_secret: '',
  is_default: false
})

const sourceForm = ref({
  source_type: 'whapi',
  source_identifier: '',
  name: '',
  description: '',
  is_active: true,
  account_ids: [] as number[],
  auto_approve: {} as Record<number, boolean>,
  filter_config: {
    chat_id: ''
  }
})

const fetchAccounts = async () => {
  try {
    const response = await axios.get('/api/accounts')
    accounts.value = response.data
  } catch (error) {
    console.error('Error fetching accounts:', error)
    alert('Failed to fetch accounts')
  }
}

const fetchSources = async () => {
  try {
    const response = await axios.get('/api/sources')
    sources.value = response.data
  } catch (error) {
    console.error('Error fetching sources:', error)
    alert('Failed to load signal sources')
  }
}

const createAccount = async () => {
  loading.value = true
  try {
    await axios.post('/api/accounts', newAccount.value)
    showAddAccount.value = false
    newAccount.value = {
      name: '',
      account_type: 'paper',
      broker: 'alpaca',
      api_key: '',
      api_secret: '',
      is_default: false
    }
    await fetchAccounts()
    await accountStore.fetchActiveAccount()
  } catch (error) {
    console.error('Error creating account:', error)
    alert('Failed to create account')
  } finally {
    loading.value = false
  }
}

const activateAccount = async (accountId: number) => {
  try {
    await axios.post(`/api/accounts/${accountId}/activate`)
    await accountStore.fetchActiveAccount()
    await fetchAccounts()
  } catch (error) {
    console.error('Error activating account:', error)
    alert('Failed to activate account')
  }
}

const editAccount = (account: Account) => {
  // TODO: Implement edit functionality
  alert('Edit functionality coming soon!')
}

const deleteAccount = async (accountId: number) => {
  if (!confirm('Are you sure you want to delete this account?')) {
    return
  }
  
  try {
    await axios.delete(`/api/accounts/${accountId}`)
    await fetchAccounts()
    if (accountId === activeAccountId.value) {
      await accountStore.fetchActiveAccount()
    }
  } catch (error: any) {
    console.error('Error deleting account:', error)
    alert(error.response?.data?.detail || 'Failed to delete account')
  }
}

const copyWebhookUrl = (source: SignalSource) => {
  const url = `${apiUrl.value}/api/webhook/whapi/${source.webhook_token}`
  navigator.clipboard.writeText(url).then(() => {
    alert('Webhook URL copied to clipboard!')
  }).catch(() => {
    alert('Failed to copy URL. Please copy manually.')
  })
}

const editSource = (source: SignalSource) => {
  editingSource.value = source
  sourceForm.value = {
    source_type: source.source_type,
    source_identifier: source.source_identifier,
    name: source.name,
    description: source.description || '',
    is_active: source.is_active,
    account_ids: source.accounts.map(a => a.account_id),
    auto_approve: source.accounts.reduce((acc, a) => {
      acc[a.account_id] = a.auto_approve
      return acc
    }, {} as Record<number, boolean>),
    filter_config: {
      chat_id: source.filter_config?.chat_id || ''
    }
  }
  showAddSource.value = true
}

const saveSource = async () => {
  loading.value = true
  
  try {
    const url = editingSource.value
      ? `/api/sources/${editingSource.value.id}`
      : '/api/sources'
    
    const method = editingSource.value ? 'put' : 'post'
    
    await axios[method](url, sourceForm.value)
    
    await fetchSources()
    cancelSourceEdit()
    alert(editingSource.value ? 'Source updated successfully' : 'Source created successfully')
  } catch (error: any) {
    console.error('Error saving source:', error)
    alert(error.response?.data?.detail || 'Failed to save source')
  } finally {
    loading.value = false
  }
}

const cancelSourceEdit = () => {
  showAddSource.value = false
  editingSource.value = null
  sourceForm.value = {
    source_type: 'whapi',
    source_identifier: '',
    name: '',
    description: '',
    is_active: true,
    account_ids: [],
    auto_approve: {},
    filter_config: {
      chat_id: ''
    }
  }
}

const deleteSource = async (source: SignalSource) => {
  if (!confirm(`Are you sure you want to delete "${source.name}"?`)) {
    return
  }
  
  try {
    await axios.delete(`/api/sources/${source.id}`)
    await fetchSources()
    alert('Source deleted successfully')
  } catch (error) {
    console.error('Error deleting source:', error)
    alert('Failed to delete source')
  }
}

onMounted(() => {
  fetchAccounts()
  fetchSources()
})
</script> 