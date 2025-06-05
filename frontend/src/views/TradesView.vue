<template>
  <div class="py-6">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="md:flex md:items-center md:justify-between">
        <h1 class="text-2xl font-semibold text-gray-900">Trades</h1>
        <div class="mt-4 flex space-x-3 md:mt-0">
          <button
            @click="showCreateTradeModal"
            class="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
          >
            <svg class="mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
            </svg>
            Create Trade
          </button>
          <button
            @click="syncTrades"
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
            {{ syncing ? 'Syncing...' : 'Sync with Broker' }}
          </button>
          <span v-if="lastSync" class="text-sm text-gray-500 self-center">
            Last sync: {{ formatTime(lastSync) }}
          </span>
          <span v-if="streamConnected" class="text-sm text-green-600 self-center flex items-center">
            <span class="inline-block w-2 h-2 bg-green-600 rounded-full mr-1 animate-pulse"></span>
            Real-time updates active
          </span>
        </div>
      </div>
      
      <!-- Trade notifications -->
      <div v-if="notifications.length > 0" class="mt-4">
        <div class="bg-blue-50 border-l-4 border-blue-400 p-4 rounded-md">
          <div class="flex">
            <div class="flex-shrink-0">
              <svg class="h-5 w-5 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
              </svg>
            </div>
            <div class="ml-3 flex-1">
              <p class="text-sm text-blue-700">
                {{ notifications[0].data.message }}
              </p>
            </div>
            <button @click="dismissNotifications" class="ml-auto flex-shrink-0">
              <svg class="h-5 w-5 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
              </svg>
            </button>
          </div>
        </div>
      </div>
      
      <div class="mt-8">
        <div class="flex flex-col">
          <div class="-my-2 overflow-x-auto sm:-mx-6 lg:-mx-8">
            <div class="py-2 align-middle inline-block min-w-full sm:px-6 lg:px-8">
              <div class="shadow overflow-hidden border-b border-gray-200 sm:rounded-lg">
                <table class="min-w-full divide-y divide-gray-200">
                  <thead class="bg-gray-50">
                    <tr>
                      <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Symbol
                      </th>
                      <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Action
                      </th>
                      <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Quantity
                      </th>
                      <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Entry Price
                      </th>
                      <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Current/Exit
                      </th>
                      <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        P&L
                      </th>
                      <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Status
                      </th>
                      <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody class="bg-white divide-y divide-gray-200">
                    <tr v-for="trade in trades" :key="trade.id" :class="{ 'bg-yellow-50': trade.justUpdated }">
                      <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {{ trade.symbol }}
                      </td>
                      <td class="px-6 py-4 whitespace-nowrap text-sm">
                        <span 
                          :class="[
                            trade.action === 'BUY' ? 'text-green-600' : 'text-red-600',
                            'font-medium'
                          ]"
                        >
                          {{ trade.action }}
                        </span>
                      </td>
                      <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {{ formatQuantity(trade.quantity) }}
                      </td>
                      <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        ${{ formatPrice(trade.entry_price || trade.broker_fill_price) }}
                      </td>
                      <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        <div v-if="trade.status === 'open' && trade.current_price">
                          ${{ formatPrice(trade.current_price) }}
                        </div>
                        <div v-else-if="trade.exit_price">
                          ${{ formatPrice(trade.exit_price) }}
                        </div>
                        <div v-else>
                          ${{ formatPrice(trade.current_price) }}
                        </div>
                      </td>
                      <td class="px-6 py-4 whitespace-nowrap text-sm">
                        <span 
                          v-if="trade.status === 'open' && trade.floating_pnl !== null && trade.floating_pnl !== undefined"
                          :class="trade.floating_pnl >= 0 ? 'text-green-600' : 'text-red-600'"
                        >
                          ${{ formatPrice(trade.floating_pnl) }}
                        </span>
                        <span 
                          v-else-if="trade.status === 'closed' && trade.pnl !== null && trade.pnl !== undefined"
                          :class="trade.pnl >= 0 ? 'text-green-600' : 'text-red-600'"
                        >
                          ${{ formatPrice(trade.pnl) }}
                        </span>
                        <span v-else class="text-gray-400">-</span>
                      </td>
                      <td class="px-6 py-4 whitespace-nowrap">
                        <span 
                          :class="[
                            'px-2 inline-flex text-xs leading-5 font-semibold rounded-full',
                            trade.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                            trade.status === 'open' ? 'bg-green-100 text-green-800' :
                            trade.status === 'closed' ? 'bg-gray-100 text-gray-800' :
                            'bg-red-100 text-red-800'
                          ]"
                        >
                          {{ trade.status }}
                        </span>
                      </td>
                      <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        <button
                          v-if="trade.status === 'open' && trade.action === 'BUY'"
                          @click="openCloseTradeModal(trade)"
                          class="inline-flex items-center px-3 py-1 border border-transparent text-sm rounded-md text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                        >
                          <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M16 11V7a4 4 0 00-8 0v4M5 11h14l-1.68 9.39A2 2 0 0115.34 22H8.66a2 2 0 01-1.98-1.61L5 11z" />
                          </svg>
                          Sell
                        </button>
                      </td>
                    </tr>
                  </tbody>
                </table>
                <div v-if="trades.length === 0" class="text-center py-12">
                  <p class="text-gray-500">No trades yet</p>
                </div>
              </div>
            </div>
          </div>
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
    
    <!-- Order Confirmation Modal for creating trades -->
    <OrderConfirmModal
      :signal="selectedTradeToCreate"
      :is-open="showCreateModal"
      @close="closeCreateModal"
      @executed="onTradeCreated"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import axios from '@/plugins/axios'
import OrderConfirmModal from '@/components/OrderConfirmModal.vue'

interface Trade {
  id: number
  symbol: string
  action: 'BUY' | 'SELL'
  quantity: number
  entry_price?: number
  broker_fill_price?: number
  exit_price?: number
  current_price?: number
  floating_pnl?: number
  pnl?: number
  status: string
  justUpdated?: boolean
}

interface Notification {
  id: number
  data: {
    message: string
    trade_id: number
    status: string
    fill_price?: number
    quantity?: number
    type: string
  }
}

const trades = ref<Trade[]>([])
const syncing = ref(false)
const lastSync = ref<Date | null>(null)
const notifications = ref<Notification[]>([])
const streamConnected = ref(false)
const showCloseModal = ref(false)
const selectedTrade = ref<any>(null)
const showCreateModal = ref(false)
const selectedTradeToCreate = ref<any>(null)
let syncInterval: any = null
let notificationInterval: any = null

const formatQuantity = (quantity: number | string) => {
  // Convert to number if it's a string
  const numQuantity = typeof quantity === 'string' ? parseFloat(quantity) : quantity
  if (isNaN(numQuantity)) return '0'
  return numQuantity === Math.floor(numQuantity) ? numQuantity.toString() : numQuantity.toFixed(4)
}

const formatPrice = (price: any) => {
  if (price === null || price === undefined) return 'N/A'
  // Convert to number if it's a string
  const numPrice = typeof price === 'string' ? parseFloat(price) : price
  return isNaN(numPrice) ? 'N/A' : numPrice.toFixed(2)
}

const formatTime = (date: Date) => {
  return new Intl.DateTimeFormat('en-US', {
    hour: 'numeric',
    minute: '2-digit',
    second: '2-digit'
  }).format(date)
}

const fetchTrades = async () => {
  try {
    const response = await axios.get('/api/trades')
    trades.value = response.data
  } catch (error) {
    console.error('Error fetching trades:', error)
  }
}

const syncTrades = async () => {
  syncing.value = true
  try {
    const response = await axios.get('/api/trades/sync')
    console.log('Sync result:', response.data)
    // Log the number of Alpaca orders and their IDs
    console.log('Alpaca orders fetched:', response.data.total_orders)
    console.log('Alpaca order IDs:', response.data.alpaca_order_ids)
    lastSync.value = new Date()
    
    // Refresh trades after sync
    await fetchTrades()
    
    if (response.data.trades_updated > 0) {
      console.log(`Synced ${response.data.trades_updated} trades with broker`)
    }
  } catch (error) {
    console.error('Error syncing trades:', error)
    // Only show alert for actual errors, not for successful syncs
    // alert('Failed to sync trades with broker')
  } finally {
    syncing.value = false  // Make sure to stop the spinner
  }
}

const checkNotifications = async () => {
  try {
    const response = await axios.get('/api/notifications/trades?unread_only=true')
    const newNotifications = response.data
    
    if (newNotifications.length > 0) {
      notifications.value = newNotifications
      streamConnected.value = true
      
      // Process each notification
      for (const notification of newNotifications) {
        const notifData = notification.data
        
        // Update trade in the list
        const tradeIndex = trades.value.findIndex(t => t.id === notifData.trade_id)
        if (tradeIndex !== -1) {
          // Update trade status and highlight it
          trades.value[tradeIndex] = {
            ...trades.value[tradeIndex],
            status: notifData.status,
            entry_price: notifData.fill_price || trades.value[tradeIndex].entry_price,
            quantity: notifData.quantity || trades.value[tradeIndex].quantity,
            justUpdated: true
          }
          
          // Remove highlight after 3 seconds
          setTimeout(() => {
            if (trades.value[tradeIndex]) {
              trades.value[tradeIndex].justUpdated = false
            }
          }, 3000)
        }
        
        // Mark notification as read
        try {
          await axios.post(`/api/notifications/trades/${notification.id}/read`)
        } catch (error) {
          console.error('Error marking notification as read:', error)
        }
      }
      
      // Refresh trades to get latest data
      if (newNotifications.some((n: Notification) => ['order_filled', 'order_partial_fill'].includes(n.data.type))) {
        await fetchTrades()
      }
      
      // Auto-dismiss notifications after 5 seconds
      setTimeout(() => {
        dismissNotifications()
      }, 5000)
    }
  } catch (error) {
    console.error('Error checking notifications:', error)
    streamConnected.value = false
  }
}

const dismissNotifications = () => {
  notifications.value = []
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
  await fetchTrades()
}

const showCreateTradeModal = () => {
  // Create a new trade object for the modal
  selectedTradeToCreate.value = {
    id: 0, // 0 indicates this is a new order
    symbol: '',
    action: 'BUY',
    quantity: 100, // Default quantity
    source: 'manual_create'
  }
  
  showCreateModal.value = true
}

const closeCreateModal = () => {
  showCreateModal.value = false
  selectedTradeToCreate.value = null
}

const onTradeCreated = async (result: any) => {
  alert(`Trade created successfully! Order ID: ${result.broker_order_id}`)
  await fetchTrades()
  closeCreateModal()
}

onMounted(() => {
  fetchTrades()
  
  // Check for notifications every 3 seconds
  notificationInterval = setInterval(() => {
    checkNotifications()
  }, 3000)
  
  // Fallback sync every 30 seconds
  syncInterval = setInterval(() => {
    syncTrades()
  }, 30000)
  
  // Initial sync
  syncTrades()
  
  // Check notifications immediately
  checkNotifications()
  
  // Listen for account switches
  window.addEventListener('account-switched', fetchTrades)
})

onUnmounted(() => {
  if (syncInterval) {
    clearInterval(syncInterval)
  }
  if (notificationInterval) {
    clearInterval(notificationInterval)
  }
  
  // Clean up event listener
  window.removeEventListener('account-switched', fetchTrades)
})
</script> 