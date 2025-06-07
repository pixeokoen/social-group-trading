<template>
  <div class="price-timeline flex items-center justify-center" style="height: 320px;">
    <div class="relative flex flex-col items-center w-48" style="height: 320px; margin-left: 20px;">
      
      <div class="relative flex items-center w-full" style="height: 320px;">
        
        <!-- Left Price Labels (fixed levels only) -->
      <div class="relative w-24 pr-3" style="height: 100%;">
        <div 
          v-for="level in debugLevels" 
          :key="`label-${level.type}-${level.id}`"
          class="absolute right-3 flex items-center whitespace-nowrap"
          :style="{ 
            top: level.topPercent + '%',
            transform: 'translateY(-50%)',
            zIndex: 10
          }"
        >
          <div class="text-right flex items-center">
            <!-- Status Icon for Take Profit levels -->
            <div v-if="level.type === 'takeProfit'" class="mr-1.5">
              <!-- Check Icon (Executed) -->
              <svg v-if="level.isExecuted" class="w-3 h-3 text-emerald-600" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
              </svg>
              <!-- Waiting Icon (Pending) -->
              <svg v-else class="w-3 h-3 text-slate-400" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clip-rule="evenodd" />
              </svg>
            </div>
            
            <!-- Percentage Pill for Take Profit levels -->
            <div v-if="level.type === 'takeProfit'" class="mr-2">
              <span 
                :class="[
                  'text-xs font-medium px-1.5 py-0.5 rounded-full',
                  level.isExecuted 
                    ? 'bg-emerald-100 text-emerald-700' 
                    : 'bg-slate-100 text-slate-600'
                ]"
              >
                {{ level.percentage }}%
              </span>
            </div>
            
            <div 
              :class="[
                'text-sm font-semibold',
                level.color
              ]"
            >
              ${{ level.price.toFixed(2) }}
            </div>
          </div>
        </div>
      </div>

      <!-- Central Thermometer Bar -->
      <div class="relative w-3 bg-gradient-to-t from-slate-400 to-slate-300 rounded-full shadow-inner border border-slate-500" style="height: 100%;">
        
        <!-- Fixed Level Lines (stick out to the left) -->
        <div 
          v-for="level in debugLevels" 
          :key="`line-${level.type}-${level.id}`"
          class="absolute"
          :style="{ 
            top: level.topPercent + '%',
            right: '50%',
            transform: 'translateY(-50%)',
            zIndex: 20
          }"
        >
          <div 
            :class="[
              'h-0.5 bg-white shadow-sm',
              level.stripeClass
            ]"
            style="width: 12px;"
          ></div>
        </div>

        <!-- Current Price Line (stick out to the right) -->
        <div 
          class="absolute"
          :style="{ 
            top: currentTopPercent + '%',
            left: '50%',
            transform: 'translateY(-50%)',
            zIndex: 30
          }"
        >
          <div class="h-0.5 bg-blue-600 shadow-sm border-r-4 border-blue-600" style="width: 12px;"></div>
        </div>
      </div>

      <!-- Right Current Price Label -->
      <div class="relative w-16 pl-3" style="height: 100%;">
        <div 
          class="absolute left-3 flex items-center whitespace-nowrap transition-all duration-500 ease-out"
          :style="{ 
            top: currentTopPercent + '%',
            transform: 'translateY(-50%)',
            zIndex: 10
          }"
        >
          <div class="text-left flex items-center gap-1">
            <div class="text-sm font-bold transition-all duration-300"
                 :class="{ 
                   'scale-110': isPriceUpdating,
                   'text-emerald-600': priceDirection === 'up',
                   'text-rose-600': priceDirection === 'down',
                   'text-blue-600': priceDirection === 'same'
                 }">
              ${{ displayPrice.toFixed(2) }}
            </div>
            <!-- Animated Heartbeat Icon -->
            <svg 
              class="w-3 h-3 text-red-500" 
              :class="{ 'animate-ping': isPriceUpdating, 'animate-pulse': !isPriceUpdating }"
              fill="currentColor" 
              viewBox="0 0 20 20"
            >
              <path fill-rule="evenodd" d="M3.172 5.172a4 4 0 015.656 0L10 6.343l1.172-1.171a4 4 0 115.656 5.656L10 17.657l-6.828-6.829a4 4 0 010-5.656z" clip-rule="evenodd" />
            </svg>
          </div>
        </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'

interface TakeProfitLevel {
  id: number
  level_number: number
  price: number
  shares_quantity: number
  status: string
  percentage?: number
}

interface Props {
  position: any
  entryPrice: number
  currentPrice: number
  stopLoss?: number
  takeProfitLevels: TakeProfitLevel[]
  scaleSettings?: {
    topPercent: number
    bottomPercent: number
  }
}

const props = defineProps<Props>()

// Animation states
const isPriceUpdating = ref(false)
const priceDirection = ref<'up' | 'down' | 'same'>('same')
const displayPrice = ref(props.currentPrice)
const lastPrice = ref(props.currentPrice)

// Watch for price changes and trigger animations
watch(() => props.currentPrice, (newPrice, oldPrice) => {
  if (newPrice && newPrice > 0 && oldPrice && newPrice !== oldPrice) {
    // Check if this is a meaningful price change (not entry<->market flip)
    const entryPrice = props.entryPrice
    const isEntryToMarket = (oldPrice === entryPrice && newPrice !== entryPrice) || 
                            (oldPrice !== entryPrice && newPrice === entryPrice)
    
    // Update display price
    displayPrice.value = newPrice
    
    if (!isEntryToMarket) {
      // Only animate real market price changes, not entry<->market flips
      // Determine direction
      if (newPrice > oldPrice) {
        priceDirection.value = 'up'
      } else if (newPrice < oldPrice) {
        priceDirection.value = 'down'
      } else {
        priceDirection.value = 'same'
      }
      
      // Trigger update animation
      isPriceUpdating.value = true
      
      // Reset animation after 1 second
      setTimeout(() => {
        isPriceUpdating.value = false
        priceDirection.value = 'same'
      }, 1000)
    } else {
      // Just heartbeat for entry<->market transitions
      isPriceUpdating.value = true
      setTimeout(() => {
        isPriceUpdating.value = false
      }, 500)
    }
    
    lastPrice.value = newPrice
  } else if (newPrice && newPrice > 0) {
    // Price update without change (still trigger heartbeat)
    displayPrice.value = newPrice
    isPriceUpdating.value = true
    
    setTimeout(() => {
      isPriceUpdating.value = false
    }, 500)
  }
}, { immediate: true })

// Initialize display price
if (props.currentPrice && props.currentPrice > 0) {
  displayPrice.value = props.currentPrice
}

// Check if this is a basic position (no enhanced features)
const isBasicPosition = computed(() => {
  return !props.takeProfitLevels || props.takeProfitLevels.length === 0
})

// Calculate realized P&L from executed take profit levels
const realizedPnl = computed(() => {
  return props.takeProfitLevels
    .filter(tp => tp.status === 'executed')
    .reduce((total, tp) => {
      const gainPerShare = tp.price - props.entryPrice
      return total + (gainPerShare * tp.shares_quantity)
    }, 0)
})

// Calculate floating P&L from remaining shares
const remainingFloatingPnl = computed(() => {
  const totalShares = props.position?.quantity || 150
  const executedShares = props.takeProfitLevels
    .filter(tp => tp.status === 'executed')
    .reduce((total, tp) => total + tp.shares_quantity, 0)
  
  const remainingShares = totalShares - executedShares
  return (props.currentPrice - props.entryPrice) * remainingShares
})

// Simple debug approach - calculate positions step by step
const debugLevels = computed(() => {
  const levels = []
  
  // Collect all prices first
  const allPrices = [props.currentPrice]
  
  // Add take profit levels with allocation percentages
  props.takeProfitLevels.forEach(tp => {
    levels.push({
      id: tp.id,
      type: 'takeProfit',
      price: tp.price,
      percentage: tp.percentage || Math.round((tp.shares_quantity / 150) * 100), // Use provided percentage or calculate
      color: tp.status === 'executed' ? 'text-emerald-600' : 'text-slate-600',
      stripeClass: tp.status === 'executed' ? 'border-l-4 border-emerald-600' : 'border-l-4 border-slate-500',
      isExecuted: tp.status === 'executed'
    })
    allPrices.push(tp.price)
  })
  
  // Add entry level
  levels.push({
    id: 'entry',
    type: 'entry',
    price: props.entryPrice,
    percentage: '0.0', // Entry is baseline
    color: 'text-slate-800',
    stripeClass: 'border-l-4 border-slate-700',
    isExecuted: false
  })
  allPrices.push(props.entryPrice)
  
  // Add stop loss
  if (props.stopLoss) {
    // Calculate percentage loss from entry price
    const percentageLoss = ((props.stopLoss - props.entryPrice) / props.entryPrice * 100)
    
    levels.push({
      id: 'stopLoss',
      type: 'stopLoss',
      price: props.stopLoss,
      percentage: percentageLoss.toFixed(1),
      color: 'text-rose-600',
      stripeClass: 'border-l-4 border-rose-500',
      isExecuted: false
    })
    allPrices.push(props.stopLoss)
  }
  
  // Calculate min/max based on position type
  let adjustedMin: number, adjustedMax: number, adjustedRange: number
  
  if (isBasicPosition.value) {
    // For basic positions, use entry price + scale settings
    const entryPrice = props.entryPrice
    const topPercent = props.scaleSettings?.topPercent || 10
    const bottomPercent = props.scaleSettings?.bottomPercent || 5
    adjustedMax = entryPrice + (entryPrice * topPercent / 100)
    adjustedMin = entryPrice - (entryPrice * bottomPercent / 100)
    adjustedRange = adjustedMax - adjustedMin
  } else {
    // For enhanced positions, use existing logic with padding
    const minPrice = Math.min(...allPrices)
    const maxPrice = Math.max(...allPrices)
    const priceRange = maxPrice - minPrice
    const padding = priceRange * 0.15
    
    adjustedMin = minPrice - padding
    adjustedMax = maxPrice + padding
    adjustedRange = adjustedMax - adjustedMin
  }
  
  console.log('Price calculation:', {
    adjustedMin,
    adjustedMax,
    adjustedRange,
    isBasic: isBasicPosition.value
  })
  
  // Calculate positions for each level
  const levelsWithPositions = levels.map(level => {
    // Top position: 0% = top of container, 100% = bottom
    // Higher prices should be at top (lower percentage)
    const topPercent = ((adjustedMax - level.price) / adjustedRange) * 100
    
    console.log(`Level ($${level.price}): ${topPercent.toFixed(1)}%`)
    
    return {
      ...level,
      topPercent: Math.max(5, Math.min(95, topPercent)) // Clamp between 5% and 95%
    }
  })
  
  return levelsWithPositions
})

const currentTopPercent = computed(() => {
  let adjustedMin: number, adjustedMax: number, adjustedRange: number
  
  if (isBasicPosition.value) {
    // For basic positions, use entry price + scale settings
    const entryPrice = props.entryPrice
    const topPercent = props.scaleSettings?.topPercent || 10
    const bottomPercent = props.scaleSettings?.bottomPercent || 5
    adjustedMax = entryPrice + (entryPrice * topPercent / 100)
    adjustedMin = entryPrice - (entryPrice * bottomPercent / 100)
    adjustedRange = adjustedMax - adjustedMin
  } else {
    // For enhanced positions, use existing logic with padding
    const allPrices = [props.currentPrice, props.entryPrice]
    props.takeProfitLevels.forEach(tp => allPrices.push(tp.price))
    if (props.stopLoss) allPrices.push(props.stopLoss)
    
    const minPrice = Math.min(...allPrices)
    const maxPrice = Math.max(...allPrices)
    const priceRange = maxPrice - minPrice
    const padding = priceRange * 0.15
    
    adjustedMin = minPrice - padding
    adjustedMax = maxPrice + padding
    adjustedRange = adjustedMax - adjustedMin
  }
  
  const topPercent = ((adjustedMax - props.currentPrice) / adjustedRange) * 100
  console.log(`Current price ($${props.currentPrice}): ${topPercent.toFixed(1)}%`)
  
  return Math.max(5, Math.min(95, topPercent))
})
</script>

<style scoped>
.price-timeline {
  min-height: 320px;
  max-height: 100%;
}
</style> 