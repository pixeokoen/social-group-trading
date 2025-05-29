<template>
  <div class="space-y-6">
    <!-- Trading Performance -->
    <div class="bg-white overflow-hidden shadow rounded-lg">
      <div class="px-4 py-5 sm:p-6">
        <h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">Trading Performance</h3>
        <dl class="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
          <div class="px-4 py-5 bg-gray-50 shadow rounded-lg overflow-hidden sm:p-6">
            <dt class="text-sm font-medium text-gray-500 truncate">Total Trades</dt>
            <dd class="mt-1 text-3xl font-semibold text-gray-900">{{ analytics.total_trades || 0 }}</dd>
          </div>

          <div class="px-4 py-5 bg-green-50 shadow rounded-lg overflow-hidden sm:p-6">
            <dt class="text-sm font-medium text-gray-500 truncate">Winning Trades</dt>
            <dd class="mt-1 text-3xl font-semibold text-green-600">{{ analytics.winning_trades || 0 }}</dd>
          </div>

          <div class="px-4 py-5 bg-red-50 shadow rounded-lg overflow-hidden sm:p-6">
            <dt class="text-sm font-medium text-gray-500 truncate">Losing Trades</dt>
            <dd class="mt-1 text-3xl font-semibold text-red-600">{{ analytics.losing_trades || 0 }}</dd>
          </div>

          <div class="px-4 py-5 bg-blue-50 shadow rounded-lg overflow-hidden sm:p-6">
            <dt class="text-sm font-medium text-gray-500 truncate">Win Rate</dt>
            <dd class="mt-1 text-3xl font-semibold text-blue-600">{{ winRate }}%</dd>
          </div>
        </dl>

        <div class="mt-6 grid grid-cols-1 gap-5 sm:grid-cols-2">
          <div class="bg-white overflow-hidden shadow rounded-lg">
            <div class="px-4 py-5 sm:p-6">
              <dt class="text-base font-normal text-gray-900">Total P&L</dt>
              <dd class="mt-1 flex justify-between items-baseline md:block lg:flex">
                <div
                  :class="[
                    'flex items-baseline text-2xl font-semibold',
                    totalPnL >= 0 ? 'text-green-600' : 'text-red-600'
                  ]"
                >
                  {{ totalPnL >= 0 ? '+' : '' }}${{ Math.abs(totalPnL).toFixed(2) }}
                </div>
              </dd>
            </div>
          </div>

          <div class="bg-white overflow-hidden shadow rounded-lg">
            <div class="px-4 py-5 sm:p-6">
              <dt class="text-base font-normal text-gray-900">Average P&L per Trade</dt>
              <dd class="mt-1 flex justify-between items-baseline md:block lg:flex">
                <div
                  :class="[
                    'flex items-baseline text-2xl font-semibold',
                    avgPnL >= 0 ? 'text-green-600' : 'text-red-600'
                  ]"
                >
                  {{ avgPnL >= 0 ? '+' : '' }}${{ Math.abs(avgPnL).toFixed(2) }}
                </div>
              </dd>
            </div>
          </div>
        </div>

        <div v-if="analytics.avg_trade_duration_hours" class="mt-6">
          <div class="bg-gray-50 overflow-hidden shadow rounded-lg">
            <div class="px-4 py-5 sm:p-6">
              <dt class="text-base font-normal text-gray-900">Average Trade Duration</dt>
              <dd class="mt-1 text-2xl font-semibold text-gray-900">
                {{ formatDuration(analytics.avg_trade_duration_hours) }}
              </dd>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Signal Statistics -->
    <div class="bg-white overflow-hidden shadow rounded-lg">
      <div class="px-4 py-5 sm:p-6">
        <h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">Signal Statistics</h3>
        <dl class="grid grid-cols-1 gap-5 sm:grid-cols-3">
          <div class="px-4 py-5 bg-gray-50 shadow rounded-lg overflow-hidden sm:p-6">
            <dt class="text-sm font-medium text-gray-500 truncate">Total Signals</dt>
            <dd class="mt-1 text-3xl font-semibold text-gray-900">{{ analytics.total_signals || 0 }}</dd>
          </div>

          <div class="px-4 py-5 bg-green-50 shadow rounded-lg overflow-hidden sm:p-6">
            <dt class="text-sm font-medium text-gray-500 truncate">Approved Signals</dt>
            <dd class="mt-1 text-3xl font-semibold text-green-600">{{ analytics.approved_signals || 0 }}</dd>
          </div>

          <div class="px-4 py-5 bg-red-50 shadow rounded-lg overflow-hidden sm:p-6">
            <dt class="text-sm font-medium text-gray-500 truncate">Rejected Signals</dt>
            <dd class="mt-1 text-3xl font-semibold text-red-600">{{ analytics.rejected_signals || 0 }}</dd>
          </div>
        </dl>

        <div v-if="signalApprovalRate > 0" class="mt-6">
          <div class="bg-blue-50 overflow-hidden shadow rounded-lg">
            <div class="px-4 py-5 sm:p-6">
              <dt class="text-base font-normal text-gray-900">Signal Approval Rate</dt>
              <dd class="mt-1 text-2xl font-semibold text-blue-600">
                {{ signalApprovalRate.toFixed(1) }}%
              </dd>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Analytics {
  total_trades: number
  winning_trades: number
  losing_trades: number
  total_pnl: number
  avg_pnl: number
  win_rate?: number
  avg_trade_duration_hours?: number
  total_signals?: number
  approved_signals?: number
  rejected_signals?: number
}

const props = defineProps<{
  analytics: Analytics
}>()

const winRate = computed(() => {
  if (!props.analytics.total_trades) return '0.0'
  return ((props.analytics.winning_trades / props.analytics.total_trades) * 100).toFixed(1)
})

const totalPnL = computed(() => props.analytics.total_pnl || 0)
const avgPnL = computed(() => props.analytics.avg_pnl || 0)

const signalApprovalRate = computed(() => {
  const total = props.analytics.total_signals || 0
  const approved = props.analytics.approved_signals || 0
  if (total === 0) return 0
  return (approved / total) * 100
})

const formatDuration = (hours: number): string => {
  if (hours < 1) {
    return `${Math.round(hours * 60)} minutes`
  } else if (hours < 24) {
    return `${hours.toFixed(1)} hours`
  } else {
    return `${(hours / 24).toFixed(1)} days`
  }
}
</script> 