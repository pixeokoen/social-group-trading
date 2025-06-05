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
                trade.status === 'filled' ? 'bg-blue-100 text-blue-800' :
                trade.status === 'open' ? 'bg-green-100 text-green-800' :
                trade.status === 'closed' ? 'bg-gray-100 text-gray-800' :
                trade.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                'bg-red-100 text-red-800'
              ]"
            >
              {{ trade.status }}
            </span>
          </div>
          <div class="mt-2 text-sm text-gray-500">
            <div>{{ trade.quantity }} @ ${{ trade.entry_price || 0 }}</div>
            <div v-if="trade.exit_price">Exit: ${{ trade.exit_price }}</div>
          </div>
          <div class="mt-2 flex items-center justify-between">
            <div>
              <span
                v-if="trade.status === 'closed' && trade.pnl !== null && trade.pnl !== undefined"
                :class="[
                  'text-sm font-medium',
                  (trade.pnl || 0) >= 0 ? 'text-green-600' : 'text-red-600'
                ]"
              >
                P&L: {{ (trade.pnl || 0) >= 0 ? '+' : '' }}${{ trade.pnl ? Math.abs(trade.pnl).toFixed(2) : '0.00' }}
              </span>
              <span
                v-else-if="(trade.status === 'filled' || trade.status === 'open') && trade.floating_pnl !== null && trade.floating_pnl !== undefined"
                :class="[
                  'text-sm font-medium',
                  (trade.floating_pnl || 0) >= 0 ? 'text-green-600' : 'text-red-600'
                ]"
              >
                Float: {{ (trade.floating_pnl || 0) >= 0 ? '+' : '' }}${{ trade.floating_pnl ? Math.abs(trade.floating_pnl).toFixed(2) : '0.00' }}
              </span>
            </div>
            <button
              v-if="(trade.status === 'filled' || trade.status === 'open') && trade.action === 'BUY'"
              @click="$emit('close', trade)"
              class="inline-flex items-center px-3 py-1 border border-transparent text-xs rounded-md text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
            >
              <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M16 11V7a4 4 0 00-8 0v4M5 11h14l-1.68 9.39A2 2 0 0115.34 22H8.66a2 2 0 01-1.98-1.61L5 11z" />
              </svg>
              Sell
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
              ${{ trade.entry_price || 0 }}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
              <div v-if="(trade.status === 'filled' || trade.status === 'open') && trade.current_price">
                ${{ trade.current_price }}
              </div>
              <div v-else-if="trade.exit_price">
                ${{ trade.exit_price }}
              </div>
              <div v-else>-</div>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
              <div>
                <span
                  v-if="trade.status === 'closed' && trade.pnl !== null && trade.pnl !== undefined"
                  :class="[
                    'font-medium',
                    (trade.pnl || 0) >= 0 ? 'text-green-600' : 'text-red-600'
                  ]"
                >
                  {{ (trade.pnl || 0) >= 0 ? '+' : '' }}${{ trade.pnl ? Math.abs(trade.pnl).toFixed(2) : '0.00' }}
                </span>
                <span
                  v-else-if="(trade.status === 'filled' || trade.status === 'open') && trade.floating_pnl !== null && trade.floating_pnl !== undefined"
                  :class="[
                    'font-medium',
                    (trade.floating_pnl || 0) >= 0 ? 'text-green-600' : 'text-red-600'
                  ]"
                >
                  {{ (trade.floating_pnl || 0) >= 0 ? '+' : '' }}${{ trade.floating_pnl ? Math.abs(trade.floating_pnl).toFixed(2) : '0.00' }}
                  <span class="text-xs text-gray-400 ml-1">(Float)</span>
                </span>
                <span v-else class="text-gray-400">-</span>
              </div>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
              <span
                :class="[
                  'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
                  trade.status === 'filled' ? 'bg-blue-100 text-blue-800' :
                  trade.status === 'open' ? 'bg-green-100 text-green-800' :
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
                v-if="(trade.status === 'filled' || trade.status === 'open') && trade.action === 'BUY'"
                @click="$emit('close', trade)"
                class="inline-flex items-center px-3 py-1 border border-transparent text-xs rounded-md text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
              >
                <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M16 11V7a4 4 0 00-8 0v4M5 11h14l-1.68 9.39A2 2 0 0115.34 22H8.66a2 2 0 01-1.98-1.61L5 11z" />
                </svg>
                Sell
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
  entry_price?: number
  exit_price?: number
  current_price?: number
  pnl?: number
  floating_pnl?: number
  status: 'pending' | 'filled' | 'open' | 'closed' | 'cancelled'
  created_at?: string
  closed_at?: string
  close_reason?: string
}

defineProps<{
  trades: Trade[]
}>()

defineEmits<{
  close: [trade: Trade]
  'update-price': [id: number]
}>()
</script> 