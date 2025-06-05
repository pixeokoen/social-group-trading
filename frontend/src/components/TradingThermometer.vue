<template>
  <div class="trading-thermometer h-full flex items-center">
    <!-- Price Labels (Left Side) -->
    <div class="flex flex-col justify-start h-full w-16 text-xs text-gray-600 pr-2 relative">
      <!-- Stop Loss (Bottom) -->
      <div 
        v-if="stopLoss" 
        class="absolute text-right w-full"
        :style="{ bottom: `${stopLossPosition}%` }"
      >
        <div 
          :class="[
            'font-medium text-xs',
            position.stop_loss_status === 'executed' ? 'text-gray-500 line-through' : 'text-red-600'
          ]"
        >
          ${{ formatPrice(stopLoss) }}
        </div>
        <div class="text-xs text-gray-500">
          STOP
          <span v-if="position.stop_loss_status === 'executed'" class="text-red-600">✓</span>
        </div>
      </div>
      
      <!-- Entry Price (Zero Level) -->
      <div 
        class="absolute text-right w-full"
        :style="{ bottom: `${entryLinePosition}%` }"
      >
        <div class="font-medium text-xs text-gray-900 bg-gray-100 px-1 rounded">
          ${{ formatPrice(entryPrice) }}
        </div>
        <div class="text-xs text-gray-500">ENTRY</div>
      </div>
      
      <!-- Take Profit Levels -->
      <div 
        v-for="(tp, index) in sortedTakeProfitLevels" 
        :key="`tp-${index}`" 
        class="absolute text-right w-full"
        :style="{ bottom: `${getTakeProfitPosition(tp)}%` }"
      >
        <div 
          :class="[
            'font-medium text-xs',
            tp.status === 'executed' ? 'text-gray-500 line-through' : 'text-green-600'
          ]"
        >
          ${{ formatPrice(tp.price) }}
        </div>
        <div class="text-xs text-gray-500">
          {{ formatQuantity(tp.shares_quantity) }}sh
          <span v-if="tp.status === 'executed'" class="text-green-600">✓</span>
        </div>
      </div>
      
      <!-- Current Price (Moving) -->
      <div 
        class="absolute text-right w-full transition-all duration-500 ease-in-out z-30"
        :style="{ 
          bottom: `${currentPricePosition}%`,
          transform: `translateY(${currentPriceOffset}px)` 
        }"
      >
        <div class="font-semibold text-xs text-blue-600 bg-blue-50 px-1 rounded shadow">
          ${{ formatPrice(currentPrice) }}
        </div>
        <div class="text-xs text-blue-500">NOW</div>
      </div>
    </div>
    
    <!-- Thermometer Bar -->
    <div class="relative w-6 h-full bg-gray-200 rounded-full overflow-hidden">
      <!-- Red Area (Loss - Below Entry) -->
      <div 
        class="absolute bottom-0 w-full bg-red-300 transition-all duration-300"
        :style="{ height: `${entryLinePosition}%` }"
      ></div>
      
      <!-- Green Area (Profit - Above Entry) -->
      <div 
        class="absolute w-full bg-green-300 transition-all duration-300"
        :style="{ 
          bottom: `${entryLinePosition}%`,
          height: `${100 - entryLinePosition}%`
        }"
      ></div>
      
      <!-- Horizontal Lines for Levels -->
      
      <!-- Stop Loss Line -->
      <div 
        v-if="stopLoss && stopLossPosition >= 0"
        class="absolute w-full h-0.5 bg-red-700 z-10"
        :style="{ bottom: `${stopLossPosition}%` }"
      ></div>
      
      <!-- Entry Price Line (Bold - Zero Level) -->
      <div 
        class="absolute w-full h-1 bg-gray-900 z-10"
        :style="{ bottom: `${entryLinePosition}%` }"
      ></div>
      
      <!-- Take Profit Lines -->
      <div 
        v-for="tp in sortedTakeProfitLevels" 
        :key="`line-${tp.id}`"
        class="absolute w-full h-0.5 z-10 transition-all duration-300"
        :class="tp.status === 'executed' ? 'bg-gray-600' : 'bg-green-700'"
        :style="{ bottom: `${getTakeProfitPosition(tp)}%` }"
      ></div>
      
      <!-- Current Price Indicator (Moving) -->
      <div 
        class="absolute w-full h-1 bg-blue-500 z-20 transition-all duration-500 ease-in-out rounded-full shadow-lg"
        :style="{ bottom: `${currentPricePosition}%` }"
      >
        <!-- Animated pulse -->
        <div class="absolute inset-0 bg-blue-400 rounded-full animate-pulse opacity-75"></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, watch, ref } from 'vue'

interface TakeProfitLevel {
  id: number
  level_number: number
  price: number
  shares_quantity: number
  status: string
}

interface Props {
  position: any
  entryPrice: number
  currentPrice: number
  stopLoss?: number
  takeProfitLevels: TakeProfitLevel[]
}

const props = defineProps<Props>()

// Animation state
const currentPriceOffset = ref(0)

// Computed properties for price positioning
const priceRange = computed(() => {
  const hasLevels = props.takeProfitLevels.length > 0 || props.stopLoss
  
  if (hasLevels) {
    // Scale from stop loss (bottom) to highest take profit (top)
    const allPrices = [props.entryPrice]
    
    if (props.stopLoss) allPrices.push(props.stopLoss)
    props.takeProfitLevels.forEach(tp => allPrices.push(tp.price))
    
    const minPrice = Math.min(...allPrices)
    const maxPrice = Math.max(...allPrices)
    const range = maxPrice - minPrice
    const padding = range * 0.1 // 10% padding
    
    return {
      min: minPrice - padding,
      max: maxPrice + padding,
      range: range + (padding * 2)
    }
  } else {
    // Simple view: entry in middle, space above and below
    const range = Math.max(Math.abs(props.currentPrice - props.entryPrice) * 3, props.entryPrice * 0.2)
    return {
      min: props.entryPrice - range * 0.4,
      max: props.entryPrice + range * 0.6,
      range: range
    }
  }
})

const entryLinePosition = computed(() => {
  const { min, range } = priceRange.value
  return ((props.entryPrice - min) / range) * 100
})

const currentPricePosition = computed(() => {
  const { min, range } = priceRange.value
  return ((props.currentPrice - min) / range) * 100
})

const stopLossPosition = computed(() => {
  if (!props.stopLoss) return -1
  const { min, range } = priceRange.value
  return ((props.stopLoss - min) / range) * 100
})



const sortedTakeProfitLevels = computed(() => {
  return [...props.takeProfitLevels]
    .filter(tp => tp.status === 'pending')
    .sort((a, b) => a.level_number - b.level_number)
})

const getTakeProfitPosition = (tp: any) => {
  const { min, range } = priceRange.value
  return ((tp.price - min) / range) * 100
}

const getTakeProfitHeight = (index: number) => {
  const levels = sortedTakeProfitLevels.value
  if (index >= levels.length) return { bottom: 0, height: 0 }
  
  const { min, range } = priceRange.value
  const currentLevel = levels[index]
  const nextLevel = levels[index + 1]
  
  const currentPos = ((currentLevel.price - min) / range) * 100
  const nextPos = nextLevel ? ((nextLevel.price - min) / range) * 100 : 100
  
  return {
    bottom: Math.max(currentPos, entryLinePosition.value),
    height: nextPos - Math.max(currentPos, entryLinePosition.value)
  }
}

// Helper functions
const formatPrice = (price: number | undefined) => {
  if (price === null || price === undefined) return 'N/A'
  const numPrice = typeof price === 'string' ? parseFloat(price) : price
  return isNaN(numPrice) ? 'N/A' : numPrice.toFixed(2)
}

const formatQuantity = (quantity: number | string) => {
  const numQuantity = typeof quantity === 'string' ? parseFloat(quantity) : quantity
  if (isNaN(numQuantity)) return '0'
  return numQuantity === Math.floor(numQuantity) ? numQuantity.toString() : numQuantity.toFixed(1)
}

// Watch for price changes and animate
watch(() => props.currentPrice, (newPrice, oldPrice) => {
  if (oldPrice && newPrice !== oldPrice) {
    // Trigger a small animation offset
    const direction = newPrice > oldPrice ? -2 : 2
    currentPriceOffset.value = direction
    
    // Reset after animation
    setTimeout(() => {
      currentPriceOffset.value = 0
    }, 100)
  }
}, { immediate: false })
</script>

<style scoped>
.trading-thermometer {
  min-height: 200px;
}
</style> 