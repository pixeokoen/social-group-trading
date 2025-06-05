<template>
  <div class="py-6">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="md:flex md:items-center md:justify-between">
        <h1 class="text-2xl font-semibold text-gray-900">Positions</h1>
        <div class="mt-4 flex space-x-3 md:mt-0">
          <button
            @click="syncPositions"
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
            {{ syncing ? 'Syncing...' : 'Sync Positions' }}
          </button>
          <span v-if="lastSync" class="text-sm text-gray-500 self-center">
            Last sync: {{ formatTime(lastSync) }}
          </span>
        </div>
      </div>
      
      <div class="mt-8">
        <!-- Mobile view -->
        <div class="sm:hidden">
          <div class="bg-white shadow overflow-hidden sm:rounded-md">
            <ul class="divide-y divide-gray-200">
              <li v-for="position in positions" :key="position.symbol" class="px-4 py-4">
                <div class="flex items-center justify-between">
                  <div class="flex items-center space-x-3">
                    <span class="font-medium text-gray-900">{{ position.symbol }}</span>
                    <span
                      :class="[
                        position.side === 'LONG' ? 'text-green-600' : 'text-red-600',
                        'text-sm font-medium'
                      ]"
                    >
                      {{ position.side }}
                    </span>
                  </div>
                  <button
                    v-if="position.side === 'LONG'"
                    @click="openClosePositionModal(position)"
                    class="inline-flex items-center px-3 py-1 border border-transparent text-sm rounded-md text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                  >
                    <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M16 11V7a4 4 0 00-8 0v4M5 11h14l-1.68 9.39A2 2 0 0115.34 22H8.66a2 2 0 01-1.98-1.61L5 11z" />
                    </svg>
                    Sell
                  </button>
                </div>
                <div class="mt-2 text-sm text-gray-500">
                  <div>{{ formatQuantity(position.quantity) }} @ ${{ formatPrice(position.avg_entry_price) }}</div>
                  <div>Current: ${{ formatPrice(position.current_price) }}</div>
                  <div>Value: ${{ formatPrice(position.market_value) }}</div>
                </div>
                <div class="mt-2 flex items-center justify-between">
                  <div>
                    <div>
                      <span
                        :class="position.unrealized_pnl >= 0 ? 'text-green-600' : 'text-red-600'"
                        class="text-sm font-medium"
                      >
                        {{ position.unrealized_pnl >= 0 ? '+' : '' }}${{ formatPrice(Math.abs(position.unrealized_pnl)) }}
                        ({{ position.unrealized_pnl_pct >= 0 ? '+' : '' }}{{ position.unrealized_pnl_pct.toFixed(2) }}%)
                      </span>
                      <span class="text-xs text-gray-400 ml-1">Total</span>
                    </div>
                    <div class="mt-1">
                      <span
                        :class="position.today_pnl >= 0 ? 'text-green-600' : 'text-red-600'"
                        class="text-sm"
                      >
                        {{ position.today_pnl >= 0 ? '+' : '' }}${{ formatPrice(Math.abs(position.today_pnl)) }}
                      </span>
                      <span class="text-xs text-gray-400 ml-1">Today</span>
                    </div>
                  </div>
                </div>
              </li>
            </ul>
          </div>
        </div>

        <!-- Desktop view -->
        <div class="hidden sm:block">
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
                          Side
                        </th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Quantity
                        </th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Avg Entry
                        </th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Current Price
                        </th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Market Value
                        </th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Unrealized P&L
                        </th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Today's P&L
                        </th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Actions
                        </th>
                      </tr>
                    </thead>
                    <tbody class="bg-white divide-y divide-gray-200">
                      <tr v-for="position in positions" :key="position.symbol">
                        <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {{ position.symbol }}
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm">
                          <span 
                            :class="[
                              position.side === 'LONG' ? 'text-green-600' : 'text-red-600',
                              'font-medium'
                            ]"
                          >
                            {{ position.side }}
                          </span>
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {{ formatQuantity(position.quantity) }}
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          ${{ formatPrice(position.avg_entry_price) }}
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          ${{ formatPrice(position.current_price) }}
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          ${{ formatPrice(position.market_value) }}
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm">
                          <div>
                            <span 
                              :class="position.unrealized_pnl >= 0 ? 'text-green-600' : 'text-red-600'"
                              class="font-medium"
                            >
                              {{ position.unrealized_pnl >= 0 ? '+' : '' }}${{ formatPrice(Math.abs(position.unrealized_pnl)) }}
                            </span>
                            <span 
                              :class="position.unrealized_pnl_pct >= 0 ? 'text-green-600' : 'text-red-600'"
                              class="text-xs ml-1"
                            >
                              ({{ position.unrealized_pnl_pct >= 0 ? '+' : '' }}{{ position.unrealized_pnl_pct.toFixed(2) }}%)
                            </span>
                          </div>
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm">
                          <div>
                            <span 
                              :class="position.today_pnl >= 0 ? 'text-green-600' : 'text-red-600'"
                              class="font-medium"
                            >
                              {{ position.today_pnl >= 0 ? '+' : '' }}${{ formatPrice(Math.abs(position.today_pnl)) }}
                            </span>
                            <span 
                              :class="position.today_pnl_pct >= 0 ? 'text-green-600' : 'text-red-600'"
                              class="text-xs ml-1"
                            >
                              ({{ position.today_pnl_pct >= 0 ? '+' : '' }}{{ position.today_pnl_pct.toFixed(2) }}%)
                            </span>
                          </div>
                        </td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          <button
                            v-if="position.side === 'LONG'"
                            @click="openClosePositionModal(position)"
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
                  <div v-if="positions.length === 0" class="text-center py-12">
                    <p class="text-gray-500">No open positions</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Order Confirmation Modal for closing positions -->
    <OrderConfirmModal
      :signal="selectedPosition"
      :is-open="showCloseModal"
      @close="closeModal"
      @executed="onPositionClosed"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import axios from '@/plugins/axios'
import OrderConfirmModal from '@/components/OrderConfirmModal.vue'

interface Position {
  symbol: string
  side: string
  quantity: number
  avg_entry_price: number
  current_price: number
  market_value: number
  cost_basis: number
  unrealized_pnl: number
  unrealized_pnl_pct: number
  today_pnl: number
  today_pnl_pct: number
  asset_class: string
  exchange: string
}

const positions = ref<Position[]>([])
const syncing = ref(false)
const lastSync = ref<Date | null>(null)
const showCloseModal = ref(false)
const selectedPosition = ref<any>(null)
let syncInterval: any = null

const formatQuantity = (quantity: number) => {
  return quantity === Math.floor(quantity) ? quantity.toString() : quantity.toFixed(4)
}

const formatPrice = (price: number) => {
  return price.toFixed(2)
}

const formatTime = (date: Date) => {
  return new Intl.DateTimeFormat('en-US', {
    hour: 'numeric',
    minute: '2-digit',
    second: '2-digit'
  }).format(date)
}

const fetchPositions = async () => {
  try {
    const response = await axios.get('/api/positions')
    positions.value = response.data
  } catch (error) {
    console.error('Error fetching positions:', error)
  }
}

const syncPositions = async () => {
  syncing.value = true
  try {
    const response = await axios.get('/api/positions/sync')
    console.log('Sync result:', response.data)
    lastSync.value = new Date()
    
    // Refresh positions after sync
    await fetchPositions()
    
    if (response.data.positions_count > 0) {
      console.log(`Synced ${response.data.positions_count} positions`)
    }
  } catch (error) {
    console.error('Error syncing positions:', error)
  } finally {
    syncing.value = false
  }
}

const openClosePositionModal = (position: Position) => {
  // Create a signal-like object for the modal
  selectedPosition.value = {
    id: 0, // 0 indicates this is a new order
    symbol: position.symbol,
    action: 'SELL', // Selling to close a long position
    quantity: position.quantity, // Default to closing the full position
    source: 'close_position',
    position_data: position // Store the position data for reference
  }
  
  showCloseModal.value = true
}

const closeModal = () => {
  showCloseModal.value = false
  selectedPosition.value = null
}

const onPositionClosed = async (result: any) => {
  alert(`Position closed successfully! Order ID: ${result.broker_order_id}`)
  await fetchPositions()
}

onMounted(() => {
  fetchPositions()
  
  // Sync positions every 30 seconds
  syncInterval = setInterval(() => {
    syncPositions()
  }, 30000)
  
  // Initial sync
  syncPositions()
  
  // Listen for account switches
  window.addEventListener('account-switched', fetchPositions)
})

onUnmounted(() => {
  if (syncInterval) {
    clearInterval(syncInterval)
  }
  
  // Clean up event listener
  window.removeEventListener('account-switched', fetchPositions)
})
</script> 