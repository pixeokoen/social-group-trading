<template>
  <div v-if="isOpen" class="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center p-4 z-50">
    <div class="bg-white rounded-lg max-w-7xl w-full max-h-[90vh] overflow-hidden">
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
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <!-- Left Column - Order Form -->
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
                <option value="STOP">Stop</option>
                <option value="STOP_LIMIT">Stop-Limit</option>
              </select>
              
              <!-- Order type explanations -->
              <div class="mt-2 text-xs text-gray-500">
                <p v-if="orderForm.order_type === 'MARKET'">
                  <strong>Market:</strong> Execute immediately at current market price
                </p>
                <p v-if="orderForm.order_type === 'LIMIT'">
                  <strong>Limit:</strong> Only execute at specified price or better
                </p>
                <p v-if="orderForm.order_type === 'STOP'">
                  <strong>Stop:</strong> Becomes market order when stop price is reached
                </p>
                <p v-if="orderForm.order_type === 'STOP_LIMIT'">
                  <strong>Stop-Limit:</strong> Becomes limit order when stop price is reached
                </p>
              </div>
            </div>
            
            <!-- Stop Price (if stop or stop-limit order) -->
            <div v-if="orderForm.order_type === 'STOP' || orderForm.order_type === 'STOP_LIMIT'">
              <label class="block text-sm font-medium text-gray-700">Stop Price</label>
              <div class="mt-1 flex items-center space-x-2">
                <span class="text-gray-500">$</span>
                <input
                  v-model="orderForm.stop_price"
                  type="number"
                  step="0.01"
                  min="0.01"
                  class="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                  @change="validateOrder"
                />
              </div>
            </div>
            
            <!-- Limit Price (if limit or stop-limit order) -->
            <div v-if="orderForm.order_type === 'LIMIT' || orderForm.order_type === 'STOP_LIMIT'">
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
          
          <!-- Middle Column - Trading Levels -->
          <div class="h-full flex flex-col space-y-3">
            <!-- Take Profit Levels Zone (Top) -->
            <div class="flex-1 bg-green-50 border border-green-200 rounded-lg p-4 min-h-[200px] flex flex-col">
              <!-- Header with Add Button -->
              <div class="flex items-center justify-between mb-4">
                <h5 class="text-sm font-medium text-green-800 flex items-center">
                  <svg class="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                  </svg>
                  Take Profit Levels
                </h5>
                <button
                  @click="addTakeProfitLevel"
                  class="w-8 h-8 bg-green-600 hover:bg-green-700 text-white rounded-md flex items-center justify-center focus:outline-none focus:ring-2 focus:ring-green-500"
                  title="Add Level"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
                  </svg>
                </button>
              </div>

              <!-- Levels Container (Stack from bottom up) -->
              <div class="flex-1 flex flex-col-reverse space-y-reverse space-y-2">
                <!-- No levels message -->
                <div v-if="takeProfitLevels.length === 0" class="flex-1 flex items-center justify-center">
                  <div class="text-center text-green-600">
                    <svg class="h-8 w-8 mx-auto mb-2 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                    </svg>
                    <p class="text-xs">Click + to add profit levels</p>
                  </div>
                </div>

                <!-- Level Bars -->
                <div
                  v-for="(level, index) in sortedTakeProfitLevels"
                  :key="level.id"
                  class="bg-green-100 border border-green-300 rounded-md p-2 shadow-sm"
                >
                  <div class="flex items-center justify-between w-full">
                    <div class="flex items-center space-x-2 flex-1">
                      <!-- Price Input -->
                      <div class="w-20">
                        <div class="flex items-center">
                          <span class="text-green-600 text-sm mr-1">$</span>
                          <input
                            v-model.number="level.price"
                            @input="validateLevelPrices"
                            type="number"
                            step="0.01"
                            min="0.01"
                            placeholder="0.00"
                            class="w-full px-1 py-1 text-sm border border-green-300 rounded focus:ring-green-500 focus:border-green-500 bg-white"
                          />
                        </div>
                      </div>

                      <!-- Percentage/Shares Input -->
                      <div class="w-16 flex items-center">
                        <!-- Bottom level (lowest price) shows calculated value -->
                        <div v-if="isBottomLevel(level)" class="w-full px-2 py-1 text-sm bg-green-200 border border-green-300 rounded text-green-800 font-medium text-center">
                          {{ formatLevelValue(level.calculatedValue) }}{{ orderForm.amountType === 'dollars' ? '%' : '' }}
                        </div>
                        
                        <!-- Other levels have input -->
                        <input
                          v-else
                          v-model.number="level.percentage"
                          @input="recalculateBottomLevel"
                          type="number"
                          :min="orderForm.amountType === 'dollars' ? 1 : 0.01"
                          :max="orderForm.amountType === 'dollars' ? getMaxPercentage(level) : getMaxShares(level)"
                          :step="orderForm.amountType === 'dollars' ? 1 : 0.01"
                          class="w-full px-1 py-1 text-sm border border-green-300 rounded focus:ring-green-500 focus:border-green-500 bg-white"
                        />
                      </div>
                      
                      <span v-if="orderForm.amountType === 'dollars'" class="text-green-600 text-sm">%</span>
                      
                      <!-- +/- buttons (only for non-bottom levels) -->
                      <div v-if="!isBottomLevel(level)" class="flex space-x-1">
                        <button
                          @click="adjustLevelValue(level, false)"
                          class="w-6 h-6 bg-green-600 hover:bg-green-700 text-white text-xs rounded focus:outline-none flex items-center justify-center"
                          title="Decrease"
                        >
                          -
                        </button>
                        <button
                          @click="adjustLevelValue(level, true)"
                          class="w-6 h-6 bg-green-600 hover:bg-green-700 text-white text-xs rounded focus:outline-none flex items-center justify-center"
                          title="Increase"
                        >
                          +
                        </button>
                      </div>
                    </div>
                    
                    <!-- Delete Button (far right) -->
                    <button
                      @click="removeTakeProfitLevel(level.id)"
                      class="w-6 h-6 text-red-600 hover:text-red-800 focus:outline-none flex items-center justify-center ml-2"
                      title="Delete Level"
                    >
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  </div>
                  
                  <!-- Live calculation display below -->
                  <div v-if="orderForm.amountType === 'dollars'" class="text-xs text-green-600 mt-1 text-center">
                    <span v-if="isBottomLevel(level)">
                      ${{ (orderForm.dollarAmount * level.calculatedValue / 100).toFixed(2) }}
                    </span>
                    <span v-else>
                      ${{ (orderForm.dollarAmount * (level.percentage || 0) / 100).toFixed(2) }}
                    </span>
                  </div>
                  <div v-else-if="orderForm.amountType === 'shares' && level.percentage > 0" class="text-xs text-green-600 mt-1 text-center">
                    {{ level.percentage }} shares
                  </div>
                </div>
              </div>
            </div>
            
            <!-- Entry Price Bar (Middle) -->
            <div class="bg-blue-100 border border-blue-300 rounded-lg p-3 shadow-sm">
              <div class="flex items-center justify-between">
                <span class="text-sm font-medium text-blue-800 flex items-center">
                  <svg class="h-4 w-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  Entry
                </span>
                <div class="text-sm text-blue-700 font-medium">
                  <span v-if="orderForm.order_type === 'MARKET'">
                    Market Order
                    <span v-if="marketData?.last" class="ml-1 text-blue-600">@ ${{ marketData.last.toFixed(2) }}</span>
                  </span>
                  <span v-else-if="orderForm.order_type === 'LIMIT' && orderForm.limit_price">
                    Limit @ ${{ Number(orderForm.limit_price).toFixed(2) }}
                  </span>
                  <span v-else-if="orderForm.order_type === 'STOP' && orderForm.stop_price">
                    Stop @ ${{ Number(orderForm.stop_price).toFixed(2) }}
                  </span>
                  <span v-else-if="orderForm.order_type === 'STOP_LIMIT' && orderForm.limit_price">
                    Stop-Limit @ ${{ Number(orderForm.limit_price).toFixed(2) }}
                  </span>
                  <span v-else class="text-blue-500">No Price Set</span>
                </div>
              </div>
            </div>
            
            <!-- Stop Loss Zone (Bottom) -->
            <div class="bg-red-50 border border-red-200 rounded-lg p-4 shadow-sm">
              <div class="flex items-center mb-3">
                <svg class="h-4 w-4 mr-2 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
                <h5 class="text-sm font-medium text-red-800">Stop Loss</h5>
              </div>
              
              <div class="space-y-3">
                <div>
                  <label class="block text-xs font-medium text-red-700 mb-1">Stop Price</label>
                  <div class="flex items-center space-x-2">
                    <span class="text-red-500 text-sm">$</span>
                    <input
                      v-model="orderForm.stop_loss_price"
                      type="number"
                      step="0.01"
                      min="0.01"
                      placeholder="0.00"
                      class="flex-1 px-2 py-1 text-sm border border-red-300 rounded focus:ring-red-500 focus:border-red-500 bg-white"
                    />
                  </div>
                  <p class="text-xs text-red-600 mt-1">Automatically sell if price drops to this level</p>
                </div>
              </div>
            </div>
          </div>
          
          <!-- Right Column - Order Preview & Account Info -->
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
  source?: string
  enhanced_data?: string
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
  stop_price: null as number | null,
  time_in_force: 'DAY',
  stop_loss_price: 0.00
})

// Take Profit Levels Management
interface TakeProfitLevel {
  id: number
  price: number
  percentage: number
  calculatedValue: number
}

const takeProfitLevels = ref<TakeProfitLevel[]>([])
let levelIdCounter = 1

// Add a new take profit level
const addTakeProfitLevel = () => {
  const newLevel: TakeProfitLevel = {
    id: levelIdCounter++,
    price: 0,
    percentage: orderForm.value.amountType === 'dollars' ? 10 : 1,
    calculatedValue: 0
  }
  takeProfitLevels.value.push(newLevel)
  // Trigger recalculation after adding
  setTimeout(() => recalculateBottomLevel(), 0)
}

// Remove a take profit level
const removeTakeProfitLevel = (levelId: number) => {
  takeProfitLevels.value = takeProfitLevels.value.filter(level => level.id !== levelId)
  // Trigger recalculation after removing
  setTimeout(() => recalculateBottomLevel(), 0)
}

// Get sorted levels by price (ascending = bottom to top display)
const sortedTakeProfitLevels = computed(() => {
  return [...takeProfitLevels.value].sort((a, b) => a.price - b.price)
})

// Check if a level is the bottom level (lowest price)
const isBottomLevel = (level: TakeProfitLevel) => {
  if (takeProfitLevels.value.length === 0) return false
  if (takeProfitLevels.value.length === 1) return true
  
  // Get all levels with valid prices (> 0)
  const levelsWithPrice = takeProfitLevels.value.filter(l => l.price > 0)
  
  // If no levels have prices set yet, the first level added should be bottom
  if (levelsWithPrice.length === 0) {
    return takeProfitLevels.value[0].id === level.id
  }
  
  // If only one level has a price, it's the bottom
  if (levelsWithPrice.length === 1) {
    return levelsWithPrice[0].id === level.id
  }
  
  // If this level doesn't have a price, it's not the bottom
  if (level.price <= 0) return false
  
  // Find the actual lowest price among levels with prices
  const lowestPrice = Math.min(...levelsWithPrice.map(l => l.price))
  return level.price === lowestPrice
}

// Recalculate the bottom level's percentage/shares
const recalculateBottomLevel = () => {
  if (takeProfitLevels.value.length === 0) return
  
  // For single level, it should always be 100% (or total shares)
  if (takeProfitLevels.value.length === 1) {
    const singleLevel = takeProfitLevels.value[0]
    if (orderForm.value.amountType === 'dollars') {
      singleLevel.calculatedValue = 100
    } else {
      singleLevel.calculatedValue = orderForm.value.quantity
    }
    return
  }
  
  // For multiple levels, find the bottom level
  const levelsWithPrice = takeProfitLevels.value.filter(l => l.price > 0)
  
  let bottomLevel
  if (levelsWithPrice.length === 0) {
    // No prices set yet, use first level as bottom
    bottomLevel = takeProfitLevels.value[0]
  } else if (levelsWithPrice.length === 1) {
    // Only one level has price, it's the bottom
    bottomLevel = levelsWithPrice[0]
  } else {
    // Multiple levels with prices, find lowest price
    bottomLevel = levelsWithPrice.reduce((min, level) => 
      level.price < min.price ? level : min
    )
  }
  
  if (orderForm.value.amountType === 'dollars') {
    // Calculate remaining percentage for bottom level
    const otherLevelsSum = takeProfitLevels.value
      .filter(l => l.id !== bottomLevel.id)
      .reduce((sum, level) => sum + (level.percentage || 0), 0)
    bottomLevel.calculatedValue = Math.max(0, 100 - otherLevelsSum)
  } else {
    // Calculate remaining shares for bottom level
    const otherLevelsSum = takeProfitLevels.value
      .filter(l => l.id !== bottomLevel.id)
      .reduce((sum, level) => sum + (level.percentage || 0), 0)
    bottomLevel.calculatedValue = Math.max(0, orderForm.value.quantity - otherLevelsSum)
  }
}

// Adjust level value with +/- buttons (increments of 10 for percentage)
const adjustLevelValue = (level: TakeProfitLevel, increase: boolean) => {
  if (isBottomLevel(level)) return // Bottom level is calculated, not adjustable
  
  if (orderForm.value.amountType === 'dollars') {
    // Percentage mode: increment/decrement by 10
    const currentValue = level.percentage || 0
    let newValue: number
    
    if (increase) {
      // Smart increment: 8->10, 10->20, 20->30, etc.
      if (currentValue < 10) {
        newValue = 10
      } else {
        newValue = Math.ceil(currentValue / 10) * 10 + 10
      }
    } else {
      // Smart decrement: 40->30, 30->20, 20->10, 10->0, etc.
      if (currentValue <= 10) {
        newValue = 0
      } else {
        newValue = Math.floor(currentValue / 10) * 10 - 10
      }
    }
    
    // Ensure we don't exceed the maximum allowed or go below 0
    const maxValue = getMaxPercentage(level)
    level.percentage = Math.min(maxValue, Math.max(0, newValue))
  } else {
    // Shares mode: increment by 1 or appropriate step
    const currentValue = level.percentage || 0
    const step = canTradeFractional.value ? 0.1 : 1
    const newValue = increase ? currentValue + step : currentValue - step
    const maxValue = getMaxShares(level)
    level.percentage = Math.min(maxValue, Math.max(0.01, newValue))
  }
  
  recalculateBottomLevel()
}

// Get maximum percentage a level can have
const getMaxPercentage = (level: TakeProfitLevel) => {
  const otherLevels = takeProfitLevels.value.filter(l => l.id !== level.id && !isBottomLevel(l))
  const otherLevelsSum = otherLevels.reduce((sum, l) => sum + (l.percentage || 0), 0)
  return Math.max(1, 100 - otherLevelsSum)
}

// Get maximum shares a level can have
const getMaxShares = (level: TakeProfitLevel) => {
  const otherLevels = takeProfitLevels.value.filter(l => l.id !== level.id && !isBottomLevel(l))
  const otherLevelsSum = otherLevels.reduce((sum, l) => sum + (l.percentage || 0), 0)
  return Math.max(0.01, orderForm.value.quantity - otherLevelsSum)
}

// Format level value for display
const formatLevelValue = (value: number) => {
  if (orderForm.value.amountType === 'dollars') {
    return value.toFixed(1)
  } else {
    return canTradeFractional.value ? value.toFixed(4) : value.toFixed(0)
  }
}

// Validate that level prices are in correct order
const validateLevelPrices = () => {
  // Automatically recalculate when prices change
  setTimeout(() => recalculateBottomLevel(), 0)
}

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
  
  let price: number
  
  // Determine the price to use based on order type
  if (orderForm.value.order_type === 'LIMIT' && orderForm.value.limit_price) {
    price = Number(orderForm.value.limit_price)
  } else if (orderForm.value.order_type === 'STOP' && orderForm.value.stop_price) {
    price = Number(orderForm.value.stop_price)
  } else if (orderForm.value.order_type === 'STOP_LIMIT' && orderForm.value.limit_price) {
    // For stop-limit, use limit price for cost calculation
    price = Number(orderForm.value.limit_price)
  } else {
    // Market order or incomplete stop/limit order
    price = marketData.value.last
  }
    
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
    
    // If signal has enhanced analysis data, use that order type
    let orderType = 'MARKET' // default
    let limitPrice = null
    let stopPrice = null
    
    // Check if we have enhanced analysis data with order type
    if (newSignal.enhanced_data) {
      try {
        const enhancedData = typeof newSignal.enhanced_data === 'string' 
          ? JSON.parse(newSignal.enhanced_data) 
          : newSignal.enhanced_data
        
        if (enhancedData.order_type) {
          orderType = enhancedData.order_type.toUpperCase()
          console.log('Using order type from enhanced analysis:', orderType)
        }
      } catch (e) {
        console.error('Error parsing enhanced_data:', e)
      }
    }
    
    // Fallback: If signal has a price but no enhanced data order type, default to limit order
    if (!newSignal.enhanced_data && newSignal.price) {
      orderType = 'LIMIT'
      limitPrice = newSignal.price
    } else if (orderType === 'LIMIT' && newSignal.price) {
      limitPrice = newSignal.price
    } else if ((orderType === 'STOP' || orderType === 'STOP_LIMIT') && newSignal.price) {
      stopPrice = newSignal.price
      if (orderType === 'STOP_LIMIT') {
        limitPrice = newSignal.price
      }
    }
    
    orderForm.value.order_type = orderType
    orderForm.value.limit_price = limitPrice
    orderForm.value.stop_price = stopPrice
    
    // Initialize stop loss price from signal
    if (newSignal.stop_loss) {
      orderForm.value.stop_loss_price = newSignal.stop_loss
    } else {
      orderForm.value.stop_loss_price = 0.00
    }
    
    // Reset take profit levels when signal changes
    takeProfitLevels.value = []
    levelIdCounter = 1
    
    // Pre-fill take profit levels if converting from a signal (has signal data)
    if (newSignal.id > 0 && newSignal.enhanced_data) {
      // Use setTimeout to ensure the levels are created after the DOM updates
      setTimeout(() => {
        try {
          // Parse enhanced_data to get take profit levels
          const enhancedData = typeof newSignal.enhanced_data === 'string' 
            ? JSON.parse(newSignal.enhanced_data) 
            : newSignal.enhanced_data
          
          // Look for take_profit_levels array in enhanced data
          if (enhancedData.take_profit_levels && Array.isArray(enhancedData.take_profit_levels)) {
            const profitLevels = enhancedData.take_profit_levels
            console.log('Found take profit levels from analysis:', profitLevels)
            
            // Create a level for each profit target
            profitLevels.forEach((_price: any, _index: number) => {
              addTakeProfitLevel()
            })
            
            // Wait for levels to be created, then set prices and percentages
            setTimeout(() => {
              profitLevels.forEach((price: any, index: number) => {
                if (takeProfitLevels.value[index]) {
                  takeProfitLevels.value[index].price = Number(price)
                  // Set 10% for all levels except the last one (which gets calculated remainder)
                  if (index < profitLevels.length - 1) {
                    takeProfitLevels.value[index].percentage = 10
                  }
                }
              })
              
              // Recalculate to set the bottom level percentage
              recalculateBottomLevel()
              console.log('Pre-filled', profitLevels.length, 'take profit levels')
            }, 50)
                     } else if (newSignal.take_profit && typeof newSignal.take_profit === 'number') {
             // Fallback: if no enhanced data levels but has single take_profit
             addTakeProfitLevel()
             setTimeout(() => {
               if (takeProfitLevels.value.length > 0) {
                 takeProfitLevels.value[0].price = newSignal.take_profit as number
                 takeProfitLevels.value[0].percentage = 10
                 recalculateBottomLevel()
               }
             }, 50)
           }
        } catch (error) {
          console.error('Error parsing enhanced_data for take profit levels:', error)
          console.log('Enhanced data:', newSignal.enhanced_data)
        }
      }, 50)
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
  
  // Recalculate take profit levels when switching amount types
  recalculateBottomLevel()
})

// Watch for dollar amount changes to recalculate take profit levels
watch(() => orderForm.value.dollarAmount, () => {
  recalculateBottomLevel()
})

// Watch for quantity changes to recalculate take profit levels  
watch(() => orderForm.value.quantity, () => {
  recalculateBottomLevel()
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
      stop_price: orderForm.value.stop_price,
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
      // Check if this is a position close
      if (props.signal.source === 'close_position') {
        // Use the close-position endpoint for proper P&L tracking
        const response = await axios.post('/api/trades/close-position', {
          symbol: orderForm.value.symbol,
          quantity: orderForm.value.quantity,
          order_type: orderForm.value.order_type,
          limit_price: orderForm.value.limit_price,
          stop_price: orderForm.value.stop_price,
          time_in_force: orderForm.value.time_in_force
        })
        emit('executed', response.data)
        close()
      } else {
        // Regular new signal flow
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
          stop_price: orderForm.value.stop_price,
          time_in_force: orderForm.value.time_in_force,
          take_profit_levels: takeProfitLevels.value.filter(level => level.price > 0),
          stop_loss_price: orderForm.value.stop_loss_price
        })
        emit('executed', response.data)
        close()
      }
    } else {
      // Existing flow for already created signals
      await axios.post(`/api/signals/${props.signal.id}/approve`, { approved: true })
      const response = await axios.post(`/api/trades/execute/${props.signal.id}`, {
        quantity: orderForm.value.quantity,
        order_type: orderForm.value.order_type,
        limit_price: orderForm.value.limit_price,
        stop_price: orderForm.value.stop_price,
        time_in_force: orderForm.value.time_in_force,
        take_profit_levels: takeProfitLevels.value.filter(level => level.price > 0),
        stop_loss_price: orderForm.value.stop_loss_price
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
    stop_price: null,
    time_in_force: 'DAY',
    stop_loss_price: 0.00
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