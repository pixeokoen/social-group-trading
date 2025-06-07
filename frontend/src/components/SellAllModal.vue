<template>
  <div 
    v-if="show" 
    class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
    @click.self="$emit('close')"
  >
    <div class="bg-white rounded-lg p-6 max-w-md w-full mx-4 shadow-xl">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-lg font-semibold text-gray-900">
          Sell All Remaining Shares
        </h3>
        <button 
          @click="$emit('close')"
          class="text-gray-400 hover:text-gray-600"
        >
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <div class="mb-6">
        <div class="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
          <div class="flex">
            <svg class="w-5 h-5 text-red-400 mt-0.5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
            <div class="text-sm text-red-700">
              <p class="font-medium">This action cannot be undone</p>
              <p class="mt-1">All pending take profit and stop loss levels will be cancelled.</p>
            </div>
          </div>
        </div>

        <div class="space-y-3">
          <div class="flex justify-between items-center">
            <span class="text-sm font-medium text-gray-600">Symbol:</span>
            <span class="font-semibold">{{ position.symbol }}</span>
          </div>
          
          <div class="flex justify-between items-center">
            <span class="text-sm font-medium text-gray-600">Remaining Shares:</span>
            <span class="font-semibold">{{ remainingShares.toLocaleString() }}</span>
          </div>
          
          <div class="flex justify-between items-center">
            <span class="text-sm font-medium text-gray-600">Current Price:</span>
            <span class="font-semibold">${{ currentPrice.toFixed(2) }}</span>
          </div>
          
          <div class="flex justify-between items-center">
            <span class="text-sm font-medium text-gray-600">Entry Price:</span>
            <span class="font-semibold">${{ entryPrice.toFixed(2) }}</span>
          </div>
          
          <hr class="border-gray-200">
          
          <div class="flex justify-between items-center">
            <span class="text-sm font-medium text-gray-600">Estimated Total:</span>
            <span class="font-semibold">${{ estimatedTotal.toFixed(2) }}</span>
          </div>
          
          <div class="flex justify-between items-center">
            <span class="text-sm font-medium text-gray-600">Estimated P&L:</span>
            <span 
              :class="{
                'text-green-600': estimatedPnl >= 0,
                'text-red-600': estimatedPnl < 0
              }"
              class="font-semibold"
            >
              {{ estimatedPnl >= 0 ? '+' : '' }}${{ estimatedPnl.toFixed(2) }}
            </span>
          </div>
          
          <div v-if="overriddenLevels.total > 0" class="mt-4 p-3 bg-amber-50 border border-amber-200 rounded-lg">
            <p class="text-sm text-amber-800 font-medium">Levels to be cancelled:</p>
            <ul class="text-sm text-amber-700 mt-1 space-y-1">
              <li v-if="overriddenLevels.takeProfits > 0">
                • {{ overriddenLevels.takeProfits }} Take Profit level(s)
              </li>
              <li v-if="overriddenLevels.stopLosses > 0">
                • {{ overriddenLevels.stopLosses }} Stop Loss level(s)
              </li>
            </ul>
          </div>
        </div>
      </div>

      <div class="flex gap-3">
        <button
          @click="$emit('close')"
          class="flex-1 px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
        >
          Cancel
        </button>
        <button
          @click="confirmSellAll"
          :disabled="loading"
          class="flex-1 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors disabled:opacity-50 flex items-center justify-center"
        >
          <svg v-if="loading" class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          {{ loading ? 'Executing...' : 'Sell All' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'SellAllModal',
  props: {
    show: {
      type: Boolean,
      default: false
    },
    position: {
      type: Object,
      required: true
    }
  },
  emits: ['close', 'confirm'],
  data() {
    return {
      loading: false
    }
  },
  computed: {
    remainingShares() {
      // Use effective_quantity if available (for linked trades), otherwise calculate normally
      if (this.position.effective_quantity !== undefined) {
        return Number(this.position.effective_quantity)
      }
      
      // Fallback to original calculation for non-linked trades
      return Number(this.position.quantity || 0) - Number(this.position.executed_tp_shares || 0)
    },
    currentPrice() {
      const price = Number(this.position.current_price || this.position.entry_price || this.position.broker_fill_price || 0)
      return isNaN(price) ? 0 : price
    },
    entryPrice() {
      const price = Number(this.position.entry_price || this.position.broker_fill_price || 0)
      return isNaN(price) ? 0 : price
    },
    estimatedTotal() {
      const total = this.remainingShares * this.currentPrice
      return isNaN(total) ? 0 : total
    },
    estimatedPnl() {
      if (this.position.action === 'BUY') {
        const pnl = (this.currentPrice - this.entryPrice) * this.remainingShares
        return isNaN(pnl) ? 0 : pnl
      } else {
        // Short position
        const pnl = (this.entryPrice - this.currentPrice) * this.remainingShares
        return isNaN(pnl) ? 0 : pnl
      }
    },
    overriddenLevels() {
      const takeProfits = (this.position.levels || []).filter(l => l.type === 'take_profit' && l.status === 'pending').length
      const stopLosses = (this.position.levels || []).filter(l => l.type === 'stop_loss' && l.status === 'active').length
      
      return {
        takeProfits,
        stopLosses,
        total: takeProfits + stopLosses
      }
    }
  },
  methods: {
    async confirmSellAll() {
      this.loading = true
      try {
        await this.$emit('confirm', {
          tradeId: this.position.id,
          remainingShares: this.remainingShares,
          currentPrice: this.currentPrice,
          estimatedPnl: this.estimatedPnl
        })
      } finally {
        this.loading = false
      }
    }
  }
}
</script> 