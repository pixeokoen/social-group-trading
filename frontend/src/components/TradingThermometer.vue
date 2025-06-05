<template>
  <div class="trading-thermometer h-full flex items-center">
    <!-- Price Labels (Left Side) -->
    <div class="flex flex-col justify-between h-full w-16 text-xs text-gray-600 pr-2">
      <!-- Take Profit Levels (Top) -->
      <div v-for="(tp, index) in sortedTakeProfitLevels" :key="`tp-${index}`" class="text-right">
        <div 
          :class="[
            'font-medium',
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
        class="text-right transition-all duration-500 ease-in-out"
        :style="{ transform: `translateY(${currentPriceOffset}px)` }"
      >
        <div class="font-semibold text-blue-600 bg-blue-50 px-1 rounded">
          ${{ formatPrice(currentPrice) }}
        </div>
        <div class="text-xs text-blue-500">CURRENT</div>
      </div>
      
      <!-- Entry Price (Zero Level) -->
      <div class="text-right">
        <div class="font-medium text-gray-900 bg-gray-100 px-1 rounded">
          ${{ formatPrice(entryPrice) }}
        </div>
        <div class="text-xs text-gray-500">ENTRY</div>
      </div>
      
      <!-- Stop Loss (Bottom) -->
      <div v-if="stopLoss" class="text-right">
        <div 
          :class="[
            'font-medium',
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
    </div>
    
    <!-- Thermometer Bar -->
    <div class="relative w-6 h-full bg-gray-200 rounded-full overflow-hidden">
      <!-- Background Segments -->
      
      <!-- Loss Area (Red - Below Entry) -->
      <div 
        class="absolute bottom-0 w-full bg-red-200 transition-all duration-300"
        :style="{ height: `${lossAreaHeight}%` }"
      ></div>
      
      <!-- Profit Areas (Green - Above Entry) -->
      <div 
        v-for="(tp, index) in sortedTakeProfitLevels" 
        :key="`area-${index}`"
        class="absolute w-full transition-all duration-300"
        :class="[
          tp.status === 'executed' ? 'bg-gray-300' : (
            index === 0 ? 'bg-green-200' : 
            index === 1 ? 'bg-green-300' : 
            index === 2 ? 'bg-green-400' : 'bg-green-500'
          )
        ]"
        :style="{ 
          bottom: `${getTakeProfitHeight(index).bottom}%`, 
          height: `${getTakeProfitHeight(index).height}%` 
        }"
      ></div>
      
      <!-- Entry Price Line (Zero Level) -->
      <div 
        class="absolute w-full h-0.5 bg-gray-800 z-10"
        :style="{ bottom: `${entryLinePosition}%` }"
      ></div>
      
      <!-- Current Price Indicator (Moving) -->
      <div 
        class="absolute w-full h-1 bg-blue-500 z-20 transition-all duration-500 ease-in-out rounded-full shadow-lg"
        :style="{ bottom: `${currentPricePosition}%` }"
      >
        <!-- Animated pulse -->
        <div class="absolute inset-0 bg-blue-400 rounded-full animate-pulse opacity-75"></div>
      </div>
      
      <!-- Stop Loss Line -->
      <div 
        v-if="stopLoss && stopLossPosition >= 0"
        class="absolute w-full h-0.5 bg-red-600 z-10"
        :style="{ bottom: `${stopLossPosition}%` }"
      ></div>
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
    // Scenario 2: Scale based on actual levels
    const prices = [props.entryPrice, props.currentPrice]
    
    if (props.stopLoss) prices.push(props.stopLoss)
    props.takeProfitLevels.forEach(tp => prices.push(tp.price))
    
    const minPrice = Math.min(...prices)
    const maxPrice = Math.max(...prices)
    const padding = (maxPrice - minPrice) * 0.15 // 15% padding for margins
    
    return {
      min: minPrice - padding,
      max: maxPrice + padding,
      range: (maxPrice - minPrice) + (padding * 2)
    }
  } else {
    // Scenario 1: Simple thermometer with entry at 1/3 from bottom
    const priceDiff = Math.abs(props.currentPrice - props.entryPrice)
    const range = Math.max(priceDiff * 4, props.entryPrice * 0.2) // At least 20% of entry price
    
    // Entry at 1/3 from bottom means 2/3 above, 1/3 below
    const bottomSpace = range * 0.33
    const topSpace = range * 0.67
    
    return {
      min: props.entryPrice - bottomSpace,
      max: props.entryPrice + topSpace,
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

const lossAreaHeight = computed(() => {
  if (!props.stopLoss) return entryLinePosition.value
  return Math.max(0, entryLinePosition.value - stopLossPosition.value)
})

const sortedTakeProfitLevels = computed(() => {
  return [...props.takeProfitLevels]
    .filter(tp => tp.status === 'pending')
    .sort((a, b) => a.level_number - b.level_number)
})

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