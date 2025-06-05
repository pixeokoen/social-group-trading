<template>
  <div class="min-h-screen bg-gray-50 py-8">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="mb-8">
        <h1 class="text-3xl font-bold text-gray-900">Trade Monitoring</h1>
        <p class="mt-2 text-gray-600">Monitor active take profit and stop loss levels</p>
      </div>

      <!-- Summary Cards -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div class="bg-white overflow-hidden shadow rounded-lg">
          <div class="p-5">
            <div class="flex items-center">
              <div class="flex-shrink-0">
                <svg class="h-6 w-6 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"></path>
                </svg>
              </div>
              <div class="ml-5 w-0 flex-1">
                <dl>
                  <dt class="text-sm font-medium text-gray-500 truncate">Active Take Profit Levels</dt>
                  <dd class="text-lg font-medium text-gray-900">{{ monitoringData?.total_tp_levels || 0 }}</dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div class="bg-white overflow-hidden shadow rounded-lg">
          <div class="p-5">
            <div class="flex items-center">
              <div class="flex-shrink-0">
                <svg class="h-6 w-6 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6"></path>
                </svg>
              </div>
              <div class="ml-5 w-0 flex-1">
                <dl>
                  <dt class="text-sm font-medium text-gray-500 truncate">Active Stop Loss Levels</dt>
                  <dd class="text-lg font-medium text-gray-900">{{ monitoringData?.total_sl_levels || 0 }}</dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div class="bg-white overflow-hidden shadow rounded-lg">
          <div class="p-5">
            <div class="flex items-center">
              <div class="flex-shrink-0">
                <svg class="h-6 w-6 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
                </svg>
              </div>
              <div class="ml-5 w-0 flex-1">
                <dl>
                  <dt class="text-sm font-medium text-gray-500 truncate">Total Symbols</dt>
                  <dd class="text-lg font-medium text-gray-900">{{ uniqueSymbols.length }}</dd>
                </dl>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Take Profit Levels -->
      <div class="bg-white shadow overflow-hidden sm:rounded-md mb-8">
        <div class="px-4 py-5 sm:px-6">
          <h3 class="text-lg leading-6 font-medium text-gray-900">Take Profit Levels</h3>
          <p class="mt-1 max-w-2xl text-sm text-gray-500">Active take profit orders waiting to be executed</p>
        </div>
        <div class="border-t border-gray-200">
          <div v-if="loading" class="p-6 text-center">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            <p class="mt-2 text-gray-500">Loading monitoring data...</p>
          </div>
          <div v-else-if="monitoringData?.take_profit_levels?.length === 0" class="p-6 text-center text-gray-500">
            No active take profit levels
          </div>
          <div v-else class="overflow-x-auto">
            <table class="min-w-full divide-y divide-gray-200">
              <thead class="bg-gray-50">
                <tr>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Symbol</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Level</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Price</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Percentage</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Shares</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                </tr>
              </thead>
              <tbody class="bg-white divide-y divide-gray-200">
                <tr v-for="level in monitoringData?.take_profit_levels" :key="level.id">
                  <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {{ level.symbol }}
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    Level {{ level.level_number }}
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    ${{ level.price.toFixed(2) }}
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {{ level.percentage.toFixed(1) }}%
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {{ level.shares_quantity.toFixed(4) }}
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap">
                    <span class="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-yellow-100 text-yellow-800">
                      {{ level.status }}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- Stop Loss Levels -->
      <div class="bg-white shadow overflow-hidden sm:rounded-md">
        <div class="px-4 py-5 sm:px-6">
          <h3 class="text-lg leading-6 font-medium text-gray-900">Stop Loss Levels</h3>
          <p class="mt-1 max-w-2xl text-sm text-gray-500">Active stop loss orders for position protection</p>
        </div>
        <div class="border-t border-gray-200">
          <div v-if="monitoringData?.stop_loss_levels?.length === 0" class="p-6 text-center text-gray-500">
            No active stop loss levels
          </div>
          <div v-else class="overflow-x-auto">
            <table class="min-w-full divide-y divide-gray-200">
              <thead class="bg-gray-50">
                <tr>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Symbol</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Price</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Remaining Shares</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                </tr>
              </thead>
              <tbody class="bg-white divide-y divide-gray-200">
                <tr v-for="level in monitoringData?.stop_loss_levels" :key="level.id">
                  <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {{ level.symbol }}
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    ${{ level.price.toFixed(2) }}
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {{ level.remaining_shares.toFixed(4) }}
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap">
                    <span class="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">
                      {{ level.status }}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import axios from '@/plugins/axios'

interface TakeProfitLevel {
  id: number
  trade_id: number
  level_number: number
  price: number
  percentage: number
  shares_quantity: number
  status: string
  symbol: string
  action: string
}

interface StopLossLevel {
  id: number
  trade_id: number
  price: number
  status: string
  symbol: string
  action: string
  remaining_shares: number
}

interface MonitoringData {
  take_profit_levels: TakeProfitLevel[]
  stop_loss_levels: StopLossLevel[]
  total_tp_levels: number
  total_sl_levels: number
}

const monitoringData = ref<MonitoringData | null>(null)
const loading = ref(true)

const uniqueSymbols = computed(() => {
  if (!monitoringData.value) return []
  
  const symbols = new Set<string>()
  monitoringData.value.take_profit_levels.forEach(level => symbols.add(level.symbol))
  monitoringData.value.stop_loss_levels.forEach(level => symbols.add(level.symbol))
  
  return Array.from(symbols)
})

const fetchMonitoringData = async () => {
  try {
    loading.value = true
    const response = await axios.get('/api/monitoring/levels')
    monitoringData.value = response.data
  } catch (error) {
    console.error('Error fetching monitoring data:', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchMonitoringData()
  
  // Auto-refresh every 30 seconds
  setInterval(fetchMonitoringData, 30000)
})
</script> 