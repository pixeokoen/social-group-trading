<template>
  <div class="py-6">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="md:flex md:items-center md:justify-between mb-6">
        <h1 class="text-2xl font-semibold text-gray-900">Trading Signals</h1>
        <div class="mt-4 md:mt-0 flex space-x-3">
          <button
            @click="showMessageAnalyzer = true"
            class="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
          >
            <svg class="-ml-1 mr-2 h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            Analyze Message
          </button>
          <button
            @click="showCreateSignalModal"
            class="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
          >
            <svg class="-ml-1 mr-2 h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
            </svg>
            Create Signal
          </button>
        </div>
      </div>
      
      <!-- Filter tabs -->
      <div class="border-b border-gray-200 mb-6">
        <nav class="-mb-px flex space-x-8">
          <button
            v-for="status in ['all', 'pending', 'approved', 'executed', 'rejected']"
            :key="status"
            @click="filterStatus = status"
            :class="[
              filterStatus === status
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300',
              'whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm capitalize'
            ]"
          >
            {{ status }}
          </button>
        </nav>
      </div>
      
      <!-- Signals list -->
      <SignalList
        :signals="filteredSignals"
        @approve="approveSignal"
        @reject="rejectSignal"
        @execute="executeSignal"
        @cancel="cancelSignal"
      />
      
      <!-- Analyze Message Modal -->
      <div v-if="showMessageAnalyzer" class="fixed z-10 inset-0 overflow-y-auto">
        <div class="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
          <div class="fixed inset-0 transition-opacity" @click="closeAnalyzer">
            <div class="absolute inset-0 bg-gray-500 opacity-75"></div>
          </div>
          
          <div class="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-3xl sm:w-full">
            <div class="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
              <h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">Analyze Trading Message</h3>
              
              <div class="space-y-4">
                <div>
                  <label class="block text-sm font-medium text-gray-700">Paste your trading message</label>
                  <textarea
                    v-model="messageToAnalyze"
                    rows="6"
                    placeholder="Paste a WhatsApp or other message containing trading signals..."
                    class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                  />
                </div>
                
                <!-- Analysis Result -->
                <div v-if="analysisResult" class="mt-4 p-4 bg-gray-50 rounded-lg">
                  <h4 class="text-sm font-medium text-gray-900 mb-2">Analysis Result</h4>
                  
                  <div v-if="analysisResult.is_signal" class="space-y-2">
                    <p class="text-sm text-green-600">✓ Trading signals detected</p>
                    
                    <div v-for="(signal, index) in analysisResult.signals" :key="index" class="p-3 bg-white rounded border">
                      <p class="text-sm"><span class="font-medium">Symbol:</span> {{ signal.symbol }}</p>
                      <p class="text-sm"><span class="font-medium">Action:</span> {{ signal.action }}</p>
                      <p v-if="signal.entry_price" class="text-sm"><span class="font-medium">Entry:</span> ${{ signal.entry_price }}</p>
                      <p v-if="signal.stop_loss" class="text-sm"><span class="font-medium">Stop Loss:</span> ${{ signal.stop_loss }}</p>
                      <p v-if="signal.take_profit" class="text-sm"><span class="font-medium">Take Profit:</span> ${{ signal.take_profit }}</p>
                    </div>
                    
                    <div v-if="analysisResult.analysis_notes" class="mt-2">
                      <p class="text-sm font-medium text-gray-700">Notes:</p>
                      <p class="text-sm text-gray-600">{{ analysisResult.analysis_notes }}</p>
                    </div>
                  </div>
                  
                  <div v-else>
                    <p class="text-sm text-red-600">✗ No trading signals detected</p>
                    <p v-if="analysisResult.analysis_notes" class="text-sm text-gray-600 mt-2">{{ analysisResult.analysis_notes }}</p>
                  </div>
                </div>
              </div>
            </div>
            
            <div class="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
              <button
                @click="analyzeMessage"
                :disabled="analyzing || !messageToAnalyze.trim()"
                class="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-primary-600 text-base font-medium text-white hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:ml-3 sm:w-auto sm:text-sm disabled:opacity-50"
              >
                {{ analyzing ? 'Analyzing...' : 'Analyze' }}
              </button>
              <button
                type="button"
                @click="closeAnalyzer"
                class="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Order Confirmation Modal (used for both approve and create) -->
      <OrderConfirmModal
        :signal="selectedSignal"
        :is-open="showOrderModal"
        @close="closeOrderModal"
        @executed="onOrderExecuted"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import axios from '@/plugins/axios'
import { useAccountStore } from '@/stores/account'
import SignalList from '@/components/SignalList.vue'
import OrderConfirmModal from '@/components/OrderConfirmModal.vue'

interface Signal {
  id: number
  symbol: string
  action: string
  price?: number
  stop_loss?: number
  take_profit?: number
  quantity?: number
  status: string
  created_at: string
  source: string
  original_message?: string
  remarks?: string
  analysis_notes?: string
}

const accountStore = useAccountStore()

const signals = ref<Signal[]>([])
const filterStatus = ref('all')
const loading = ref(false)
const showMessageAnalyzer = ref(false)
const analyzing = ref(false)
const messageToAnalyze = ref('')
const analysisResult = ref<any>(null)
const selectedSignal = ref<Signal | null>(null)
const showOrderModal = ref(false)

const filteredSignals = computed(() => {
  if (filterStatus.value === 'all') {
    return signals.value
  }
  return signals.value.filter(signal => signal.status === filterStatus.value)
})

const fetchSignals = async () => {
  try {
    const response = await axios.get('/api/signals')
    signals.value = response.data
  } catch (error) {
    console.error('Error fetching signals:', error)
  }
}

const showCreateSignalModal = () => {
  selectedSignal.value = {
    id: 0,
    symbol: '',
    action: 'BUY',
    quantity: 100,
    status: 'manual_entry',
    created_at: new Date().toISOString(),
    source: 'manual_entry'
  }
  showOrderModal.value = true
}

const approveSignal = async (signal: Signal) => {
  selectedSignal.value = signal
  showOrderModal.value = true
}

const rejectSignal = async (signalId: number) => {
  try {
    await axios.post(`/api/signals/${signalId}/approve`, { approved: false })
    await fetchSignals()
  } catch (error) {
    console.error('Error rejecting signal:', error)
    alert('Failed to reject signal')
  }
}

const executeSignal = async (signalId: number) => {
  try {
    await axios.post(`/api/trades/execute/${signalId}`)
    await fetchSignals()
    alert('Trade executed successfully!')
  } catch (error: any) {
    console.error('Error executing signal:', error)
    alert(error.response?.data?.detail || 'Failed to execute trade')
  }
}

const cancelSignal = async (signalId: number) => {
  if (!confirm('Are you sure you want to cancel/delete this signal?')) return
  try {
    await axios.delete(`/api/signals/${signalId}`)
    await fetchSignals()
  } catch (error) {
    console.error('Error cancelling signal:', error)
    alert('Failed to cancel/delete signal')
  }
}

const analyzeMessage = async () => {
  if (!messageToAnalyze.value.trim()) return
  
  analyzing.value = true
  try {
    const response = await axios.post('/api/signals/analyze', {
      message: messageToAnalyze.value
    })
    analysisResult.value = response.data
  } catch (error: any) {
    console.error('Error analyzing message:', error)
    alert(error.response?.data?.detail || 'Failed to analyze message')
  } finally {
    analyzing.value = false
  }
}

const closeAnalyzer = () => {
  showMessageAnalyzer.value = false
  messageToAnalyze.value = ''
  analysisResult.value = null
}

const closeOrderModal = () => {
  selectedSignal.value = null
  showOrderModal.value = false
}

const onOrderExecuted = (result: any) => {
  alert(`Trade executed successfully! Order ID: ${result.broker_order_id}`)
  fetchSignals()
}

onMounted(() => {
  fetchSignals()
})
</script> 