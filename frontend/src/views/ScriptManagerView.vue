<template>
  <div class="script-manager-view">
    <div class="header">
      <h1>🎯 Script Manager</h1>
      <p class="description">
        Centralized monitoring and control for all automated processes
      </p>
    </div>

    <!-- Status Overview -->
    <div class="overview-cards" v-if="status">
      <div class="status-card">
        <div class="card-icon">📊</div>
        <div class="card-content">
          <h3>{{ status.total_processes }}</h3>
          <p>Total Processes</p>
        </div>
      </div>
      
      <div class="status-card running">
        <div class="card-icon">🟢</div>
        <div class="card-content">
          <h3>{{ status.running_processes }}</h3>
          <p>Running</p>
        </div>
      </div>
      
      <div class="status-card error" v-if="status.error_processes > 0">
        <div class="card-icon">🔴</div>
        <div class="card-content">
          <h3>{{ status.error_processes }}</h3>
          <p>Errors</p>
        </div>
      </div>
      
      <div class="status-card api">
        <div class="card-icon">🌐</div>
        <div class="card-content">
          <h3>{{ status.api_usage.total_calls_last_minute }}</h3>
          <p>API Calls/min</p>
        </div>
      </div>
    </div>

    <!-- API Usage Summary -->
    <div class="api-usage-section" v-if="status">
      <h2>API Usage Summary</h2>
      <div class="api-stats">
        <div class="api-stat">
          <span class="label">Current Rate:</span>
          <span class="value">{{ status.api_usage.total_calls_last_minute }} calls/minute</span>
        </div>
        <div class="api-stat">
          <span class="label">Projected Hourly:</span>
          <span class="value">~{{ status.api_usage.estimated_calls_per_hour }} calls/hour</span>
        </div>
        <div class="api-stat">
          <span class="label">Last Updated:</span>
          <span class="value">{{ formatDateTime(status.api_usage.timestamp) }}</span>
        </div>
      </div>
      
      <!-- API Usage by Process -->
      <div class="api-by-process">
        <h3>Usage by Process</h3>
        <div class="api-process-list">
          <div 
            v-for="(usage, processName) in status.api_usage.usage_by_process" 
            :key="processName"
            class="api-process-item"
          >
            <div class="process-name">{{ usage.process_name }}</div>
            <div class="usage-bar">
              <div 
                class="usage-fill" 
                :style="{ width: Math.min(usage.usage_percent, 100) + '%' }"
                :class="{ 'high-usage': usage.usage_percent > 80 }"
              ></div>
            </div>
            <div class="usage-stats">
              <span>{{ usage.calls_last_minute }}/{{ usage.limit_per_minute }}</span>
              <span class="percentage">({{ usage.usage_percent.toFixed(1) }}%)</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Process Status Table -->
    <div class="processes-section" v-if="status">
      <h2>Process Status</h2>
      <div class="processes-table">
        <div class="table-header">
          <div class="col-name">Process</div>
          <div class="col-status">Status</div>
          <div class="col-runs">Runs</div>
          <div class="col-success">Success Rate</div>
          <div class="col-duration">Avg Duration</div>
          <div class="col-api">API Calls</div>
          <div class="col-last">Last Run</div>
          <div class="col-next">Next Run</div>
        </div>
        
        <div 
          v-for="(process, processName) in status.processes" 
          :key="processName"
          class="table-row"
          :class="{ 
            'status-running': process.status === 'running',
            'status-error': process.status === 'error',
            'status-disabled': process.status === 'disabled'
          }"
        >
          <div class="col-name">
            <div class="process-info">
              <span class="status-indicator" :class="process.status"></span>
              <span class="process-name">{{ process.process_name }}</span>
            </div>
          </div>
          
          <div class="col-status">
            <span class="status-badge" :class="process.status">
              {{ process.status.charAt(0).toUpperCase() + process.status.slice(1) }}
            </span>
          </div>
          
          <div class="col-runs">
            <div class="runs-info">
              <span class="total">{{ process.metrics.total_runs }}</span>
              <div class="breakdown">
                <span class="success">✅ {{ process.metrics.success_count }}</span>
                <span class="error">❌ {{ process.metrics.error_count }}</span>
              </div>
            </div>
          </div>
          
          <div class="col-success">
            <div class="success-rate">
              <span class="percentage">
                {{ process.metrics.total_runs > 0 ? 
                   ((process.metrics.success_count / process.metrics.total_runs) * 100).toFixed(1) : '0.0' 
                }}%
              </span>
              <div 
                class="success-bar"
                :style="{ 
                  width: process.metrics.total_runs > 0 ? 
                    ((process.metrics.success_count / process.metrics.total_runs) * 100) + '%' : '0%' 
                }"
              ></div>
            </div>
          </div>
          
          <div class="col-duration">
            {{ process.metrics.avg_duration.toFixed(2) }}s
          </div>
          
          <div class="col-api">
            {{ process.metrics.api_calls_last_minute }}
          </div>
          
          <div class="col-last">
            <span v-if="process.metrics.last_run">
              {{ formatTime(process.metrics.last_run) }}
            </span>
            <span v-else class="no-data">Never</span>
          </div>
          
          <div class="col-next">
            <span v-if="process.next_run && process.status === 'running'">
              {{ formatTime(process.next_run) }}
            </span>
            <span v-else class="no-data">-</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Error Details -->
    <div class="errors-section" v-if="hasErrors">
      <h2>⚠️ Recent Errors</h2>
      <div class="error-list">
        <div 
          v-for="(process, processName) in errorProcesses" 
          :key="processName"
          class="error-item"
        >
          <div class="error-header">
            <span class="process-name">{{ process.process_name }}</span>
            <span class="error-time">{{ formatDateTime(process.metrics.last_error) }}</span>
          </div>
          <div class="error-message">{{ process.metrics.last_error_message }}</div>
        </div>
      </div>
    </div>

    <!-- System Resources -->
    <div class="resources-section" v-if="status && Object.keys(status.processes).length > 0">
      <h2>💻 System Resources</h2>
      <div class="resource-stats">
        <div class="resource-item">
          <span class="label">CPU Usage:</span>
          <span class="value">{{ getAverageResource('cpu_percent').toFixed(1) }}%</span>
        </div>
        <div class="resource-item">
          <span class="label">Memory Usage:</span>
          <span class="value">{{ getAverageResource('memory_mb').toFixed(1) }} MB</span>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <p>Loading script manager status...</p>
    </div>

    <!-- Error State -->
    <div v-if="error" class="error-state">
      <div class="error-icon">⚠️</div>
      <h3>Failed to Load Status</h3>
      <p>{{ error }}</p>
      <button @click="fetchStatus" class="retry-btn">Retry</button>
    </div>

    <!-- Refresh Controls -->
    <div class="controls" v-if="!loading && !error">
      <button @click="fetchStatus" class="refresh-btn" :disabled="refreshing">
        <span v-if="refreshing">⏳</span>
        <span v-else>🔄</span>
        Refresh
      </button>
      <span class="last-updated" v-if="lastUpdate">
        Last updated: {{ formatTime(lastUpdate) }}
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import axios from 'axios'

interface ProcessMetrics {
  last_run: string | null
  last_success: string | null
  last_error: string | null
  total_runs: number
  success_count: number
  error_count: number
  avg_duration: number
  api_calls_last_minute: number
  last_error_message: string | null
}

interface ProcessStatus {
  process_name: string
  status: string
  last_update: string
  next_run: string | null
  metrics: ProcessMetrics
  resource_usage: {
    cpu_percent: number
    memory_mb: number
    memory_percent: number
  }
}

interface ApiUsage {
  total_calls_last_minute: number
  estimated_calls_per_hour: number
  usage_by_process: Record<string, {
    calls_last_minute: number
    limit_per_minute: number
    usage_percent: number
    process_name: string
  }>
  timestamp: string
}

interface ScriptManagerStatus {
  processes: Record<string, ProcessStatus>
  api_usage: ApiUsage
  total_processes: number
  running_processes: number
  error_processes: number
}

const status = ref<ScriptManagerStatus | null>(null)
const loading = ref(true)
const refreshing = ref(false)
const error = ref<string | null>(null)
const lastUpdate = ref<Date | null>(null)
let autoRefreshInterval: any = null

const hasErrors = computed(() => {
  if (!status.value) return false
  return Object.values(status.value.processes).some(
    process => process.status === 'error' && process.metrics.last_error_message
  )
})

const errorProcesses = computed(() => {
  if (!status.value) return {}
  return Object.fromEntries(
    Object.entries(status.value.processes).filter(
      ([_, process]) => process.status === 'error' && process.metrics.last_error_message
    )
  )
})

const getAverageResource = (metric: string) => {
  if (!status.value) return 0
  const processes = Object.values(status.value.processes)
  const values = processes
    .map(p => p.resource_usage[metric as keyof typeof p.resource_usage])
    .filter(v => v != null)
  
  return values.length > 0 ? values.reduce((a, b) => a + b, 0) / values.length : 0
}

const formatTime = (dateString: string) => {
  const date = new Date(dateString)
  return new Intl.DateTimeFormat('en-US', {
    hour: 'numeric',
    minute: '2-digit',
    second: '2-digit'
  }).format(date)
}

const formatDateTime = (dateString: string) => {
  const date = new Date(dateString)
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit'
  }).format(date)
}

const fetchStatus = async () => {
  if (status.value) {
    refreshing.value = true
  } else {
    loading.value = true
  }
  
  error.value = null
  
  try {
    const response = await axios.get('/api/script-manager/status')
    status.value = response.data
    lastUpdate.value = new Date()
  } catch (err) {
    console.error('Error fetching script manager status:', err)
    error.value = 'Failed to fetch script manager status'
  } finally {
    loading.value = false
    refreshing.value = false
  }
}

onMounted(() => {
  fetchStatus()
  
  // Auto-refresh every 10 seconds
  autoRefreshInterval = setInterval(fetchStatus, 10000)
})

onUnmounted(() => {
  if (autoRefreshInterval) {
    clearInterval(autoRefreshInterval)
  }
})
</script>

<style scoped>
.script-manager-view {
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
}

.header {
  margin-bottom: 32px;
  text-align: center;
}

.header h1 {
  font-size: 2.5rem;
  color: #1f2937;
  margin-bottom: 8px;
}

.description {
  color: #6b7280;
  font-size: 1.1rem;
}

.overview-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 32px;
}

.status-card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
  gap: 16px;
  transition: transform 0.2s ease;
}

.status-card:hover {
  transform: translateY(-2px);
}

.status-card.running {
  border-left: 4px solid #10b981;
}

.status-card.error {
  border-left: 4px solid #ef4444;
}

.status-card.api {
  border-left: 4px solid #3b82f6;
}

.card-icon {
  font-size: 2rem;
}

.card-content h3 {
  font-size: 2rem;
  font-weight: bold;
  margin: 0;
  color: #1f2937;
}

.card-content p {
  margin: 4px 0 0 0;
  color: #6b7280;
  font-size: 0.9rem;
}

.api-usage-section, .processes-section, .errors-section, .resources-section {
  background: white;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.api-usage-section h2, .processes-section h2, .errors-section h2, .resources-section h2 {
  margin: 0 0 20px 0;
  color: #1f2937;
  font-size: 1.5rem;
}

.api-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.api-stat {
  display: flex;
  justify-content: space-between;
  padding: 12px 16px;
  background: #f9fafb;
  border-radius: 8px;
}

.api-stat .label {
  color: #6b7280;
  font-weight: 500;
}

.api-stat .value {
  color: #1f2937;
  font-weight: 600;
}

.api-by-process h3 {
  margin: 0 0 16px 0;
  color: #1f2937;
}

.api-process-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.api-process-item {
  display: grid;
  grid-template-columns: 1fr 200px 100px;
  gap: 16px;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #e5e7eb;
}

.api-process-item:last-child {
  border-bottom: none;
}

.process-name {
  font-weight: 500;
  color: #1f2937;
}

.usage-bar {
  height: 8px;
  background: #e5e7eb;
  border-radius: 4px;
  overflow: hidden;
}

.usage-fill {
  height: 100%;
  background: #3b82f6;
  transition: width 0.3s ease;
}

.usage-fill.high-usage {
  background: #ef4444;
}

.usage-stats {
  text-align: right;
  font-size: 0.9rem;
}

.percentage {
  color: #6b7280;
  margin-left: 8px;
}

.processes-table {
  overflow-x: auto;
}

.table-header, .table-row {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1fr 1fr 1fr 1.5fr 1.5fr;
  gap: 16px;
  padding: 12px 0;
  border-bottom: 1px solid #e5e7eb;
}

.table-header {
  font-weight: 600;
  color: #6b7280;
  font-size: 0.9rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.table-row {
  border-bottom: 1px solid #f3f4f6;
}

.table-row:last-child {
  border-bottom: none;
}

.table-row:hover {
  background: #f9fafb;
}

.process-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #6b7280;
}

.status-indicator.running {
  background: #10b981;
}

.status-indicator.error {
  background: #ef4444;
}

.status-indicator.disabled {
  background: #9ca3af;
}

.status-badge {
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 0.8rem;
  font-weight: 500;
  text-transform: uppercase;
}

.status-badge.running {
  background: #dcfce7;
  color: #166534;
}

.status-badge.error {
  background: #fee2e2;
  color: #dc2626;
}

.status-badge.disabled {
  background: #f3f4f6;
  color: #6b7280;
}

.runs-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.total {
  font-weight: 600;
  color: #1f2937;
}

.breakdown {
  display: flex;
  gap: 8px;
  font-size: 0.8rem;
}

.success-rate {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.success-bar {
  height: 4px;
  background: #10b981;
  border-radius: 2px;
}

.no-data {
  color: #9ca3af;
  font-style: italic;
}

.error-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.error-item {
  padding: 16px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
}

.error-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.error-header .process-name {
  font-weight: 600;
  color: #dc2626;
}

.error-time {
  color: #6b7280;
  font-size: 0.9rem;
}

.error-message {
  color: #991b1b;
  font-family: monospace;
  font-size: 0.9rem;
  background: white;
  padding: 8px;
  border-radius: 4px;
}

.resource-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.resource-item {
  display: flex;
  justify-content: space-between;
  padding: 12px 16px;
  background: #f9fafb;
  border-radius: 8px;
}

.controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 24px;
  padding: 16px;
  background: #f9fafb;
  border-radius: 8px;
}

.refresh-btn, .retry-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  transition: background-color 0.2s ease;
}

.refresh-btn:hover, .retry-btn:hover {
  background: #2563eb;
}

.refresh-btn:disabled {
  background: #9ca3af;
  cursor: not-allowed;
}

.last-updated {
  color: #6b7280;
  font-size: 0.9rem;
}

.loading, .error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px;
  text-align: center;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #e5e7eb;
  border-top: 3px solid #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-icon {
  font-size: 3rem;
  margin-bottom: 16px;
}

.error-state h3 {
  color: #dc2626;
  margin-bottom: 8px;
}

.error-state p {
  color: #6b7280;
  margin-bottom: 16px;
}
</style> 