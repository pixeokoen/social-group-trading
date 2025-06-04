<template>
  <div class="py-6">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="md:flex md:items-center md:justify-between mb-8">
        <h1 class="text-2xl font-semibold text-gray-900">Dashboard</h1>
        <div class="mt-4 flex space-x-3 md:mt-0">
          <button
            @click="recalculatePnL"
            :disabled="recalculating"
            class="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50"
          >
            <svg 
              :class="['mr-2 h-4 w-4', recalculating ? 'animate-spin' : '']" 
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
            </svg>
            {{ recalculating ? 'Recalculating...' : 'Recalculate P&L' }}
          </button>
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
        
        <!-- Total P&L -->
        <div class="bg-white overflow-hidden shadow rounded-lg">
          <div class="px-4 py-5 sm:p-6">
            <dt class="text-sm font-medium text-gray-500 truncate">Total P&L</dt>
            <dd :class="[
              'mt-1 text-3xl font-semibold',
              analytics.total_pnl >= 0 ? 'text-green-600' : 'text-red-600'
            ]">
              ${{ formatNumber(analytics.total_pnl) }}
            </dd>
            <dd class="mt-1 text-sm text-gray-500">
              Avg: ${{ formatNumber(analytics.avg_pnl) }}
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
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
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
  status: string
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
  recent_trades: []
})

const recentSignals = ref([])
const recentTrades = ref<Trade[]>([])
const syncing = ref(false)
const recalculating = ref(false)
const lastSync = ref<Date | null>(null)
const showCloseModal = ref(false)
const selectedTrade = ref<any>(null)
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
    // First sync trades with broker
    await axios.get('/api/trades/sync')
    
    // Then fetch updated data
    await fetchData()
    
    console.log('Dashboard synced successfully')
  } catch (error) {
    console.error('Error syncing dashboard:', error)
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

const recalculatePnL = async () => {
  recalculating.value = true
  try {
    await axios.post('/api/trades/recalculate-pnl')
    await fetchData()
  } catch (error) {
    console.error('Error recalculating P&L:', error)
  } finally {
    recalculating.value = false
  }
}

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