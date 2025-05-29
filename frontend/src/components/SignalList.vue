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
                    signal.status === 'rejected' ? 'bg-red-100 text-red-800' :
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
            <!-- Pending signals - show approve/reject buttons -->
            <template v-if="signal.status === 'pending'">
              <button
                @click="$emit('approve', signal)"
                class="text-primary-600 hover:text-primary-900"
              >
                Approve
              </button>
              <button
                @click="$emit('reject', signal.id)"
                class="text-red-600 hover:text-red-900"
              >
                Reject
              </button>
            </template>
            
            <!-- Approved signals - show execute button -->
            <template v-else-if="signal.status === 'approved'">
              <button
                @click="$emit('execute', signal.id)"
                class="text-green-600 hover:text-green-900"
              >
                Execute
              </button>
            </template>
            
            <!-- Executed signals - show status -->
            <template v-else-if="signal.status === 'executed'">
              <span class="text-gray-500">Executed</span>
            </template>
            
            <!-- Rejected signals - show status -->
            <template v-else-if="signal.status === 'rejected'">
              <span class="text-red-500">Rejected</span>
            </template>
          </div>
        </div>
      </li>
    </ul>
    <div v-if="signals.length === 0" class="text-center py-12">
      <p class="text-gray-500">No signals available</p>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Signal {
  id: number
  symbol: string
  action: 'BUY' | 'SELL'
  quantity?: number
  price?: number
  stop_loss?: number
  take_profit?: number
  status: 'pending' | 'approved' | 'rejected' | 'executed'
  source: 'manual_entry' | 'message_paste' | 'whatsapp' | 'telegram' | 'discord'
  original_message?: string
  created_at: string
  remarks?: string
  analysis_notes?: string
}

defineProps<{
  signals: Signal[]
}>()

defineEmits<{
  execute: [id: number]
  approve: [signal: Signal]
  reject: [id: number]
}>()
</script> 