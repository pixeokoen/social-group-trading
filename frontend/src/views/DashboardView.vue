<template>
  <div class="py-6">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="md:flex md:items-center md:justify-between mb-8">
        <h1 class="text-2xl font-semibold text-gray-900">Dashboard</h1>
        <div class="mt-4 flex space-x-3 md:mt-0 items-center">
          <button
            @click="syncData"
            :disabled="syncing"
            class="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50"
          >
            <svg 
              :class="['mr-2 h-4 w-4', syncing ? 'animate-spin' : '']" 
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
            </svg>
            {{ syncing ? 'Syncing...' : 'Sync Dashboard' }}
          </button>
          <!-- Log button -->
          <button
            @click="openSyncLogModal"
            class="ml-2 p-2 rounded-md border border-gray-300 bg-white hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
            title="Show last sync log"
          >
            <svg class="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
              <rect x="3" y="3" width="18" height="18" rx="2" ry="2" stroke="currentColor" stroke-width="2" fill="none" />
            </svg>
          </button>
          <span v-if="lastSync" class="text-sm text-gray-500 self-center">
            Last sync: {{ formatTime(lastSync) }}
          </span>
        </div>
      </div>
    </div>
    
    <div class="max-w-7xl mx-auto px-4 sm:px-6 md:px-8">
      <!-- Account Info -->
      <div class="mt-4 bg-blue-50 border-l-4 border-blue-400 p-4 rounded-md">
        <div class="flex">
          <div class="flex-shrink-0">
            <svg class="h-5 w-5 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
            </svg>
          </div>
          <div class="ml-3">
            <p class="text-sm text-blue-700">
              Active Account: <strong>{{ analytics.active_account || 'None' }}</strong> 
              ({{ analytics.account_type || 'N/A' }})
            </p>
          </div>
        </div>
      </div>
      
      <!-- Hero Metrics Section -->
      <div class="mt-10 relative">
        <!-- Background element -->
        <div class="absolute inset-0 bg-gradient-to-br from-slate-50 to-gray-100 rounded-xl transform rotate-1 opacity-40"></div>
        <div class="relative bg-white rounded-xl p-6 shadow-xl border border-gray-200/50">
          
          <!-- Core Metrics Grid -->
          <div class="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
            
            <!-- Total Trades -->
            <div class="group relative bg-gradient-to-br from-slate-50 to-slate-100 rounded-lg p-5 hover:shadow-md transition-all duration-200 border border-slate-200">
              <div class="flex items-center mb-3">
                <div class="p-2 bg-slate-600 rounded-md mr-3">
                  <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
                  </svg>
                </div>
                <dt class="text-sm font-semibold text-slate-600 uppercase tracking-wide">Total Trades</dt>
              </div>
              <dd class="text-2xl font-bold text-slate-900 mb-1">{{ analytics.total_trades || 0 }}</dd>
              <dd class="text-sm text-slate-500 font-medium">
                {{ analytics.open_trades || 0 }} open · {{ analytics.pending_trades || 0 }} pending
              </dd>
            </div>
            
            <!-- Win Rate -->
            <div class="group relative bg-gradient-to-br from-emerald-50 to-teal-100 rounded-lg p-5 hover:shadow-md transition-all duration-200 border border-emerald-200">
              <div class="flex items-center mb-3">
                <div class="p-2 bg-emerald-600 rounded-md mr-3">
                  <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                  </svg>
                </div>
                <dt class="text-sm font-semibold text-emerald-700 uppercase tracking-wide">Win Rate</dt>
              </div>
              <dd class="text-2xl font-bold text-emerald-900 mb-1">{{ formatPercentage(analytics.win_rate) }}</dd>
              <dd class="text-sm text-emerald-600 font-medium">
                {{ analytics.winning_trades || 0 }}W · {{ analytics.losing_trades || 0 }}L
              </dd>
            </div>
            
            <!-- Realized P&L -->
            <div :class="[
              'group relative rounded-lg p-5 hover:shadow-md transition-all duration-200 border',
              analytics.realized_pnl >= 0 
                ? 'bg-gradient-to-br from-green-50 to-emerald-100 border-green-200' 
                : 'bg-gradient-to-br from-red-50 to-rose-100 border-red-200'
            ]">
              <div class="flex items-center mb-3">
                <div :class="[
                  'p-2 rounded-md mr-3',
                  analytics.realized_pnl >= 0 ? 'bg-green-600' : 'bg-red-600'
                ]">
                  <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1"></path>
                  </svg>
                </div>
                <dt :class="[
                  'text-sm font-semibold uppercase tracking-wide',
                  analytics.realized_pnl >= 0 ? 'text-green-700' : 'text-red-700'
                ]">Realized P&L</dt>
              </div>
              <dd :class="[
                'text-2xl font-bold mb-1',
                analytics.realized_pnl >= 0 ? 'text-green-900' : 'text-red-900'
              ]">
                ${{ formatNumber(analytics.realized_pnl) }}
              </dd>
              <dd :class="[
                'text-sm font-medium',
                analytics.realized_pnl >= 0 ? 'text-green-600' : 'text-red-600'
              ]">
                Closed positions
              </dd>
            </div>
            
            <!-- Floating P&L -->
            <div :class="[
              'group relative rounded-lg p-5 hover:shadow-md transition-all duration-200 border',
              analytics.floating_pnl >= 0 
                ? 'bg-gradient-to-br from-blue-50 to-indigo-100 border-blue-200' 
                : 'bg-gradient-to-br from-orange-50 to-red-100 border-orange-200'
            ]">
              <div class="flex items-center mb-3">
                <div :class="[
                  'p-2 rounded-md mr-3',
                  analytics.floating_pnl >= 0 ? 'bg-blue-600' : 'bg-orange-600'
                ]">
                  <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"></path>
                  </svg>
                </div>
                <dt :class="[
                  'text-sm font-semibold uppercase tracking-wide',
                  analytics.floating_pnl >= 0 ? 'text-blue-700' : 'text-orange-700'
                ]">Floating P&L</dt>
              </div>
              <dd :class="[
                'text-2xl font-bold mb-1',
                analytics.floating_pnl >= 0 ? 'text-blue-900' : 'text-orange-900'
              ]">
                {{ isNaN(analytics.floating_pnl) ? '$0.00' : (analytics.floating_pnl < 0 ? '-' : '') + '$' + formatNumber(Math.abs(analytics.floating_pnl || 0)) }}
              </dd>
              <dd :class="[
                'text-sm font-medium',
                analytics.floating_pnl >= 0 ? 'text-blue-600' : 'text-orange-600'
              ]">
                Open positions
              </dd>
            </div>
            
          </div>
        </div>
      </div>
    </div>

    <!-- Sync Log Modal -->
    <div v-if="showSyncLogModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-40">
      <div class="bg-white rounded-lg shadow-lg max-w-lg w-full p-6 relative">
        <button @click="closeSyncLogModal" class="absolute top-2 right-2 text-gray-400 hover:text-gray-600">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
        <h2 class="text-lg font-semibold mb-4">Last Sync Log</h2>
        <div class="space-y-2">
          <template v-for="(row, idx) in formatSyncLog" :key="idx">
            <div v-if="row.type === 'section'" class="font-semibold text-gray-700 mt-2">{{ row.label }}</div>
            <div v-else-if="row.type === 'error'" class="text-red-600 font-semibold">{{ row.label }}: {{ row.value }}</div>
            <div v-else class="flex justify-between text-sm">
              <span class="text-gray-500">{{ row.label }}</span>
              <span class="font-mono">{{ row.value }}</span>
            </div>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import axios from '@/plugins/axios'
import SignalList from '@/components/SignalList.vue'
import TradeList from '@/components/TradeList.vue'
import OrderConfirmModal from '@/components/OrderConfirmModal.vue'

interface Trade {
  id: number
  symbol: string
  action: 'BUY' | 'SELL'
  quantity: number
  entry_price?: number
  exit_price?: number
  current_price?: number
  floating_pnl?: number
  pnl?: number
  status: 'pending' | 'open' | 'closed' | 'cancelled'
  close_reason?: string
}

interface Analytics {
  // Trade statistics
  total_trades: number
  open_trades: number
  pending_trades: number
  winning_trades: number
  losing_trades: number
  total_pnl: number
  avg_pnl: number
  win_rate: number
  floating_pnl: number  // Changed from total_floating_pnl
  
  // Account info
  active_account: string
  account_type: string
  
  // Recent trades
  recent_trades: any[]
  
  // New fields
  realized_pnl: number
  realized_pnl_updated_at?: string | null
}

const analytics = ref<Analytics>({
  // Trade statistics
  total_trades: 0,
  open_trades: 0,
  pending_trades: 0,
  winning_trades: 0,
  losing_trades: 0,
  total_pnl: 0,
  avg_pnl: 0,
  win_rate: 0,
  floating_pnl: 0,
  
  // Account info
  active_account: '',
  account_type: '',
  
  // Recent trades
  recent_trades: [],
  
  // New fields
  realized_pnl: 0,
  realized_pnl_updated_at: null
})

const recentSignals = ref([])
const recentTrades = ref<Trade[]>([])
const syncing = ref(false)
const lastSync = ref<Date | null>(null)
const showCloseModal = ref(false)
const selectedTrade = ref<any>(null)
const showSyncLogModal = ref(false)
const lastSyncLog = ref<any>({})
let syncInterval: any = null

const formatNumber = (num: number) => {
  if (num === null || num === undefined) return '0.00'
  return Math.abs(num).toFixed(2)
}

const formatPercentage = (num: number) => {
  if (num === null || num === undefined) return '0%'
  return `${num.toFixed(1)}%`
}

const formatTime = (date: Date) => {
  return new Intl.DateTimeFormat('en-US', {
    hour: 'numeric',
    minute: '2-digit',
    second: '2-digit'
  }).format(date)
}

const fetchData = async () => {
  try {
    const [analyticsRes, signalsRes] = await Promise.all([
      axios.get('/api/analytics'),
      axios.get('/api/signals?status=pending')  // Focus on pending signals
    ])
    
    analytics.value = analyticsRes.data
    recentSignals.value = signalsRes.data.slice(0, 5)
    
    // Use recent trades from analytics endpoint
    recentTrades.value = analyticsRes.data.recent_trades || []
    
    lastSync.value = new Date()
  } catch (error) {
    console.error('Error fetching dashboard data:', error)
  }
}

const syncData = async () => {
  syncing.value = true
  try {
    // Use the new consolidated sync-dashboard endpoint
    const result = await axios.post('/api/sync-dashboard')
    
    // Store sync log for modal
    lastSyncLog.value = result.data
    
    // Fetch updated data to refresh the UI
    await fetchData()
  } catch (error: any) {
    console.error('Error syncing dashboard:', error)
    lastSyncLog.value = { error: error?.message || error }
  } finally {
    syncing.value = false
  }
}

const executeSignal = async (signalId: number) => {
  try {
    await axios.post(`/api/trades/execute/${signalId}`)
    await fetchData() // Refresh data
  } catch (error) {
    console.error('Error executing signal:', error)
  }
}

const openCloseTradeModal = (trade: Trade) => {
  // Create a signal-like object for the modal
  // When closing a trade, we need to SELL if we bought, or BUY if we sold (short)
  const closeAction = trade.action === 'BUY' ? 'SELL' : 'BUY'
  
  selectedTrade.value = {
    id: 0, // 0 indicates this is a new order
    symbol: trade.symbol,
    action: closeAction,
    quantity: trade.quantity, // Default to closing the full position
    source: 'close_position',
    original_trade_id: trade.id // Store reference to the trade being closed
  }
  
  showCloseModal.value = true
}

const closeModal = () => {
  showCloseModal.value = false
  selectedTrade.value = null
}

const onTradeExecuted = async (result: any) => {
  alert(`Trade closed successfully! Order ID: ${result.broker_order_id}`)
  await fetchData() // Refresh dashboard data
}

const openSyncLogModal = () => {
  showSyncLogModal.value = true
}

const closeSyncLogModal = () => {
  showSyncLogModal.value = false
}

const formatSyncLog = computed<any[]>(() => {
  const log = lastSyncLog.value as any || {}
  if ((log as any).error) {
    return [
      { label: 'Error', value: (log as any).error, type: 'error' }
    ]
  }
  if (!(log as any).message && !(log as any).sync_results && !(log as any).pnl_results) {
    return [{ label: 'No log data', value: '', type: 'info' }]
  }
  const rows = []
  if ((log as any).message) rows.push({ label: 'Status', value: (log as any).message })
  if ((log as any).sync_results) {
    rows.push({ label: 'Orders Imported', value: (log as any).sync_results?.imported ?? '-' })
    rows.push({ label: 'Orders Updated', value: (log as any).sync_results?.updated ?? '-' })
    rows.push({ label: 'Total Orders', value: (log as any).sync_results?.total_orders ?? '-' })
  }
  if ((log as any).pnl_results) {
    rows.push({ label: 'Realized P&L', value: `$${Number((log as any).pnl_results?.total_realized_pnl ?? 0).toFixed(2)}` })
    rows.push({ label: 'Win Rate', value: `${Number((log as any).pnl_results?.win_rate ?? 0).toFixed(1)}%` })
    rows.push({ label: 'Winning Trades', value: (log as any).pnl_results?.winning_trades ?? '-' })
    rows.push({ label: 'Losing Trades', value: (log as any).pnl_results?.losing_trades ?? '-' })
    rows.push({ label: 'Closed Trades', value: (log as any).pnl_results?.total_closed_trades ?? '-' })
    if ((log as any).pnl_results?.last_updated) {
      rows.push({ label: 'Last Updated', value: new Date((log as any).pnl_results.last_updated).toLocaleString() })
    }
  }
  if ((log as any).symbol_pnls && typeof (log as any).symbol_pnls === 'object') {
    const symbols = Object.entries((log as any).symbol_pnls)
    if (symbols.length > 0) {
      rows.push({ label: 'P&L by Symbol', value: '', type: 'section' })
      for (const [symbol, pnl] of symbols) {
        rows.push({ label: `• ${symbol}`, value: `$${Number(pnl ?? 0).toFixed(2)}` })
      }
    }
  }
  return rows
})

onMounted(() => {
  fetchData()
  
  // Auto-sync every 30 seconds
  syncInterval = setInterval(() => {
    syncData()
  }, 30000)
  
  // Listen for account switches
  window.addEventListener('account-switched', fetchData)
})

onUnmounted(() => {
  if (syncInterval) {
    clearInterval(syncInterval)
  }
  
  // Clean up event listener
  window.removeEventListener('account-switched', fetchData)
})
</script> 