<template>
  <div class="bg-white shadow overflow-hidden sm:rounded-lg">
    <!-- Mobile view -->
    <div class="sm:hidden">
      <ul class="divide-y divide-gray-200">
        <li v-for="trade in trades" :key="trade.id" class="px-4 py-4">
          <div class="flex items-center justify-between">
            <div class="flex items-center space-x-3">
              <span
                :class="[
                  trade.action === 'BUY' ? 'text-green-600' : 'text-red-600',
                  'font-medium'
                ]"
              >
                {{ trade.action }}
              </span>
              <span class="font-medium text-gray-900">{{ trade.symbol }}</span>
            </div>
            <span
              :class="[
                'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
                trade.status === 'open' ? 'bg-blue-100 text-blue-800' :
                trade.status === 'closed' ? 'bg-gray-100 text-gray-800' :
                trade.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                'bg-red-100 text-red-800'
              ]"
            >
              {{ trade.status }}
            </span>
          </div>
          <div class="mt-2 text-sm text-gray-500">
            <div>{{ trade.quantity }} @ ${{ trade.entry_price }}</div>
            <div v-if="trade.exit_price">Exit: ${{ trade.exit_price }}</div>
          </div>
          <div class="mt-2 flex items-center justify-between">
            <div>
              <span
                v-if="trade.pnl !== null && trade.pnl !== undefined"
                :class="[
                  'text-sm font-medium',
                  trade.pnl >= 0 ? 'text-green-600' : 'text-red-600'
                ]"
              >
                P&L: {{ trade.pnl >= 0 ? '+' : '' }}${{ trade.pnl.toFixed(2) }}
              </span>
              <span
                v-else-if="trade.floating_pnl !== null && trade.floating_pnl !== undefined"
                :class="[
                  'text-sm font-medium',
                  trade.floating_pnl >= 0 ? 'text-green-600' : 'text-red-600'
                ]"
              >
                Float: {{ trade.floating_pnl >= 0 ? '+' : '' }}${{ trade.floating_pnl.toFixed(2) }}
              </span>
            </div>
            <button
              v-if="trade.status === 'open'"
              @click="$emit('close', trade.id)"
              class="text-xs text-primary-600 hover:text-primary-900"
            >
              Close Trade
            </button>
          </div>
        </li>
      </ul>
    </div>

    <!-- Desktop view -->
    <div class="hidden sm:block">
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
              Entry
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
          <tr v-for="trade in trades" :key="trade.id">
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
              {{ trade.symbol }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
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
              {{ trade.quantity }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
              ${{ trade.entry_price }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
              <div v-if="trade.status === 'open' && trade.current_price">
                ${{ trade.current_price }}
                <button
                  @click="$emit('update-price', trade.id)"
                  class="ml-2 text-xs text-primary-600 hover:text-primary-900"
                >
                  Refresh
                </button>
              </div>
              <div v-else-if="trade.exit_price">
                ${{ trade.exit_price }}
              </div>
              <div v-else>-</div>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
              <span
                v-if="trade.pnl !== null && trade.pnl !== undefined"
                :class="[
                  trade.pnl >= 0 ? 'text-green-600' : 'text-red-600'
                ]"
              >
                {{ trade.pnl >= 0 ? '+' : '' }}${{ trade.pnl.toFixed(2) }}
              </span>
              <span
                v-else-if="trade.floating_pnl !== null && trade.floating_pnl !== undefined"
                :class="[
                  trade.floating_pnl >= 0 ? 'text-green-600' : 'text-red-600'
                ]"
              >
                {{ trade.floating_pnl >= 0 ? '+' : '' }}${{ trade.floating_pnl.toFixed(2) }}
                <span class="text-xs text-gray-400 ml-1">(Float)</span>
              </span>
              <span v-else class="text-gray-400">-</span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
              <span
                :class="[
                  'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
                  trade.status === 'open' ? 'bg-blue-100 text-blue-800' :
                  trade.status === 'closed' ? 'bg-gray-100 text-gray-800' :
                  trade.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                  'bg-red-100 text-red-800'
                ]"
              >
                {{ trade.status }}
              </span>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
              <button
                v-if="trade.status === 'open'"
                @click="$emit('close', trade.id)"
                class="text-primary-600 hover:text-primary-900"
              >
                Close
              </button>
              <span v-else-if="trade.close_reason" class="text-xs text-gray-400">
                {{ trade.close_reason }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    
    <div v-if="trades.length === 0" class="text-center py-12">
      <p class="text-gray-500">No trades yet</p>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Trade {
  id: number
  symbol: string
  action: 'BUY' | 'SELL'
  quantity: number
  entry_price: number
  exit_price?: number
  current_price?: number
  pnl?: number
  floating_pnl?: number
  status: 'pending' | 'open' | 'closed' | 'cancelled'
  created_at: string
  closed_at?: string
  close_reason?: string
}

defineProps<{
  trades: Trade[]
}>()

defineEmits<{
  close: [id: number]
  'update-price': [id: number]
}>()
</script> 