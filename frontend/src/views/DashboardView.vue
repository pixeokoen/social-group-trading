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
      
      <!-- Trading Overview -->
      <div class="mt-8 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-5">
        <!-- Total Trades -->
        <div class="bg-white overflow-hidden shadow rounded-lg">
          <div class="px-4 py-5 sm:p-6">
            <dt class="text-sm font-medium text-gray-500 truncate">Total Trades</dt>
            <dd class="mt-1 text-3xl font-semibold text-gray-900">{{ analytics.total_trades || 0 }}</dd>
            <dd class="mt-1 text-sm text-gray-500">
              {{ analytics.open_trades || 0 }} open, {{ analytics.pending_trades || 0 }} pending
            </dd>
          </div>
        </div>
        
        <!-- Win Rate -->
        <div class="bg-white overflow-hidden shadow rounded-lg">
          <div class="px-4 py-5 sm:p-6">
            <dt class="text-sm font-medium text-gray-500 truncate">Win Rate</dt>
            <dd class="mt-1 text-3xl font-semibold text-gray-900">{{ formatPercentage(analytics.win_rate) }}</dd>
            <dd class="mt-1 text-sm text-gray-500">
              {{ analytics.winning_trades || 0 }}W / {{ analytics.losing_trades || 0 }}L
            </dd>
          </div>
        </div>
        
        <!-- Realized P&L -->
        <div class="bg-white overflow-hidden shadow rounded-lg">
          <div class="px-4 py-5 sm:p-6">
            <dt class="text-sm font-medium text-gray-500 truncate">Realized P&L</dt>
            <dd :class="[
              'mt-1 text-3xl font-semibold',
              analytics.realized_pnl >= 0 ? 'text-green-600' : 'text-red-600'
            ]">
              ${{ formatNumber(analytics.realized_pnl) }}
            </dd>
            <dd class="mt-1 text-sm text-gray-500">
              Last updated: {{ analytics.realized_pnl_updated_at ? new Date(analytics.realized_pnl_updated_at).toLocaleString() : 'Never' }}
            </dd>
          </div>
        </div>
        
        <!-- Floating P&L -->
        <div class="bg-white overflow-hidden shadow rounded-lg">
          <div class="px-4 py-5 sm:p-6">
            <dt class="text-sm font-medium text-gray-500 truncate">Floating P&L</dt>
            <dd :class="[
              'mt-1 text-3xl font-semibold',
              analytics.total_floating_pnl >= 0 ? 'text-green-600' : 'text-red-600'
            ]">
              {{ analytics.total_floating_pnl < 0 ? '-' : '' }}${{ formatNumber(Math.abs(analytics.total_floating_pnl)) }}
            </dd>
            <dd class="mt-1 text-sm text-gray-500">
              Open positions
            </dd>
          </div>
        </div>
        
        <!-- Pending Signals -->
        <div class="bg-white overflow-hidden shadow rounded-lg">
          <div class="px-4 py-5 sm:p-6">
            <dt class="text-sm font-medium text-gray-500 truncate">Pending Signals</dt>
            <dd class="mt-1 text-3xl font-semibold text-yellow-600">{{ analytics.pending_signals || 0 }}</dd>
            <dd class="mt-1 text-sm text-gray-500">
              Waiting for approval
            </dd>
          </div>
        </div>
      </div>
      
      <!-- Signal Statistics -->
      <div class="mt-8 grid grid-cols-1 gap-5 sm:grid-cols-3">
        <div class="bg-white overflow-hidden shadow rounded-lg">
          <div class="px-4 py-5 sm:p-6">
            <dt class="text-sm font-medium text-gray-500 truncate">Total Signals</dt>
            <dd class="mt-1 text-2xl font-semibold text-gray-900">{{ analytics.total_signals || 0 }}</dd>
          </div>
        </div>
        
        <div class="bg-white overflow-hidden shadow rounded-lg">
          <div class="px-4 py-5 sm:p-6">
            <dt class="text-sm font-medium text-gray-500 truncate">Approved</dt>
            <dd class="mt-1 text-2xl font-semibold text-green-600">{{ analytics.approved_signals || 0 }}</dd>
          </div>
        </div>
        
        <div class="bg-white overflow-hidden shadow rounded-lg">
          <div class="px-4 py-5 sm:p-6">
            <dt class="text-sm font-medium text-gray-500 truncate">Executed</dt>
            <dd class="mt-1 text-2xl font-semibold text-blue-600">{{ analytics.executed_signals || 0 }}</dd>
          </div>
        </div>
      </div>

      <!-- Recent Signals -->
      <div class="mt-8">
        <h2 class="text-lg leading-6 font-medium text-gray-900 mb-4">Recent Signals</h2>
        <SignalList :signals="recentSignals" @execute="executeSignal" />
      </div>

      <!-- Recent Trades -->
      <div class="mt-8">
        <h2 class="text-lg leading-6 font-medium text-gray-900 mb-4">Recent Trades</h2>
        <div v-if="recentTrades.length > 0">
          <TradeList :trades="recentTrades" @close="openCloseTradeModal" />
        </div>
        <div v-else class="bg-white shadow rounded-lg p-6 text-center text-gray-500">
          No trades yet for this account
        </div>
      </div>
    </div>
    
    <!-- Order Confirmation Modal for closing trades -->
    <OrderConfirmModal
      :signal="selectedTrade"
      :is-open="showCloseModal"
      @close="closeModal"
      @executed="onTradeExecuted"
    />

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
  total_floating_pnl: number
  
  // Signal statistics
  total_signals: number
  pending_signals: number
  approved_signals: number
  rejected_signals: number
  executed_signals: number
  
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
  total_floating_pnl: 0,
  
  // Signal statistics
  total_signals: 0,
  pending_signals: 0,
  approved_signals: 0,
  rejected_signals: 0,
  executed_signals: 0,
  
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