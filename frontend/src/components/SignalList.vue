<template>
  <div class="bg-white shadow overflow-hidden sm:rounded-md">
    <ul class="divide-y divide-gray-200">
      <li v-for="signal in signals" :key="signal.id" class="px-4 sm:px-6 py-4 hover:bg-gray-50">
        <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-3 sm:space-y-0">
          <div class="flex items-start sm:items-center space-x-3">
            <div class="flex-shrink-0">
              <span
                :class="[
                  signal.action === 'BUY' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800',
                  'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium'
                ]"
              >
                {{ signal.action }}
              </span>
            </div>
            <div class="min-w-0 flex-1">
              <div class="flex items-center space-x-2">
                <p class="text-sm font-medium text-gray-900 truncate">
                  {{ signal.symbol }}
                </p>
                <span
                  :class="[
                    'inline-flex items-center px-2 py-0.5 rounded text-xs font-medium',
                    signal.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                    signal.status === 'approved' ? 'bg-green-100 text-green-800' :
                    'bg-blue-100 text-blue-800'
                  ]"
                >
                  {{ signal.status }}
                </span>
                <span
                  v-if="signal.source === 'manual_entry'"
                  class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800"
                >
                  Manual
                </span>
                <span
                  v-if="signal.source === 'message_paste'"
                  class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-indigo-100 text-indigo-800"
                >
                  Analyzed
                </span>
                <!-- Analysis Info Button for analyzed signals -->
                <button
                  v-if="signal.source === 'message_paste' && (signal.enhanced_data || signal.analysis_notes)"
                  @click="showAnalysisModal(signal)"
                  class="inline-flex items-center p-1 rounded-full text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  title="View AI Analysis Details"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </button>
                <span
                  v-if="signal.source === 'whatsapp'"
                  class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-800"
                >
                  WhatsApp
                </span>
                <span
                  v-if="signal.source === 'telegram'"
                  class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800"
                >
                  Telegram
                </span>
              </div>
              <div class="mt-1 text-sm text-gray-500">
                <span v-if="signal.quantity">{{ signal.quantity }} shares</span>
                <span v-if="signal.price"> @ ${{ signal.price }}</span>
                <span v-if="!signal.quantity && !signal.price" class="italic">Price pending</span>
              </div>
              <div v-if="signal.stop_loss || signal.take_profit" class="mt-1 text-xs text-gray-500">
                <span v-if="signal.stop_loss">SL: ${{ signal.stop_loss }}</span>
                <span v-if="signal.stop_loss && signal.take_profit" class="mx-1">•</span>
                <span v-if="signal.take_profit">TP: ${{ signal.take_profit }}</span>
              </div>
              <div v-if="signal.original_message" class="mt-2 text-xs text-gray-400 italic">
                "{{ signal.original_message.substring(0, 100) }}{{ signal.original_message.length > 100 ? '...' : '' }}"
              </div>
              <div v-if="signal.remarks" class="mt-1 text-xs text-gray-600">
                <span class="font-medium">Remarks:</span> {{ signal.remarks }}
              </div>
              <div v-if="signal.analysis_notes" class="mt-1 text-xs text-gray-500">
                <span class="font-medium">Analysis:</span> {{ signal.analysis_notes }}
              </div>
            </div>
          </div>
          
          <div class="flex items-center space-x-2 ml-11 sm:ml-0">
            <!-- Pending signals - show convert to trade and delete buttons -->
            <template v-if="signal.status === 'pending'">
              <button
                @click="$emit('approve', signal)"
                class="inline-flex items-center px-3 py-1 border border-transparent text-xs rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                </svg>
                Convert
              </button>
              <button
                @click="$emit('cancel', signal.id)"
                class="inline-flex items-center px-3 py-1 border border-transparent text-xs rounded-md text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
              >
                <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
                Delete
              </button>
            </template>
            
            <!-- Approved signals - show execute and delete buttons -->
            <template v-else-if="signal.status === 'approved'">
              <button
                @click="$emit('execute', signal.id)"
                class="inline-flex items-center px-3 py-1 border border-transparent text-xs rounded-md text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
              >
                <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
                </svg>
                Execute
              </button>
              <button
                @click="$emit('cancel', signal.id)"
                class="inline-flex items-center px-3 py-1 border border-transparent text-xs rounded-md text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
              >
                <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
                Delete
              </button>
            </template>
            
            <!-- Executed signals - show status -->
            <template v-else-if="signal.status === 'executed'">
              <span class="inline-flex items-center px-3 py-1 border border-transparent text-xs rounded-md text-gray-600 bg-gray-100">
                Executed
              </span>
            </template>
          </div>
        </div>
      </li>
    </ul>
    <div v-if="signals.length === 0" class="text-center py-12">
      <p class="text-gray-500">No signals available</p>
    </div>

    <!-- Analysis Details Modal -->
    <div v-if="showAnalysisDetailsModal" class="fixed z-50 inset-0 overflow-y-auto">
      <div class="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div class="fixed inset-0 transition-opacity" @click="closeAnalysisModal">
          <div class="absolute inset-0 bg-gray-500 opacity-75"></div>
        </div>
        
        <div class="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-4xl sm:w-full">
          <div class="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
            <div class="flex items-start justify-between mb-4">
              <h3 class="text-lg leading-6 font-medium text-gray-900">AI Analysis Details</h3>
              <button @click="closeAnalysisModal" class="text-gray-400 hover:text-gray-600">
                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            
            <div v-if="selectedAnalysisSignal" class="space-y-4">
              <!-- Signal Overview -->
              <div class="bg-gray-50 rounded-lg p-4">
                <h4 class="font-medium text-gray-900 mb-2">Signal Summary</h4>
                <div class="grid grid-cols-2 gap-4 text-sm">
                  <div><span class="font-medium">Symbol:</span> {{ selectedAnalysisSignal.symbol }}</div>
                  <div><span class="font-medium">Action:</span> {{ selectedAnalysisSignal.action }}</div>
                  <div v-if="selectedAnalysisSignal.price"><span class="font-medium">Entry Price:</span> ${{ selectedAnalysisSignal.price }}</div>
                  <div v-if="selectedAnalysisSignal.stop_loss"><span class="font-medium">Stop Loss:</span> ${{ selectedAnalysisSignal.stop_loss }}</div>
                  <div v-if="selectedAnalysisSignal.take_profit"><span class="font-medium">Take Profit:</span> ${{ selectedAnalysisSignal.take_profit }}</div>
                </div>
              </div>

              <!-- Enhanced Analysis Data -->
              <div v-if="parsedEnhancedData" class="bg-blue-50 rounded-lg p-4">
                <h4 class="font-medium text-blue-900 mb-3">Enhanced Analysis</h4>
                <div class="space-y-2 text-sm">
                  <div v-if="parsedEnhancedData.entry_concept" class="flex items-center">
                    <span class="font-medium text-blue-800 w-32">Entry Concept:</span>
                    <span class="capitalize">{{ parsedEnhancedData.entry_concept }}</span>
                  </div>
                  <div v-if="parsedEnhancedData.order_type" class="flex items-center">
                    <span class="font-medium text-blue-800 w-32">Order Type:</span>
                    <span class="font-mono bg-blue-100 px-2 py-1 rounded text-xs">{{ parsedEnhancedData.order_type }}</span>
                  </div>
                  <div v-if="parsedEnhancedData.take_profit_levels" class="flex items-start">
                    <span class="font-medium text-blue-800 w-32">Profit Targets:</span>
                    <div class="flex flex-wrap gap-1">
                      <span 
                        v-for="(level, idx) in parsedEnhancedData.take_profit_levels" 
                        :key="idx"
                        class="bg-green-100 text-green-800 px-2 py-1 rounded text-xs font-mono"
                      >
                        ${{ level }}
                      </span>
                    </div>
                  </div>
                  <div v-if="parsedEnhancedData.time_frame" class="flex items-center">
                    <span class="font-medium text-blue-800 w-32">Time Frame:</span>
                    <span class="capitalize">{{ parsedEnhancedData.time_frame }}</span>
                  </div>
                  <div v-if="parsedEnhancedData.confidence" class="flex items-center">
                    <span class="font-medium text-blue-800 w-32">Confidence:</span>
                    <div class="flex items-center space-x-2">
                      <span>{{ Math.round(parsedEnhancedData.confidence * 100) }}%</span>
                      <div class="w-24 bg-gray-200 rounded-full h-2">
                        <div 
                          class="bg-blue-600 h-2 rounded-full" 
                          :style="{ width: (parsedEnhancedData.confidence * 100) + '%' }"
                        ></div>
                      </div>
                    </div>
                  </div>
                  <div v-if="parsedEnhancedData.conditions" class="flex items-start">
                    <span class="font-medium text-blue-800 w-32">Conditions:</span>
                    <span class="text-gray-700">{{ parsedEnhancedData.conditions }}</span>
                  </div>
                </div>
              </div>

              <!-- Original Message -->
              <div v-if="selectedAnalysisSignal.original_message" class="bg-gray-50 rounded-lg p-4">
                <h4 class="font-medium text-gray-900 mb-2">Original Message</h4>
                <p class="text-sm text-gray-700 whitespace-pre-wrap">{{ selectedAnalysisSignal.original_message }}</p>
              </div>

              <!-- Analysis Notes -->
              <div v-if="selectedAnalysisSignal.analysis_notes" class="bg-yellow-50 rounded-lg p-4">
                <h4 class="font-medium text-yellow-900 mb-2">AI Analysis Notes</h4>
                <p class="text-sm text-yellow-800">{{ selectedAnalysisSignal.analysis_notes }}</p>
              </div>

              <!-- Raw JSON (Developer View) -->
              <details class="bg-gray-50 rounded-lg p-4">
                <summary class="font-medium text-gray-900 cursor-pointer">Raw Analysis Data (Developer)</summary>
                <pre class="mt-2 text-xs text-gray-600 overflow-x-auto bg-white p-3 rounded border">{{ JSON.stringify(rawAnalysisData, null, 2) }}</pre>
              </details>
            </div>
          </div>
          
          <div class="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
            <button
              @click="closeAnalysisModal"
              class="w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:ml-3 sm:w-auto sm:text-sm"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

interface Signal {
  id: number
  symbol: string
  action: 'BUY' | 'SELL'
  quantity?: number
  price?: number
  stop_loss?: number
  take_profit?: number
  status: 'pending' | 'approved' | 'executed'
  source: 'manual_entry' | 'message_paste' | 'whatsapp' | 'telegram' | 'discord'
  original_message?: string
  created_at: string
  remarks?: string
  analysis_notes?: string
  enhanced_data?: string | object // Can be JSON string or parsed object
}

defineProps<{
  signals: Signal[]
}>()

defineEmits<{
  execute: [id: number]
  approve: [signal: Signal]
  cancel: [id: number]
}>()

// Modal state
const showAnalysisDetailsModal = ref(false)
const selectedAnalysisSignal = ref<Signal | null>(null)

// Computed properties for modal data
const parsedEnhancedData = computed(() => {
  if (!selectedAnalysisSignal.value?.enhanced_data) return null
  
  try {
    if (typeof selectedAnalysisSignal.value.enhanced_data === 'string') {
      return JSON.parse(selectedAnalysisSignal.value.enhanced_data)
    }
    return selectedAnalysisSignal.value.enhanced_data
  } catch (error) {
    console.error('Error parsing enhanced_data:', error)
    return null
  }
})

const rawAnalysisData = computed(() => {
  if (!selectedAnalysisSignal.value) return null
  
  return {
    original_message: selectedAnalysisSignal.value.original_message,
    analysis_notes: selectedAnalysisSignal.value.analysis_notes,
    enhanced_data: parsedEnhancedData.value,
    remarks: selectedAnalysisSignal.value.remarks
  }
})

// Modal functions
const showAnalysisModal = (signal: Signal) => {
  selectedAnalysisSignal.value = signal
  showAnalysisDetailsModal.value = true
}

const closeAnalysisModal = () => {
  showAnalysisDetailsModal.value = false
  selectedAnalysisSignal.value = null
}
</script> 