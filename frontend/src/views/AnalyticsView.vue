<template>
  <div class="py-6">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <h1 class="text-2xl font-semibold text-gray-900">Trading Analytics</h1>
    </div>
    <div class="max-w-7xl mx-auto px-4 sm:px-6 md:px-8">
      <div class="mt-8">
        <Analytics :analytics="analytics" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from '@/plugins/axios'
import Analytics from '@/components/Analytics.vue'

const analytics = ref({
  total_trades: 0,
  winning_trades: 0,
  losing_trades: 0,
  total_pnl: 0,
  avg_pnl: 0
})

const fetchAnalytics = async () => {
  try {
    const response = await axios.get('/api/analytics')
    analytics.value = response.data
  } catch (error) {
    console.error('Error fetching analytics:', error)
  }
}

onMounted(() => {
  fetchAnalytics()
})
</script> 