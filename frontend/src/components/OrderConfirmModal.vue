<template>
  <div v-if="isOpen" class="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center p-4 z-50">
    <div class="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-hidden">
      <!-- Header -->
      <div class="px-6 py-4 border-b bg-gray-50">
        <div class="flex items-center justify-between">
          <h3 class="text-lg font-medium text-gray-900">
            Confirm Order
          </h3>
          <button
            @click="close"
            class="text-gray-400 hover:text-gray-500"
          >
            <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>
      
      <!-- Content -->
      <div class="p-6 overflow-y-auto max-h-[calc(90vh-180px)]">
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <!-- Order Form -->
          <div class="space-y-6">
            <h4 class="text-lg font-medium text-gray-900">Order Details</h4>
            
            <!-- Buy/Sell Tabs -->
            <div class="flex space-x-1 bg-gray-100 p-1 rounded-lg">
              <button
                @click="orderForm.action = 'BUY'"
                :class="[
                  'flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors',
                  orderForm.action === 'BUY'
                    ? 'bg-green-500 text-white'
                    : 'text-gray-700 hover:bg-gray-200'
                ]"
              >
                Buy
              </button>
              <button
                @click="orderForm.action = 'SELL'"
                :class="[
                  'flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors',
                  orderForm.action === 'SELL'
                    ? 'bg-red-500 text-white'
                    : 'text-gray-700 hover:bg-gray-200'
                ]"
              >
                Sell
              </button>
            </div>
            
            <!-- Symbol -->
            <div>
              <label class="block text-sm font-medium text-gray-700">Symbol</label>
              <div class="mt-1 flex items-center space-x-2">
                <input
                  v-model="orderForm.symbol"
                  type="text"
                  class="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                  @blur="validateOrder"
                />
                <button
                  @click="validateOrder"
                  :disabled="validating"
                  class="px-3 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 disabled:opacity-50"
                >
                  {{ validating ? 'Checking...' : 'Validate' }}
                </button>
              </div>
              <p v-if="marketData" class="mt-1 text-sm text-gray-600">
                Market Price: ${{ marketData.last?.toFixed(2) || 'N/A' }}
              </p>
            </div>
            
            <!-- Amount -->
            <div>
              <label class="block text-sm font-medium text-gray-700">Amount</label>
              <div class="mt-1">
                <!-- Radio buttons for selecting mode -->
                <div class="flex space-x-4 mb-3">
                  <label class="flex items-center">
                    <input
                      type="radio"
                      value="dollars"
                      v-model="orderForm.amountType"
                      class="text-primary-600 focus:ring-primary-500"
                    />
                    <span class="ml-2 text-sm text-gray-700">Dollars</span>
                  </label>
                  <label class="flex items-center">
                    <input
                      type="radio"
                      value="shares"
                      v-model="orderForm.amountType"
                      class="text-primary-600 focus:ring-primary-500"
                    />
                    <span class="ml-2 text-sm text-gray-700">Shares</span>
                  </label>
                </div>
                
                <!-- Dollar amount input (only show in dollars mode) -->
                <div v-if="orderForm.amountType === 'dollars'" class="flex items-center space-x-2">
                  <span class="text-gray-500">$</span>
                  <input
                    v-model.number="orderForm.dollarAmount"
                    type="number"
                    step="0.01"
                    min="1"
                    placeholder="100.00"
                    class="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                    @input="calculateQuantityFromDollars"
                  />
                </div>
                
                <!-- Shares input (only show in shares mode) -->
                <div v-if="orderForm.amountType === 'shares'" class="flex items-center space-x-2">
                  <input
                    v-model.number="orderForm.quantity"
                    type="number"
                    :min="canTradeFractional ? 0.0001 : 1"
                    :step="canTradeFractional ? 0.0001 : 1"
                    placeholder="100"
                    class="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                    @input="calculateDollarsFromQuantity"
                  />
                  <span class="text-gray-500">shares</span>
                </div>
                
                <!-- Calculated values display -->
                <div class="mt-2 text-sm text-gray-600">
                  <p v-if="orderForm.amountType === 'dollars' && orderForm.quantity > 0">
                    ≈ {{ formatQuantity(orderForm.quantity) }} {{ orderForm.quantity === 1 ? 'share' : 'shares' }}
                    <span v-if="marketData?.last" class="text-xs">
                      (at ${{ marketData.last.toFixed(2) }}/share)
                    </span>
                    <span v-if="canTradeFractional" class="text-xs text-green-600 ml-1">
                      • Fractional
                    </span>
                  </p>
                  <p v-if="orderForm.amountType === 'shares' && orderForm.dollarAmount > 0">
                    ≈ ${{ orderForm.dollarAmount.toFixed(2) }}
                    <span v-if="marketData?.last" class="text-xs">
                      (at ${{ marketData.last.toFixed(2) }}/share)
                    </span>
                  </p>
                  <p v-if="!marketData?.last && validating" class="text-yellow-600">
                    Fetching market data...
                  </p>
                  <p v-else-if="!marketData?.last" class="text-yellow-600">
                    Validate symbol to calculate amounts
                  </p>
                </div>
              </div>
            </div>
            
            <!-- Order Type -->
            <div>
              <label class="block text-sm font-medium text-gray-700">Order Type</label>
              <select
                v-model="orderForm.order_type"
                class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                @change="validateOrder"
              >
                <option value="MARKET">Market</option>
                <option value="LIMIT">Limit</option>
              </select>
            </div>
            
            <!-- Limit Price (if limit order) -->
            <div v-if="orderForm.order_type === 'LIMIT'">
              <label class="block text-sm font-medium text-gray-700">Limit Price</label>
              <div class="mt-1 flex items-center space-x-2">
                <span class="text-gray-500">$</span>
                <input
                  v-model="orderForm.limit_price"
                  type="number"
                  step="0.01"
                  min="0.01"
                  class="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                  @change="validateOrder"
                />
              </div>
            </div>
            
            <!-- Time in Force -->
            <div>
              <label class="block text-sm font-medium text-gray-700">Time in Force</label>
              <select
                v-model="orderForm.time_in_force"
                class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
              >
                <option value="DAY">DAY - Good for the day</option>
                <option value="GTC">GTC - Good till canceled</option>
                <option value="IOC">IOC - Immediate or cancel</option>
                <option value="FOK">FOK - Fill or kill</option>
              </select>
            </div>
          </div>
          
          <!-- Order Preview & Account Info -->
          <div class="space-y-6">
            <!-- Signal Info -->
            <div v-if="signal && signal.id !== 0" class="bg-gray-50 p-4 rounded-lg">
              <h5 class="text-sm font-medium text-gray-900 mb-2">Original Signal</h5>
              <div class="text-sm text-gray-600 space-y-1">
                <p><span class="font-medium">Symbol:</span> {{ signal.symbol }}</p>
                <p><span class="font-medium">Action:</span> {{ signal.action }}</p>
                <p v-if="signal.price"><span class="font-medium">Price:</span> ${{ signal.price }}</p>
                <p v-if="signal.stop_loss"><span class="font-medium">Stop Loss:</span> ${{ signal.stop_loss }}</p>
                <p v-if="signal.take_profit"><span class="font-medium">Take Profit:</span> ${{ signal.take_profit }}</p>
              </div>
            </div>
            
            <!-- Manual Trade Indicator -->
            <div v-if="signal && signal.id === 0" class="bg-purple-50 p-4 rounded-lg">
              <h5 class="text-sm font-medium text-purple-900 mb-2">Manual Trade Entry</h5>
              <p class="text-sm text-purple-700">Creating a new manual trade order</p>
            </div>
            
            <!-- Market Data -->
            <div v-if="marketData" class="bg-blue-50 p-4 rounded-lg">
              <h5 class="text-sm font-medium text-gray-900 mb-2">Market Data</h5>
              <div class="text-sm text-gray-600 space-y-1">
                <p><span class="font-medium">Bid:</span> ${{ marketData.bid?.toFixed(2) }}</p>
                <p><span class="font-medium">Ask:</span> ${{ marketData.ask?.toFixed(2) }}</p>
                <p><span class="font-medium">Last:</span> ${{ marketData.last?.toFixed(2) }}</p>
              </div>
            </div>
            
            <!-- Order Summary -->
            <div v-if="orderPreview && (orderForm.order_type !== 'LIMIT' || orderForm.limit_price)" class="bg-green-50 p-4 rounded-lg">
              <h5 class="text-sm font-medium text-gray-900 mb-2">Order Summary</h5>
              <div class="text-sm text-gray-600 space-y-1">
                <p><span class="font-medium">Estimated Quantity:</span> {{ formatQuantity(orderPreview.estimated_quantity) }}</p>
                <p><span class="font-medium">Estimated Price:</span> ${{ orderPreview.estimated_price?.toFixed(2) }}</p>
                <p><span class="font-medium">Estimated Cost:</span> ${{ orderPreview.estimated_cost?.toFixed(2) }}</p>
                <p v-if="canTradeFractional" class="text-xs text-green-600 mt-2">
                  ✓ This stock supports fractional shares
                </p>
              </div>
            </div>
            
            <!-- Account Info -->
            <div v-if="validationResult?.account_info" class="bg-yellow-50 p-4 rounded-lg">
              <h5 class="text-sm font-medium text-gray-900 mb-2">Account Info</h5>
              <div class="text-sm text-gray-600 space-y-1">
                <p><span class="font-medium">Buying Power:</span> ${{ validationResult.account_info.buying_power?.toFixed(2) }}</p>
                <p><span class="font-medium">Cash:</span> ${{ validationResult.account_info.cash?.toFixed(2) }}</p>
                <p><span class="font-medium">Portfolio Value:</span> ${{ validationResult.account_info.portfolio_value?.toFixed(2) }}</p>
              </div>
            </div>
            
            <!-- Validation Errors/Warnings -->
            <div v-if="validationResult?.errors?.length" class="bg-red-50 p-4 rounded-lg">
              <h5 class="text-sm font-medium text-red-900 mb-2">Errors</h5>
              <ul class="text-sm text-red-700 space-y-1">
                <li v-for="error in validationResult.errors" :key="error">• {{ error }}</li>
              </ul>
            </div>
            
            <div v-if="validationResult?.warnings?.length" class="bg-yellow-50 p-4 rounded-lg">
              <h5 class="text-sm font-medium text-yellow-900 mb-2">Warnings</h5>
              <ul class="text-sm text-yellow-700 space-y-1">
                <li v-for="warning in validationResult.warnings" :key="warning">• {{ warning }}</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Footer -->
      <div class="px-6 py-4 border-t bg-gray-50 flex justify-between items-center">
        <div class="text-sm text-gray-600">
          <span v-if="accountStore.activeAccount?.account_type === 'paper'" class="font-medium text-yellow-600">
            Paper Trading Account
          </span>
          <span v-else class="font-medium text-green-600">
            Live Trading Account
          </span>
        </div>
        <div class="flex space-x-3">
          <button
            @click="close"
            class="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            @click="executeOrder"
            :disabled="!canExecute || executing"
            class="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {{ executing ? 'Executing...' : isNewSignal ? 'Create & Execute' : 'Execute Order' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import axios from '@/plugins/axios'
import { useAccountStore } from '@/stores/account'

interface Signal {
  id: number
  symbol: string
  action: string
  price?: number
  stop_loss?: number
  take_profit?: number
  quantity?: number
}

interface Props {
  signal: Signal | null
  isOpen: boolean
}

const props = defineProps<Props>()
const emit = defineEmits(['close', 'executed'])

const accountStore = useAccountStore()

const orderForm = ref({
  symbol: '',
  action: 'BUY',
  quantity: 1,
  dollarAmount: 100,
  amountType: 'dollars' as 'dollars' | 'shares',
  order_type: 'MARKET',
  limit_price: null as number | null,
  time_in_force: 'DAY'
})

const validating = ref(false)
const executing = ref(false)
const validationResult = ref<any>(null)
const marketDataRaw = ref<any>(null)

const marketData = computed(() => {
  // Prefer validationResult market_data if present, else fallback to independently fetched market data
  return validationResult.value?.market_data || marketDataRaw.value
})

const canTradeFractional = computed(() => {
  return marketData.value?.fractionable && validationResult.value?.account_info?.fractional_trading_enabled
})
const isNewSignal = computed(() => props.signal?.id === 0)
const canExecute = computed(() => {
  if (isNewSignal.value) {
    // For new signals, just check that we have a valid symbol and quantity
    return orderForm.value.symbol && orderForm.value.quantity > 0
  }
  // For existing signals, check validation result
  return validationResult.value?.valid
})

// Compute a local order preview for immediate feedback
const localOrderPreview = computed(() => {
  if (!marketData.value?.last) return null
  
  const price = orderForm.value.order_type === 'LIMIT' && orderForm.value.limit_price 
    ? Number(orderForm.value.limit_price)
    : marketData.value.last
    
  return {
    estimated_quantity: orderForm.value.quantity,
    estimated_price: price,
    estimated_cost: orderForm.value.quantity * price
  }
})

// Use either the validation result or local preview, but prefer local for real-time updates
const orderPreview = computed(() => {
  // Always use local preview if we have market data
  if (localOrderPreview.value) {
    return localOrderPreview.value
  }
  // Fall back to validation result if no local preview
  return validationResult.value?.order_preview
})

// Debounce timer for validation
let validationTimer: any = null

// Initialize form when signal changes
watch(() => props.signal, (newSignal) => {
  if (newSignal) {
    // Reset to defaults first
    orderForm.value.symbol = newSignal.symbol
    orderForm.value.action = newSignal.action
    orderForm.value.amountType = 'dollars'
    orderForm.value.dollarAmount = 100
    orderForm.value.quantity = 1 // Default to 1 share
    
    // If signal has a specific quantity, use it
    if (newSignal.quantity && newSignal.quantity > 0) {
      orderForm.value.quantity = newSignal.quantity
      orderForm.value.amountType = 'shares'
      // Calculate dollar amount will happen after validation
    }
    
    // If signal has a price, default to limit order
    if (newSignal.price) {
      orderForm.value.order_type = 'LIMIT'
      orderForm.value.limit_price = newSignal.price
    } else {
      orderForm.value.order_type = 'MARKET'
      orderForm.value.limit_price = null
    }
    
    // Clear previous validation results
    validationResult.value = null
    
    // Auto-validate when modal opens
    if (props.isOpen) {
      setTimeout(() => validateOrder(), 100) // Small delay to ensure UI is ready
    }
  }
})

// Auto-validate when modal opens
watch(() => props.isOpen, (isOpen) => {
  if (isOpen && props.signal) {
    // Small delay to ensure UI is ready, then validate
    setTimeout(() => {
      validateOrder()
    }, 100)
  }
})

// Watch for amount type changes to recalculate
watch(() => orderForm.value.amountType, () => {
  if (marketData.value?.last) {
    if (orderForm.value.amountType === 'dollars') {
      calculateQuantityFromDollars()
    } else {
      calculateDollarsFromQuantity()
    }
  }
})

const calculateQuantityFromDollars = () => {
  if (marketData.value?.last && orderForm.value.dollarAmount && orderForm.value.dollarAmount > 0) {
    let calculatedQuantity: number
    
    if (canTradeFractional.value) {
      // For fractional trading, calculate exact quantity to 4 decimal places
      calculatedQuantity = parseFloat((orderForm.value.dollarAmount / marketData.value.last).toFixed(4))
    } else {
      // For whole shares only, round down
      calculatedQuantity = Math.floor(orderForm.value.dollarAmount / marketData.value.last)
    }
    
    orderForm.value.quantity = Math.max(canTradeFractional.value ? 0.0001 : 1, calculatedQuantity)
    
    // Only trigger validation if not already validating
    if (!validating.value) {
      clearTimeout(validationTimer)
      validationTimer = setTimeout(() => {
        validateOrder()
      }, 500)
    }
  }
}

const calculateDollarsFromQuantity = () => {
  if (marketData.value?.last && orderForm.value.quantity && orderForm.value.quantity > 0) {
    orderForm.value.dollarAmount = parseFloat((orderForm.value.quantity * marketData.value.last).toFixed(2))
    
    // Only trigger validation if not already validating
    if (!validating.value) {
      clearTimeout(validationTimer)
      validationTimer = setTimeout(() => {
        validateOrder()
      }, 500)
    }
  }
}

const validateOrder = async () => {
  if (!props.signal || validating.value) return
  
  // For new signals, skip validation API call if no symbol
  if (isNewSignal.value && !orderForm.value.symbol) {
    validationResult.value = { valid: false, errors: ['Symbol is required'] }
    return
  }
  
  // Clear any pending validation timer
  clearTimeout(validationTimer)
  
  validating.value = true
  try {
    // For initial validation, send a reasonable default quantity
    let quantityToValidate = orderForm.value.quantity
    
    // If we're in dollar mode and don't have market data yet, send 1 as placeholder
    if (orderForm.value.amountType === 'dollars' && !marketData.value?.last) {
      quantityToValidate = 1
    }
    
    const orderParams = {
      symbol: orderForm.value.symbol,
      action: orderForm.value.action,
      quantity: quantityToValidate,
      order_type: orderForm.value.order_type,
      limit_price: orderForm.value.limit_price,
      time_in_force: orderForm.value.time_in_force
    }
    
    // For new signals, we need to validate differently
    let response
    if (isNewSignal.value) {
      // Create a temporary validation endpoint that doesn't require signal ID
      response = await axios.post('/api/signals/validate-market-order', orderParams)
    } else {
      response = await axios.post(`/api/signals/${props.signal.id}/validate-order`, orderParams)
    }
    
    validationResult.value = response.data
    
    // Now that we have market data, calculate the correct quantity if in dollar mode
    if (response.data.market_data?.last) {
      const marketPrice = response.data.market_data.last
      const fractionable = response.data.market_data.fractionable
      const fractionalEnabled = response.data.account_info?.fractional_trading_enabled
      
      if (orderForm.value.amountType === 'dollars') {
        // Calculate how many shares we can buy with the dollar amount
        let calculatedQuantity: number
        
        if (fractionable && fractionalEnabled) {
          // For fractional trading, calculate exact quantity to 4 decimal places
          calculatedQuantity = parseFloat((orderForm.value.dollarAmount / marketPrice).toFixed(4))
        } else {
          // For whole shares only, round down
          calculatedQuantity = Math.floor(orderForm.value.dollarAmount / marketPrice)
        }
        
        orderForm.value.quantity = Math.max((fractionable && fractionalEnabled) ? 0.0001 : 1, calculatedQuantity)
        
        console.log('Dollar mode calculation:', {
          dollarAmount: orderForm.value.dollarAmount,
          marketPrice: marketPrice,
          calculatedQuantity: orderForm.value.quantity,
          fractionalEnabled: fractionable && fractionalEnabled
        })
      } else {
        // In share mode, calculate the dollar amount
        orderForm.value.dollarAmount = parseFloat((orderForm.value.quantity * marketPrice).toFixed(2))
      }
    }
    
  } catch (error) {
    console.error('Error validating order:', error)
    validationResult.value = {
      valid: false,
      errors: ['Failed to validate order']
    }
  } finally {
    validating.value = false
  }
}

const executeOrder = async () => {
  if (!props.signal) return
  executing.value = true
  try {
    if (isNewSignal.value) {
      // 1. Create the signal (should be 'pending')
      const signalData = {
        symbol: orderForm.value.symbol,
        action: orderForm.value.action,
        quantity: orderForm.value.quantity,
        price: orderForm.value.order_type === 'LIMIT' ? orderForm.value.limit_price : null
      }
      const signalResponse = await axios.post('/api/signals', signalData)
      const newSignalId = signalResponse.data.id
      // 2. Approve the signal
      await axios.post(`/api/signals/${newSignalId}/approve`, { approved: true })
      // 3. Execute the trade
      const response = await axios.post(`/api/trades/execute/${newSignalId}`, {
        quantity: orderForm.value.quantity,
        order_type: orderForm.value.order_type,
        limit_price: orderForm.value.limit_price,
        time_in_force: orderForm.value.time_in_force
      })
      emit('executed', response.data)
      close()
    } else {
      // Existing flow for already created signals
      await axios.post(`/api/signals/${props.signal.id}/approve`, { approved: true })
      const response = await axios.post(`/api/trades/execute/${props.signal.id}`, {
        quantity: orderForm.value.quantity,
        order_type: orderForm.value.order_type,
        limit_price: orderForm.value.limit_price,
        time_in_force: orderForm.value.time_in_force
      })
      emit('executed', response.data)
      close()
    }
  } catch (error: any) {
    console.error('Error executing order:', error)
    alert(error.response?.data?.detail || 'Failed to execute order')
  } finally {
    executing.value = false
  }
}

const close = () => {
  validationResult.value = null
  // Reset form to defaults
  orderForm.value = {
    symbol: '',
    action: 'BUY',
    quantity: 1,
    dollarAmount: 100,
    amountType: 'dollars',
    order_type: 'MARKET',
    limit_price: null,
    time_in_force: 'DAY'
  }
  emit('close')
}

const formatQuantity = (quantity: number) => {
  if (quantity === Math.floor(quantity)) {
    return quantity.toString()
  } else {
    return quantity.toFixed(4)
  }
}

// Fetch market data independently
const fetchMarketData = async (symbol: string) => {
  if (!symbol) {
    marketDataRaw.value = null
    return
  }
  try {
    const response = await axios.get(`/api/market-data/${symbol}`)
    marketDataRaw.value = response.data
  } catch (error) {
    marketDataRaw.value = null
  }
}

// Watch symbol changes to fetch market data
watch(() => orderForm.value.symbol, (newSymbol) => {
  fetchMarketData(newSymbol)
})
</script> 