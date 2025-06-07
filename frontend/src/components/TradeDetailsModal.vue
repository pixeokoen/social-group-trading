<template>
  <div
    v-if="isOpen"
    class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
    @click.self="$emit('close')"
  >
    <div class="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
      <!-- Header -->
      <div class="bg-gradient-to-r from-slate-800 to-slate-700 text-white p-6 rounded-t-2xl">
        <div class="flex items-center justify-between">
          <div>
            <h2 class="text-2xl font-bold">{{ trade?.symbol }}</h2>
            <p class="text-slate-300 text-sm">Trade Details & Analysis</p>
          </div>
          <button
            @click="$emit('close')"
            class="w-8 h-8 rounded-full bg-slate-600 hover:bg-slate-500 flex items-center justify-center transition-colors duration-200"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>

      <!-- Content -->
      <div class="p-6 space-y-6" v-if="trade">
        <!-- Basic Trade Information -->
        <div class="bg-gradient-to-br from-slate-50 to-white rounded-xl p-5 border border-slate-200">
          <h3 class="text-lg font-semibold text-slate-800 mb-4 flex items-center">
            <svg class="w-5 h-5 mr-2 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
              <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Basic Information
          </h3>
          <div class="grid grid-cols-2 gap-4">
            <div class="space-y-3">
              <div>
                <label class="text-xs font-medium text-slate-500 uppercase tracking-wide">Trade ID</label>
                <p class="text-sm font-semibold text-slate-800">{{ trade.id || 'Not available' }}</p>
              </div>
              <div>
                <label class="text-xs font-medium text-slate-500 uppercase tracking-wide">Action</label>
                <span :class="[
                  'inline-block px-2 py-1 text-xs font-bold rounded-full',
                  trade.action === 'BUY' ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'
                ]">
                  {{ trade.action || 'Not available' }}
                </span>
              </div>
              <div>
                <label class="text-xs font-medium text-slate-500 uppercase tracking-wide">Quantity</label>
                <p class="text-sm font-semibold text-slate-800">{{ formatQuantity(trade.quantity) }} shares</p>
              </div>
              <div>
                <label class="text-xs font-medium text-slate-500 uppercase tracking-wide">Status</label>
                <span :class="[
                  'inline-block px-2 py-1 text-xs font-bold rounded-full',
                  getStatusColor(trade.status)
                ]">
                  {{ trade.status || 'Not available' }}
                </span>
              </div>
            </div>
            <div class="space-y-3">
              <div>
                <label class="text-xs font-medium text-slate-500 uppercase tracking-wide">Link Group</label>
                <p class="text-sm font-semibold text-slate-800">{{ trade.link_group_id || 'Not linked' }}</p>
              </div>
              <div>
                <label class="text-xs font-medium text-slate-500 uppercase tracking-wide">Entry Price</label>
                <p class="text-sm font-semibold text-slate-800">${{ formatPrice(trade.entry_price || trade.broker_fill_price) }}</p>
              </div>
              <div>
                <label class="text-xs font-medium text-slate-500 uppercase tracking-wide">Current Price</label>
                <p class="text-sm font-semibold text-slate-800">${{ formatPrice(trade.current_price) }}</p>
              </div>
              <div>
                <label class="text-xs font-medium text-slate-500 uppercase tracking-wide">Exit Price</label>
                <p class="text-sm font-semibold text-slate-800">${{ formatPrice(trade.exit_price) }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- P&L Information -->
        <div class="bg-gradient-to-br from-slate-50 to-white rounded-xl p-5 border border-slate-200">
          <h3 class="text-lg font-semibold text-slate-800 mb-4 flex items-center">
            <svg class="w-5 h-5 mr-2 text-green-600" fill="currentColor" viewBox="0 0 20 20">
              <path d="M8.433 7.418c.155-.103.346-.196.567-.267v1.698a2.305 2.305 0 01-.567-.267C8.07 8.34 8 8.114 8 8c0-.114.07-.34.433-.582zM11 12.849v-1.698c.22.071.412.164.567.267.364.243.433.468.433.582 0 .114-.07.34-.433.582a2.305 2.305 0 01-.567.267z" />
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-13a1 1 0 10-2 0v.092a4.535 4.535 0 00-1.676.662C6.602 6.234 6 7.009 6 8c0 .99.602 1.765 1.324 2.246.48.32 1.054.545 1.676.662v1.941c-.391-.127-.68-.317-.843-.504a1 1 0 10-1.51 1.31c.562.649 1.413 1.076 2.353 1.253V15a1 1 0 102 0v-.092a4.535 4.535 0 001.676-.662C13.398 13.766 14 12.991 14 12c0-.99-.602-1.765-1.324-2.246A4.535 4.535 0 0011 9.092V7.151c.391.127.68.317.843.504a1 1 0 101.51-1.31c-.562-.649-1.413-1.076-2.353-1.253V5z" clip-rule="evenodd" />
            </svg>
            Profit & Loss
          </h3>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="text-xs font-medium text-slate-500 uppercase tracking-wide">Floating P&L</label>
              <p :class="[
                'text-lg font-bold',
                (trade.floating_pnl || 0) >= 0 ? 'text-emerald-600' : 'text-rose-600'
              ]">
                {{ (trade.floating_pnl || 0) >= 0 ? '+' : '' }}${{ formatPrice(trade.floating_pnl) }}
              </p>
            </div>
            <div>
              <label class="text-xs font-medium text-slate-500 uppercase tracking-wide">Realized P&L</label>
              <p :class="[
                'text-lg font-bold',
                (trade.pnl || 0) >= 0 ? 'text-emerald-600' : 'text-rose-600'
              ]">
                {{ (trade.pnl || 0) >= 0 ? '+' : '' }}${{ formatPrice(trade.pnl) }}
              </p>
            </div>
          </div>
        </div>

        <!-- Stop Loss Information -->
        <div v-if="trade.stop_loss" class="bg-gradient-to-br from-rose-50 to-red-50 rounded-xl p-5 border border-rose-200">
          <h3 class="text-lg font-semibold text-slate-800 mb-4 flex items-center">
            <svg class="w-5 h-5 mr-2 text-rose-600" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
            </svg>
            Stop Loss
          </h3>
          <div class="grid grid-cols-3 gap-4">
            <div>
              <label class="text-xs font-medium text-slate-500 uppercase tracking-wide">Stop Price</label>
              <p class="text-sm font-semibold text-rose-700">${{ formatPrice(trade.stop_loss) }}</p>
            </div>
            <div>
              <label class="text-xs font-medium text-slate-500 uppercase tracking-wide">Status</label>
              <span :class="[
                'inline-block px-2 py-1 text-xs font-bold rounded-full',
                trade.stop_loss_status === 'executed' 
                  ? 'bg-red-100 text-red-800' 
                  : 'bg-yellow-100 text-yellow-800'
              ]">
                {{ trade.stop_loss_status || 'Not available' }}
              </span>
            </div>
            <div>
              <label class="text-xs font-medium text-slate-500 uppercase tracking-wide">Executed Price</label>
              <p class="text-sm font-semibold text-slate-800">
                {{ trade.stop_loss_executed_price ? '$' + formatPrice(trade.stop_loss_executed_price) : 'Not executed' }}
              </p>
            </div>
          </div>
        </div>

        <!-- Take Profit Levels -->
        <div v-if="trade.take_profit_levels && trade.take_profit_levels.length > 0" 
             class="bg-gradient-to-br from-emerald-50 to-green-50 rounded-xl p-5 border border-emerald-200">
          <h3 class="text-lg font-semibold text-slate-800 mb-4 flex items-center">
            <svg class="w-5 h-5 mr-2 text-emerald-600" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
            </svg>
            Take Profit Levels
          </h3>
          <div class="space-y-3">
            <div v-for="tp in trade.take_profit_levels" :key="tp.id" 
                 class="bg-white rounded-lg p-4 border border-emerald-100">
              <div class="grid grid-cols-5 gap-3">
                <div>
                  <label class="text-xs font-medium text-slate-500 uppercase tracking-wide">Level</label>
                  <p class="text-sm font-semibold text-slate-800">{{ tp.level_number }}</p>
                </div>
                <div>
                  <label class="text-xs font-medium text-slate-500 uppercase tracking-wide">Price</label>
                  <p class="text-sm font-semibold text-emerald-700">${{ formatPrice(tp.price) }}</p>
                </div>
                <div>
                  <label class="text-xs font-medium text-slate-500 uppercase tracking-wide">Percentage</label>
                  <p class="text-sm font-semibold text-slate-800">{{ tp.percentage }}%</p>
                </div>
                <div>
                  <label class="text-xs font-medium text-slate-500 uppercase tracking-wide">Shares</label>
                  <p class="text-sm font-semibold text-slate-800">{{ formatQuantity(tp.shares_quantity) }}</p>
                </div>
                <div>
                  <label class="text-xs font-medium text-slate-500 uppercase tracking-wide">Status</label>
                  <span :class="[
                    'inline-block px-2 py-1 text-xs font-bold rounded-full',
                    tp.status === 'executed' 
                      ? 'bg-green-100 text-green-800' 
                      : 'bg-yellow-100 text-yellow-800'
                  ]">
                    {{ tp.status }}
                  </span>
                </div>
              </div>
              <div v-if="tp.executed_at || tp.executed_price" class="mt-3 pt-3 border-t border-emerald-100">
                <div class="grid grid-cols-2 gap-3">
                  <div v-if="tp.executed_at">
                    <label class="text-xs font-medium text-slate-500 uppercase tracking-wide">Executed At</label>
                    <p class="text-sm font-semibold text-slate-800">{{ formatDateTime(tp.executed_at) }}</p>
                  </div>
                  <div v-if="tp.executed_price">
                    <label class="text-xs font-medium text-slate-500 uppercase tracking-wide">Executed Price</label>
                    <p class="text-sm font-semibold text-emerald-700">${{ formatPrice(tp.executed_price) }}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- No Enhanced Features Message -->
        <div v-if="!trade.stop_loss && (!trade.take_profit_levels || trade.take_profit_levels.length === 0)" 
             class="bg-gradient-to-br from-slate-50 to-gray-50 rounded-xl p-5 border border-slate-200 text-center">
          <svg class="w-12 h-12 mx-auto text-slate-400 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <h3 class="text-lg font-semibold text-slate-600 mb-2">Plain Trade</h3>
          <p class="text-sm text-slate-500">This trade has no stop loss or take profit levels configured.</p>
        </div>
      </div>

      <!-- Footer -->
      <div class="p-6 border-t border-slate-200 bg-slate-50 rounded-b-2xl">
        <div class="flex justify-end">
          <button
            @click="$emit('close')"
            class="px-6 py-2 bg-slate-600 hover:bg-slate-700 text-white rounded-lg font-medium transition-colors duration-200"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface TakeProfitLevel {
  id: number
  level_number: number
  price: number
  percentage: number
  shares_quantity: number
  status: string
  executed_at?: string
  executed_price?: number
}

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
  stop_loss?: number
  stop_loss_status?: string
  stop_loss_executed_at?: string
  stop_loss_executed_price?: number
  take_profit_levels?: TakeProfitLevel[]
  link_group_id?: string
}

interface Props {
  trade: Trade | null
  isOpen: boolean
}

defineProps<Props>()
defineEmits<{
  close: []
}>()

// Helper functions
const formatPrice = (price: any) => {
  if (price === null || price === undefined) return 'Not available'
  const numPrice = typeof price === 'string' ? parseFloat(price) : price
  return isNaN(numPrice) ? 'Not available' : numPrice.toFixed(2)
}

const formatQuantity = (quantity: number | string) => {
  if (quantity === null || quantity === undefined) return '0'
  const numQuantity = typeof quantity === 'string' ? parseFloat(quantity) : quantity
  if (isNaN(numQuantity)) return '0'
  return numQuantity === Math.floor(numQuantity) ? numQuantity.toString() : numQuantity.toFixed(1)
}

const formatDateTime = (dateString: string) => {
  if (!dateString) return 'Not available'
  try {
    return new Date(dateString).toLocaleString()
  } catch {
    return 'Invalid date'
  }
}

const getStatusColor = (status: string) => {
  switch (status?.toLowerCase()) {
    case 'open':
      return 'bg-blue-100 text-blue-800'
    case 'closed':
      return 'bg-gray-100 text-gray-800'
    case 'pending':
      return 'bg-yellow-100 text-yellow-800'
    case 'cancelled':
      return 'bg-red-100 text-red-800'
    default:
      return 'bg-slate-100 text-slate-800'
  }
}
</script> 