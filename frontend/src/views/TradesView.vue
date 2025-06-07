<template>
  <div class="py-6">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <!-- Header -->
      <div class="mb-3">
        <h1 class="text-2xl font-semibold text-gray-900">Trades</h1>
      </div>
      
      <!-- Toolbar -->
      <div class="bg-gray-50 py-2 mb-4">
        <div class="flex flex-col lg:flex-row lg:items-center lg:justify-between space-y-3 lg:space-y-0">
          <!-- Left side: View Controls and Filter -->
          <div class="flex items-center space-x-4">
            <!-- View Switcher -->
            <div class="flex items-center bg-gray-100 rounded-lg p-1">
              <button
                @click="currentView = 'list'"
                :class="[
                  'px-3 py-1.5 text-sm font-medium rounded-md transition-colors duration-200',
                  currentView === 'list' 
                    ? 'bg-white text-gray-900 shadow-sm' 
                    : 'text-gray-600 hover:text-gray-900'
                ]"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 10h16M4 14h16M4 18h16"></path>
                </svg>
              </button>
              <button
                @click="currentView = 'grid'"
                :class="[
                  'px-3 py-1.5 text-sm font-medium rounded-md transition-colors duration-200',
                  currentView === 'grid' 
                    ? 'bg-white text-gray-900 shadow-sm' 
                    : 'text-gray-600 hover:text-gray-900'
                ]"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"></path>
                </svg>
              </button>
            </div>
            
            <!-- Multi-Select Status Filter - only show on list view -->
            <div v-if="currentView === 'list'" class="relative">
              <label class="sr-only">Filter by status</label>
              <div class="relative">
                <!-- Multi-select dropdown button -->
                <button
                  @click="showStatusDropdown = !showStatusDropdown"
                  @blur="handleDropdownBlur"
                  class="relative w-64 rounded-lg border border-gray-300 bg-white px-4 py-2 text-left text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200"
                >
                  <span v-if="selectedStatuses.length === 0" class="text-gray-500">Select statuses...</span>
                  <span v-else-if="selectedStatuses.length === statusOptions.length" class="text-gray-900">All Statuses</span>
                  <div v-else class="flex flex-wrap gap-1">
                    <span
                      v-for="status in selectedStatuses.slice(0, 2)"
                      :key="status"
                      class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                    >
                      {{ getStatusLabel(status) }}
                    </span>
                    <span v-if="selectedStatuses.length > 2" class="text-xs text-gray-500">
                      +{{ selectedStatuses.length - 2 }} more
                    </span>
                  </div>
                  <svg class="absolute right-3 top-3 h-4 w-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
                
                <!-- Dropdown menu -->
                <div
                  v-show="showStatusDropdown"
                  class="absolute z-10 mt-1 w-full rounded-lg bg-white border border-gray-300 shadow-lg"
                >
                  <div class="p-2">
                    <!-- Select All / Clear All -->
                    <div class="flex items-center justify-between mb-2 pb-2 border-b border-gray-200">
                      <button
                        @click="selectAllStatuses"
                        class="text-xs text-blue-600 hover:text-blue-800 font-medium"
                      >
                        Select All
                      </button>
                      <button
                        @click="clearAllStatuses"
                        class="text-xs text-gray-600 hover:text-gray-800 font-medium"
                      >
                        Clear All
                      </button>
                    </div>
                    
                    <!-- Status options -->
                    <div
                      v-for="option in statusOptions"
                      :key="option.value"
                      class="flex items-center py-1.5 px-2 hover:bg-gray-50 rounded cursor-pointer"
                      @click="toggleStatus(option.value)"
                    >
                      <input
                        type="checkbox"
                        :checked="selectedStatuses.includes(option.value)"
                        class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                        @click.stop
                        @change="toggleStatus(option.value)"
                      />
                      <label class="ml-2 text-sm text-gray-900 cursor-pointer">
                        {{ option.label }}
                      </label>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
            
          <!-- Right side: Action Buttons and Status -->
          <div class="flex flex-col sm:flex-row sm:items-center space-y-3 sm:space-y-0 sm:space-x-4">
            <!-- Action Buttons -->
            <div class="flex items-center space-x-3">
              <button
                @click="showCreateTradeModal"
                class="inline-flex items-center px-4 py-2 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 transition-colors duration-200"
              >
                <svg class="mr-2 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
                </svg>
                Create Trade
              </button>
              <button
                @click="syncTrades"
                :disabled="syncing"
                class="inline-flex items-center px-4 py-2 border border-gray-300 rounded-lg shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 transition-colors duration-200"
              >
                <svg 
                  :class="['mr-2 h-4 w-4', syncing ? 'animate-spin' : '']" 
                  fill="none" 
                  stroke="currentColor" 
                  viewBox="0 0 24 24"
                >
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
                </svg>
                {{ syncing ? 'Syncing...' : 'Sync with Broker' }}
              </button>
            </div>
            
            <!-- Status Info -->
            <div v-if="lastSync || streamConnected" class="flex items-center space-x-4">
              <span v-if="lastSync" class="text-sm text-gray-500">
                Last sync: {{ formatTime(lastSync) }}
              </span>
              <span v-if="streamConnected" class="text-sm text-green-600 flex items-center">
                <span class="inline-block w-2 h-2 bg-green-600 rounded-full mr-1 animate-pulse"></span>
                Real-time updates active
              </span>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Trade notifications -->
      <div v-if="notifications.length > 0" class="mt-4">
        <div class="bg-blue-50 border-l-4 border-blue-400 p-4 rounded-md">
          <div class="flex">
            <div class="flex-shrink-0">
              <svg class="h-5 w-5 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
              </svg>
            </div>
            <div class="ml-3 flex-1">
              <p class="text-sm text-blue-700">
                {{ notifications[0].data.message }}
              </p>
            </div>
            <button @click="dismissNotifications" class="ml-auto flex-shrink-0">
              <svg class="h-5 w-5 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
              </svg>
            </button>
          </div>
        </div>
      </div>

      <!-- Trade Linking Toolbar (appears when trades are selected) -->
      <div 
        v-if="selectedTrades.size > 0" 
        class="bg-blue-50 border border-blue-200 rounded-lg p-4 mt-4 transition-all duration-300"
      >
        <div class="flex items-center justify-between">
          <div class="flex items-center space-x-4">
            <span class="text-blue-800 font-medium">
              {{ selectedTrades.size }} trade{{ selectedTrades.size !== 1 ? 's' : '' }} selected
            </span>
            <button
              @click="selectAll"
              class="text-blue-600 hover:text-blue-800 text-sm font-medium"
            >
              Select All
            </button>
            <button
              @click="clearSelection"
              class="text-gray-600 hover:text-gray-800 text-sm font-medium"
            >
              Clear Selection
            </button>
          </div>
          
          <div class="flex items-center space-x-3">
            <button
              @click="linkSelectedTrades"
              :disabled="selectedTrades.size < 2 || linkingTrades"
              class="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
            >
              <svg v-if="linkingTrades" class="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <svg v-else class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"></path>
              </svg>
              <span>Link Trades</span>
            </button>
            
            <button
              @click="unlinkSelectedTrades"
              :disabled="linkingTrades"
              class="bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
            >
              <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"></path>
              </svg>
              <span>Unlink</span>
            </button>
          </div>
        </div>
      </div>

      <!-- Content Area -->
      <div class="mt-4">
        <!-- List View -->
        <div v-if="currentView === 'list'" class="flex flex-col relative">
          <!-- SVG Connector Overlay - positioned outside table to the left -->
          <svg 
            ref="connectorSvg"
            class="absolute pointer-events-none z-20"
            style="left: 0px; top: 0; overflow: visible;"
            :width="300"
            :height="tableHeight"
          >
            <g v-for="(connector, index) in connectors" :key="index">
              <path
                :d="connector.path"
                :stroke="connector.color"
                stroke-width="2"
                fill="none"
                class="opacity-80"
              />
              <!-- Hollow endpoint circles (on table border) -->
              <circle
                :cx="connector.startDot.x"
                :cy="connector.startDot.y"
                r="3.5"
                :stroke="connector.color"
                stroke-width="2"
                fill="white"
                class="opacity-90"
              />
              <circle
                v-if="!connector.endDot.hidden"
                :cx="connector.endDot.x"
                :cy="connector.endDot.y"
                r="3.5"
                :stroke="connector.color"
                stroke-width="2"
                fill="white"
                class="opacity-90"
              />
              <!-- Small junction dots (where branches meet trunk) -->
              <circle
                v-for="(junction, jIndex) in connector.junctionDots || []"
                :key="`junction-${index}-${jIndex}`"
                :cx="junction.x"
                :cy="junction.y"
                r="2"
                :fill="connector.color"
                stroke="none"
                class="opacity-95"
              />
              <!-- Small junction dots (where branches meet trunk) -->
              <circle
                v-for="(junction, jIndex) in connector.junctionDots || []"
                :key="`junction-${index}-${jIndex}`"
                :cx="junction.x"
                :cy="junction.y"
                r="2"
                :fill="connector.color"
                stroke="none"
                class="opacity-95"
              />
            </g>
          </svg>
          
          <div class="-my-2 overflow-x-auto sm:-mx-6 lg:-mx-8">
            <div class="py-2 align-middle inline-block min-w-full sm:px-6 lg:px-8">
              <div class="shadow overflow-hidden border-b border-gray-200 sm:rounded-lg relative">
                
                <table class="min-w-full divide-y divide-gray-200">
                  <thead class="bg-gray-50">
                    <tr>
                      <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        <input 
                          type="checkbox" 
                          class="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                          :checked="selectedTrades.size === trades.length && trades.length > 0"
                          :indeterminate="selectedTrades.size > 0 && selectedTrades.size < trades.length"
                          @change="selectedTrades.size === trades.length ? clearSelection() : selectAll()"
                        />
                      </th>
                      <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Symbol
                      </th>
                      <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Action
                      </th>
                      <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Quantity
                      </th>
                      <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Entry Price
                      </th>
                      <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Current/Exit
                      </th>
                      <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        P&L
                      </th>
                      <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Status
                      </th>
                      <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody class="bg-white divide-y divide-gray-200">
                    <tr 
                      v-for="trade in trades" 
                      :key="trade.id" 
                      :class="{ 'bg-yellow-50': trade.justUpdated }"
                      :ref="(el: any) => { if (el) tradeRefs[trade.id] = el as HTMLElement }"
                    >
                      <td class="px-6 py-4 whitespace-nowrap">
                        <div class="flex items-center">
                          <input 
                            type="checkbox" 
                            class="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                            :checked="selectedTrades.has(trade.id)"
                            @change="toggleTradeSelection(trade.id)"
                          />
                          <!-- Link group indicator -->
                          <div v-if="trade.link_group_id" class="ml-2">
                            <svg class="h-4 w-4 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"></path>
                            </svg>
                          </div>
                        </div>
                      </td>
                      <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {{ trade.symbol }}
                      </td>
                      <td class="px-6 py-4 whitespace-nowrap text-sm">
                        <span 
                          :class="[
                            trade.action === 'BUY' ? 'text-green-600' : 'text-red-600',
                            'font-medium'
                          ]"
                        >
                          {{ trade.action }}
                        </span>
                      </td>
                      <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        <span v-if="trade.link_group_id && getEffectiveQuantity(trade) !== trade.quantity" class="text-amber-600 font-medium">
                          {{ formatQuantity(getEffectiveQuantity(trade)) }} remaining 
                          <span class="text-slate-400 font-normal">({{ formatQuantity(trade.quantity) }} orig.)</span>
                        </span>
                        <span v-else>
                          {{ formatQuantity(trade.quantity) }}
                        </span>
                      </td>
                      <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        ${{ formatPrice(trade.entry_price || trade.broker_fill_price) }}
                      </td>
                      <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        <div v-if="(trade.status === 'filled' || trade.status === 'open') && trade.current_price">
                          ${{ formatPrice(trade.current_price) }}
                        </div>
                        <div v-else-if="trade.exit_price">
                          ${{ formatPrice(trade.exit_price) }}
                        </div>
                        <div v-else>
                          ${{ formatPrice(trade.current_price) }}
                        </div>
                      </td>
                      <td class="px-6 py-4 whitespace-nowrap text-sm">
                        <span 
                          v-if="(trade.status === 'filled' || trade.status === 'open') && trade.floating_pnl !== null && trade.floating_pnl !== undefined"
                          :class="trade.floating_pnl >= 0 ? 'text-green-600' : 'text-red-600'"
                        >
                          ${{ formatPrice(trade.floating_pnl) }}
                        </span>
                        <span 
                          v-else-if="trade.status === 'closed' && trade.pnl !== null && trade.pnl !== undefined"
                          :class="trade.pnl >= 0 ? 'text-green-600' : 'text-red-600'"
                        >
                          ${{ formatPrice(trade.pnl) }}
                        </span>
                        <span v-else class="text-gray-400">-</span>
                      </td>
                      <td class="px-6 py-4 whitespace-nowrap">
                        <span 
                          :class="[
                            'px-2 inline-flex text-xs leading-5 font-semibold rounded-full',
                            trade.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                            trade.status === 'filled' ? 'bg-blue-100 text-blue-800' :
                            trade.status === 'open' ? 'bg-green-100 text-green-800' :
                            trade.status === 'closed' ? 'bg-gray-100 text-gray-800' :
                            'bg-red-100 text-red-800'
                          ]"
                        >
                          {{ trade.status }}
                        </span>
                      </td>
                      <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        <button
                          v-if="(trade.status === 'filled' || trade.status === 'open') && trade.action === 'BUY'"
                          @click="openCloseTradeModal(trade)"
                          class="inline-flex items-center px-3 py-1 border border-transparent text-sm rounded-md text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                        >
                          <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M16 11V7a4 4 0 00-8 0v4M5 11h14l-1.68 9.39A2 2 0 0115.34 22H8.66a2 2 0 01-1.98-1.61L5 11z" />
                          </svg>
                          Sell
                        </button>
                      </td>
                    </tr>
                  </tbody>
                </table>
                <div v-if="trades.length === 0" class="text-center py-12">
                  <p class="text-gray-500">No trades yet</p>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Grid View - Open Positions Only -->
        <div v-else-if="currentView === 'grid'">
          <div v-if="openPositions.length === 0" class="bg-gray-50 rounded-xl p-8">
            <div class="text-center">
              <div class="mx-auto w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center">
                <svg class="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v4"></path>
                </svg>
              </div>
              <h3 class="mt-4 text-lg font-medium text-gray-900">No Open Positions</h3>
              <p class="mt-2 text-sm text-gray-500">
                You don't have any open positions to display.<br/>
                Open positions will appear here with live price tracking.
              </p>
            </div>
          </div>
          
          <!-- Position Cards Grid -->
          <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            <!-- DUMMY CARD FOR STYLING - DISABLED -->
            <div 
              v-if="false"
              key="dummy-card"
              class="bg-gradient-to-br from-white to-slate-50 rounded-2xl p-5 hover:scale-[1.02] transition-all duration-300 relative min-h-[400px] h-auto shadow-lg shadow-green-600/15 gradient-border-positive"
            >
              <!-- Subtle Decorative Background -->
              <div class="absolute inset-0 opacity-[0.02] overflow-hidden rounded-2xl">
                <div class="absolute top-0 right-0 w-20 h-20 bg-slate-300 rounded-full transform translate-x-6 -translate-y-6"></div>
                <div class="absolute bottom-0 left-0 w-16 h-16 bg-slate-400 rounded-full transform -translate-x-4 translate-y-4"></div>
              </div>

              <!-- Trade Type Indicator - Enhanced Trade -->
              <div class="absolute -top-3 -left-3 z-20">
                <div class="w-8 h-8 rounded-full flex items-center justify-center border-2 border-white shadow-lg transition-all duration-200 bg-gradient-to-br from-purple-500 to-violet-600 hover:from-purple-400 hover:to-violet-500" title="Enhanced Trade - Protected with Stop Loss/Take Profit">
                  <svg class="w-4 h-4 text-white drop-shadow-sm" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M5 16L3 8l4.5 2.5L12 7l4.5 3.5L21 8l-2 8H5z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="currentColor"/>
                  </svg>
                </div>
              </div>

              <!-- Actions Dropdown Menu - Top Right -->
              <div class="absolute -top-3 -right-3 z-20">
                <div class="relative">
                  <button
                    @click="toggleDropdown('dummy', $event)"
                    class="w-8 h-8 rounded-full flex items-center justify-center border-2 border-white shadow-lg bg-gradient-to-r from-slate-600 to-slate-700 hover:from-slate-700 hover:to-slate-800 transition-all duration-200 group"
                    title="Trade Actions"
                  >
                    <svg class="w-4 h-4 text-white group-hover:scale-110 transition-transform duration-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" />
                    </svg>
                  </button>
                  
                  <!-- Dropdown Menu -->
                  <div 
                    v-if="openDropdowns['dummy']"
                    @click.stop
                    class="absolute right-0 top-10 w-48 bg-white rounded-lg shadow-xl border border-slate-200 py-2 z-30"
                  >
                    <button
                      @click="openTradeDetailsModal(dummyPosition); closeAllDropdowns()"
                      class="w-full px-4 py-2 text-left text-sm text-slate-700 hover:bg-slate-50 flex items-center gap-2"
                    >
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                      </svg>
                      View Details
                    </button>
                    <button
                      @click="openSellAllModal(dummyPosition)"
                      class="w-full px-4 py-2 text-left text-sm text-rose-600 hover:bg-rose-50 flex items-center gap-2"
                    >
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6" />
                      </svg>
                      Sell All
                    </button>
                  </div>
                </div>
              </div>

              <!-- Dark Gradient Header -->
              <div class="bg-gradient-to-r from-slate-800 to-slate-700 text-white p-4 rounded-t-2xl mb-4 relative z-10 -m-5 mx-[-20px] mt-[-20px]">
                <div class="flex items-center justify-between">
                  <div>
                    <h3 class="text-xl font-bold text-white">TSLA</h3>
                    <p class="text-slate-300 text-sm">150 shares</p>
                  </div>
                  <div>
                    <span class="px-3 py-1.5 text-sm font-bold rounded-full border-2 border-white/20 bg-emerald-500/80 text-white hover:bg-emerald-500">
                      BUY
                    </span>
                  </div>
                </div>
              </div>
              
              <!-- P&L Summary - Realized and Floating -->
              <div class="mb-4 relative z-10 flex space-x-2">
                <div class="flex-1 px-3 py-2 rounded-lg border-l-3 bg-gradient-to-r from-green-50 to-emerald-50 border-l-green-600 text-center">
                  <div class="text-xs font-medium text-slate-600 mb-1">Realized P&L</div>
                  <div class="text-sm font-bold text-green-700">+$427.50</div>
                </div>
                <div class="flex-1 px-3 py-2 rounded-lg border-l-3 bg-gradient-to-r from-green-50 to-emerald-50 border-l-green-600 text-center">
                  <div class="text-xs font-medium text-slate-600 mb-1">Floating P&L</div>
                  <div class="text-sm font-bold text-green-700">+$874.65</div>
                </div>
              </div>
              
              <!-- Main Feature: Centered Thermometer with Dummy Data -->
              <div class="relative z-10 flex justify-center items-center bg-gradient-to-b from-slate-50 to-white rounded-xl p-6 shadow-inner flex-1 min-h-[240px]">
                <div class="w-full max-w-[200px]">
                  <TradingThermometer 
                    :position="dummyPosition"
                    :entry-price="245.50"
                    :current-price="253.83"
                    :stop-loss="230.00"
                    :take-profit-levels="dummyTakeProfitLevels"
                    :scale-settings="defaultScaleSettings"
                    class="h-80 w-full"
                  />
                </div>
              </div>
              

                          </div>
            
            <!-- REAL POSITION CARDS -->
            <div 
              v-for="position in openPositions" 
              :key="position.id"
              :class="[
                'bg-gradient-to-br from-white to-slate-50 rounded-2xl p-5 hover:scale-[1.02] transition-all duration-300 relative min-h-[400px] h-auto',
                getPositionCardStyle(position)
              ]"
            >
              <!-- Subtle Decorative Background -->
              <div class="absolute inset-0 opacity-[0.02] overflow-hidden rounded-2xl">
                <div class="absolute top-0 right-0 w-20 h-20 bg-slate-300 rounded-full transform translate-x-6 -translate-y-6"></div>
                <div class="absolute bottom-0 left-0 w-16 h-16 bg-slate-400 rounded-full transform -translate-x-4 translate-y-4"></div>
              </div>

              <!-- Trade Type Indicator - Corner Position -->
              <div class="absolute -top-3 -left-3 z-20">
                <div 
                  :class="[
                    'w-8 h-8 rounded-full flex items-center justify-center border-2 border-white shadow-lg transition-all duration-200',
                    hasEnhancedFeatures(position) 
                      ? 'bg-gradient-to-br from-purple-500 to-violet-600 hover:from-purple-400 hover:to-violet-500' 
                      : 'bg-gradient-to-br from-amber-500 to-orange-600 hover:from-amber-400 hover:to-orange-500'
                  ]"
                  :title="hasEnhancedFeatures(position) ? 'Enhanced Trade - Protected with Stop Loss/Take Profit' : 'Plain Trade - Basic Position'"
                >
                  <!-- Enhanced Trade: Crown Icon (Royal/Premium) -->
                  <svg v-if="hasEnhancedFeatures(position)" class="w-4 h-4 text-white drop-shadow-sm" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M5 16L3 8l4.5 2.5L12 7l4.5 3.5L21 8l-2 8H5z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="currentColor"/>
                  </svg>

                  <!-- Plain Trade: Simple Bar Chart Icon -->
                  <svg v-else class="w-4 h-4 text-white drop-shadow-sm" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 7a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zM14 4a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z" />
                  </svg>
                </div>
              </div>

              <!-- Actions Dropdown Menu - Top Right -->
              <div class="absolute -top-3 -right-3 z-20">
                <div class="relative">
                  <button
                    @click="toggleDropdown(position.id.toString(), $event)"
                    class="w-8 h-8 rounded-full flex items-center justify-center border-2 border-white shadow-lg bg-gradient-to-r from-slate-600 to-slate-700 hover:from-slate-700 hover:to-slate-800 transition-all duration-200 group"
                    title="Trade Actions"
                  >
                    <svg class="w-4 h-4 text-white group-hover:scale-110 transition-transform duration-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" />
                    </svg>
                  </button>
                  
                  <!-- Dropdown Menu -->
                  <div 
                    v-if="openDropdowns[position.id.toString()]"
                    @click.stop
                    class="absolute right-0 top-10 w-48 bg-white rounded-lg shadow-xl border border-slate-200 py-2 z-30"
                  >
                    <button
                      @click="openTradeDetailsModal(position); closeAllDropdowns()"
                      class="w-full px-4 py-2 text-left text-sm text-slate-700 hover:bg-slate-50 flex items-center gap-2"
                    >
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                      </svg>
                      View Details
                    </button>
                    <button
                      @click="openSellAllModal(position)"
                      class="w-full px-4 py-2 text-left text-sm text-rose-600 hover:bg-rose-50 flex items-center gap-2"
                    >
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6" />
                      </svg>
                      Sell All
                    </button>
                  </div>
                </div>
              </div>

              <!-- Dark Gradient Header -->
              <div class="bg-gradient-to-r from-slate-800 to-slate-700 text-white p-4 rounded-t-2xl mb-4 relative z-10 -m-5 mx-[-20px] mt-[-20px]">
                <div class="flex items-center justify-between">
                  <div>
                    <h3 class="text-xl font-bold text-white">{{ position.symbol }}</h3>
                    <p v-if="position.link_group_id && getEffectiveQuantity(position) !== position.quantity" class="text-slate-300 text-sm">
                      <span class="text-amber-200 font-medium">{{ formatQuantity(getEffectiveQuantity(position)) }} remaining</span>
                      <span class="text-slate-400"> ({{ formatQuantity(position.quantity) }} orig.)</span>
                    </p>
                    <p v-else class="text-slate-300 text-sm">{{ formatQuantity(position.quantity) }} shares</p>
                  </div>
                  <div>
                    <span 
                      :class="[
                        'px-3 py-1.5 text-sm font-bold rounded-full border-2 border-white/20',
                        position.action === 'BUY' 
                          ? 'bg-emerald-500/80 text-white hover:bg-emerald-500' 
                          : 'bg-rose-500/80 text-white hover:bg-rose-500'
                      ]"
                    >
                      {{ position.action }}
                    </span>
                  </div>
                </div>
              </div>
              
              <!-- P&L Summary - Realized and Floating -->
              <div class="mb-4 relative z-10 flex space-x-2">
                <div 
                  :class="[
                    'flex-1 px-3 py-2 rounded-lg border-l-3 text-center',
                    getRealizedPnl(position) >= 0 
                      ? 'bg-gradient-to-r from-green-50 to-emerald-50 border-l-green-600' 
                      : 'bg-gradient-to-r from-red-50 to-rose-50 border-l-red-600'
                  ]"
                >
                  <div class="text-xs font-medium text-slate-600 mb-1">Realized P&L</div>
                  <div 
                    :class="[
                      'text-sm font-bold',
                      getRealizedPnl(position) >= 0 ? 'text-green-700' : 'text-red-700'
                    ]"
                  >
                    {{ getRealizedPnl(position) >= 0 ? '+' : '-' }}${{ Math.abs(getRealizedPnl(position)).toFixed(2) }}
                  </div>
                </div>
                <div 
                  :class="[
                    'flex-1 px-3 py-2 rounded-lg border-l-3 text-center',
                    getFloatingPnl(position) >= 0 
                      ? 'bg-gradient-to-r from-green-50 to-emerald-50 border-l-green-600' 
                      : 'bg-gradient-to-r from-red-50 to-rose-50 border-l-red-600'
                  ]"
                >
                  <div class="text-xs font-medium text-slate-600 mb-1">Floating P&L</div>
                  <div 
                    :class="[
                      'text-sm font-bold',
                      getFloatingPnl(position) >= 0 ? 'text-green-700' : 'text-red-700'
                    ]"
                  >
                    {{ getFloatingPnl(position) >= 0 ? '+' : '-' }}${{ Math.abs(getFloatingPnl(position)).toFixed(2) }}
                  </div>
                </div>
              </div>
              
              <!-- Main Feature: Centered Thermometer -->
              <div class="relative z-10 flex justify-center items-center bg-gradient-to-b from-slate-50 to-white rounded-xl p-6 shadow-inner flex-1 min-h-[240px]">
                
                <!-- Scale Controls for Basic Positions (top-left of thermometer window) -->
                <div v-if="!position.take_profit_levels || position.take_profit_levels.length === 0" class="absolute top-2 left-2 z-30 bg-white/90 backdrop-blur-sm rounded-lg p-2 shadow-sm border">
                  <div class="space-y-2 text-xs">
                    <!-- Top Scale -->
                    <div class="flex items-center space-x-1">
                      <svg class="w-3 h-3 text-red-500" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M5.293 7.707a1 1 0 010-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 01-1.414 1.414L11 5.414V17a1 1 0 11-2 0V5.414L6.707 7.707a1 1 0 01-1.414 0z" clip-rule="evenodd" />
                      </svg>
                      <input 
                        :value="getTradeScaleSettings(position.id).topPercent"
                        @input="updateTradeScale(position.id, 'topPercent', Number(($event.target as HTMLInputElement).value))"
                        type="number" 
                        min="1" 
                        max="50" 
                        class="w-12 px-1 py-0.5 text-xs border rounded"
                        title="Top scale (%)"
                      />
                      <span class="text-slate-500">%</span>
                    </div>
                    <!-- Bottom Scale -->
                    <div class="flex items-center space-x-1">
                      <svg class="w-3 h-3 text-blue-500" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M14.707 12.293a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 111.414-1.414L9 14.586V3a1 1 0 012 0v11.586l2.293-2.293a1 1 0 011.414 0z" clip-rule="evenodd" />
                      </svg>
                      <input 
                        :value="getTradeScaleSettings(position.id).bottomPercent"
                        @input="updateTradeScale(position.id, 'bottomPercent', Number(($event.target as HTMLInputElement).value))"
                        type="number" 
                        min="1" 
                        max="50" 
                        class="w-12 px-1 py-0.5 text-xs border rounded"
                        title="Bottom scale (%)"
                      />
                      <span class="text-slate-500">%</span>
                    </div>
                  </div>
                </div>
                
                <div class="w-full max-w-[200px]">
                  <TradingThermometer 
                    :position="position"
                    :entry-price="Number(position.entry_price || position.broker_fill_price || 0)"
                    :current-price="getStableCurrentPrice(position)"
                    :stop-loss="position.stop_loss ? Number(position.stop_loss) : undefined"
                    :take-profit-levels="position.take_profit_levels || []"
                    :scale-settings="getTradeScaleSettings(position.id)"
                    class="h-80 w-full"
                  />
                </div>
              </div>
              

            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Order Confirmation Modal for closing trades -->
    <OrderConfirmModal
      :signal="selectedTrade"
      :is-open="showCloseModal"
      @close="closeModal"
      @executed="onTradeExecuted"
    />
    
    <!-- Order Confirmation Modal for creating trades -->
    <OrderConfirmModal
      :signal="selectedTradeToCreate"
      :is-open="showCreateModal"
      @close="closeCreateModal"
      @executed="onTradeCreated"
    />

    <!-- Trade Details Modal -->
    <TradeDetailsModal
      :trade="selectedTradeForDetails"
      :is-open="showTradeDetailsModal"
      @close="closeTradeDetailsModal"
    />

    <!-- Sell All Modal -->
    <SellAllModal
      :show="showSellAllModal"
      :position="selectedTradeForSellAll"
      @close="showSellAllModal = false; selectedTradeForSellAll = null"
      @confirm="executeSellAll"
    />
  </div>
</template>

<style scoped>
/* Gradient border effects for position cards */
/* 🎨 Top-to-bottom gradients: Header slate → P&L color */

.gradient-border-positive {
  position: relative;
  border: 2px solid transparent;
  background: linear-gradient(white, white) padding-box,
              linear-gradient(to bottom, #1e293b, #16a34a) border-box;
}

.gradient-border-negative {
  position: relative;
  border: 2px solid transparent;
  background: linear-gradient(white, white) padding-box,
              linear-gradient(to bottom, #1e293b, #dc2626) border-box;
}

/* Hover effects - slightly intensify the bottom color */
.gradient-border-positive:hover {
  background: linear-gradient(white, white) padding-box,
              linear-gradient(to bottom, #1e293b, #15803d) border-box;
}

.gradient-border-negative:hover {
  background: linear-gradient(white, white) padding-box,
              linear-gradient(to bottom, #1e293b, #b91c1c) border-box;
}
</style>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, computed, nextTick } from 'vue'
import axios from '@/plugins/axios'
import OrderConfirmModal from '@/components/OrderConfirmModal.vue'
import TradingThermometer from '@/components/TradingThermometer.vue'
import TradeDetailsModal from '@/components/TradeDetailsModal.vue'
import SellAllModal from '@/components/SellAllModal.vue'

interface Trade {
  id: number
  symbol: string
  action: 'BUY' | 'SELL'
  quantity: number
  entry_price?: number
  broker_fill_price?: number
  exit_price?: number
  current_price?: number
  floating_pnl?: number
  pnl?: number
  status: string
  stop_loss?: number
  stop_loss_status?: string
  stop_loss_executed_at?: string
  stop_loss_executed_price?: number
  take_profit_levels?: Array<{
    id: number
    level_number: number
    price: number
    percentage: number
    shares_quantity: number
    status: string
    executed_at?: string
    executed_price?: number
  }>
  justUpdated?: boolean
  link_group_id?: string
}

interface Notification {
  id: number
  data: {
    message: string
    trade_id: number
    status: string
    fill_price?: number
    quantity?: number
    type: string
  }
}

const trades = ref<Trade[]>([])
const allTrades = ref<Trade[]>([]) // Store all trades for filtering
const syncing = ref(false)
const lastSync = ref<Date | null>(null)
const notifications = ref<Notification[]>([])
const streamConnected = ref(false)
const showCloseModal = ref(false)
const selectedTrade = ref<any>(null)
const showCreateModal = ref(false)
const selectedTradeToCreate = ref<any>(null)
const statusFilter = ref<string>('all')
const currentView = ref<'list' | 'grid'>('list')
const selectedTrades = ref<Set<number>>(new Set())
const linkingTrades = ref(false)

// Scale settings for basic thermometer positions (per-trade persistence)
const tradeScaleSettings = ref<Record<number, { topPercent: number; bottomPercent: number }>>({})

// Default scale values
const defaultScaleSettings = {
  topPercent: 10,    // 10% above entry price
  bottomPercent: 5   // 5% below entry price
}

// Get scale settings for a specific trade
const getTradeScaleSettings = (tradeId: number) => {
  if (!tradeScaleSettings.value[tradeId]) {
    // Try to load from localStorage first
    const savedSettings = localStorage.getItem(`tradeScale_${tradeId}`)
    if (savedSettings) {
      try {
        tradeScaleSettings.value[tradeId] = JSON.parse(savedSettings)
      } catch (e) {
        tradeScaleSettings.value[tradeId] = { ...defaultScaleSettings }
      }
    } else {
      tradeScaleSettings.value[tradeId] = { ...defaultScaleSettings }
    }
  }
  return tradeScaleSettings.value[tradeId]
}

// Save scale settings for a specific trade
const saveTradeScaleSettings = (tradeId: number, settings: { topPercent: number; bottomPercent: number }) => {
  tradeScaleSettings.value[tradeId] = settings
  localStorage.setItem(`tradeScale_${tradeId}`, JSON.stringify(settings))
}

// Update scale setting for a specific trade
const updateTradeScale = (tradeId: number, field: 'topPercent' | 'bottomPercent', value: number) => {
  const currentSettings = getTradeScaleSettings(tradeId)
  const newSettings = { ...currentSettings, [field]: value }
  saveTradeScaleSettings(tradeId, newSettings)
}

// Dropdown menu states
const openDropdowns = ref<{[key: string]: boolean}>({})

const toggleDropdown = (positionId: string, event?: Event) => {
  if (event) {
    event.stopPropagation()
  }
  // Close all other dropdowns
  Object.keys(openDropdowns.value).forEach(key => {
    if (key !== positionId) {
      openDropdowns.value[key] = false
    }
  })
  // Toggle current dropdown
  openDropdowns.value[positionId] = !openDropdowns.value[positionId]
}

const closeAllDropdowns = () => {
  Object.keys(openDropdowns.value).forEach(key => {
    openDropdowns.value[key] = false
  })
}

// Trade details modal
const showTradeDetailsModal = ref(false)
const selectedTradeForDetails = ref<Trade | null>(null)

// Sell All modal
const showSellAllModal = ref(false)
const selectedTradeForSellAll = ref<Trade | null>(null)

// Multi-select status filter
const showStatusDropdown = ref(false)
const selectedStatuses = ref<string[]>(['pending', 'open', 'closed', 'cancelled'])
const statusOptions = [
  { value: 'pending', label: 'Pending' },
  { value: 'open', label: 'Open' },
  { value: 'closed', label: 'Closed' },
  { value: 'cancelled', label: 'Cancelled' }
]

// Trade connectors for linked trades
const tradeRefs = ref<Record<number, HTMLElement>>({})
const connectorSvg = ref<SVGElement | null>(null)
const tableHeight = ref(500)
const connectorUpdateTrigger = ref(0) // Reactive trigger for connector updates

let syncInterval: any = null
let notificationInterval: any = null
let priceUpdateInterval: any = null

// Initialize from localStorage
const initializeFromStorage = () => {
  // Load saved view
  const savedView = localStorage.getItem('tradesCurrentView')
  if (savedView && ['list', 'grid'].includes(savedView)) {
    currentView.value = savedView as 'list' | 'grid'
  }
  
  // Load saved status filter
  const savedStatuses = localStorage.getItem('tradesSelectedStatuses')
  if (savedStatuses) {
    try {
      const parsed = JSON.parse(savedStatuses)
      if (Array.isArray(parsed)) {
        selectedStatuses.value = parsed
      }
    } catch (e) {
      console.warn('Failed to parse saved status filter:', e)
    }
  }
}

// Watch for view changes and save to localStorage
watch(currentView, (newView) => {
  localStorage.setItem('tradesCurrentView', newView)
})

// Watch for status filter changes and save to localStorage
watch(selectedStatuses, (newStatuses) => {
  localStorage.setItem('tradesSelectedStatuses', JSON.stringify(newStatuses))
}, { deep: true })

// Watch for trades changes and update connector positions
watch([trades, selectedStatuses], async () => {
  // Wait for DOM to update after filter changes
  await nextTick()
  updateConnectorPositions()
}, { deep: true })

// Computed property for open positions (grid view)
const openPositions = computed(() => {
  // Calculate net positions fresh each time
  const linkGroupNetPositions: Record<string, number> = {}
  
  // Calculate net position for each link group (using ALL trades regardless of status)
  allTrades.value.forEach(trade => {
    if (trade.link_group_id) {
      const quantity = parseFloat(String(trade.quantity)) || 0
      
      if (!linkGroupNetPositions[trade.link_group_id]) {
        linkGroupNetPositions[trade.link_group_id] = 0
      }
      
      if (trade.action === 'BUY') {
        linkGroupNetPositions[trade.link_group_id] += quantity
      } else if (trade.action === 'SELL') {
        linkGroupNetPositions[trade.link_group_id] -= quantity
      }
    }
  })
  
  // Filter trades for display
  const filledOrOpenTrades = allTrades.value.filter(trade => {
    // Always include open/filled trades
    if (trade.status === 'open' || trade.status === 'filled') {
      return true
    }
    
    // For closed trades, only include BUY trades (original positions)
    // Exclude closed SELL trades as they are completed transactions
    if (trade.status === 'closed') {
      return trade.action === 'BUY'
    }
    
    return false
  })
  
  return filledOrOpenTrades.filter(trade => {
    // Show unlinked trades (standalone positions)
    if (!trade.link_group_id) {
      return true
    }
    
    // For linked trades, only show if there's still a net position
    // This handles cases where a BUY was partially sold but still has remaining shares
    const netPosition = linkGroupNetPositions[trade.link_group_id] || 0
    const hasRemainingPosition = Math.abs(netPosition) > 0
    
    // Additionally, for closed BUY trades in linked groups, 
    // only show them if they represent the original position (not the sell transactions)
    if (trade.status === 'closed' && trade.action === 'BUY') {
      return hasRemainingPosition
    }
    
    return hasRemainingPosition
  })
})

// Color palette for link groups
const linkColors = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#06B6D4', '#84CC16', '#F97316']

// Dummy data for styling purposes - DISABLED WITH v-if="false"
const dummyPosition: Trade = {
  id: 999999,
  symbol: 'TSLA',
  action: 'BUY' as 'BUY',
  quantity: 150,
  entry_price: 245.50,
  current_price: 253.83,
  floating_pnl: 1247.50,
  status: 'open',
  stop_loss: 230.00
}

const dummyTakeProfitLevels = [
  { id: 1, level_number: 1, price: 255.00, shares_quantity: 45, status: 'executed', percentage: 30 },
  { id: 2, level_number: 2, price: 265.00, shares_quantity: 45, status: 'pending', percentage: 30 },
  { id: 3, level_number: 3, price: 280.00, shares_quantity: 30, status: 'pending', percentage: 20 },
  { id: 4, level_number: 4, price: 300.00, shares_quantity: 30, status: 'pending', percentage: 20 }
]

// P&L calculation functions
const getRealizedPnl = (position: Trade) => {
  if (!position.take_profit_levels) return 0
  
  return position.take_profit_levels
    .filter(tp => tp.status === 'executed')
    .reduce((total, tp) => {
      const entryPrice = Number(position.entry_price || position.broker_fill_price || 0)
      const gainPerShare = tp.price - entryPrice
      return total + (gainPerShare * tp.shares_quantity)
    }, 0)
}

const getFloatingPnl = (position: Trade) => {
  // For linked trades, use effective quantity. For others, use regular calculation
  let remainingShares: number
  
  if (position.link_group_id) {
    // For linked trades, use the net effective quantity
    remainingShares = getEffectiveQuantity(position)
  } else {
    // For regular trades, subtract executed take profit shares
    const totalShares = position.quantity || 0
    const executedShares = position.take_profit_levels
      ?.filter(tp => tp.status === 'executed')
      .reduce((total, tp) => total + tp.shares_quantity, 0) || 0
    remainingShares = totalShares - executedShares
  }
  
  const entryPrice = Number(position.entry_price || position.broker_fill_price || 0)
  
  // Use stable price function to prevent jitter (same as price update logic)
  const currentPrice = getStableCurrentPrice(position)
  
  if (position.action === 'BUY') {
    return (currentPrice - entryPrice) * remainingShares
  } else {
    // For short positions
    return (entryPrice - currentPrice) * remainingShares
  }
}

// Computed property for trade connectors
const connectors = computed(() => {
  // Include the trigger to force recalculation when needed
  connectorUpdateTrigger.value
  
  const linkGroups = new Map<string, Trade[]>()
  const connectorList: Array<{
    path: string
    color: string
    startDot: { x: number, y: number }
    endDot: { x: number, y: number, hidden?: boolean }
    junctionDots?: Array<{ x: number, y: number }>
    groupIndex: number
  }> = []

  // Group trades by link_group_id
  trades.value.forEach(trade => {
    if (trade.link_group_id) {
      if (!linkGroups.has(trade.link_group_id)) {
        linkGroups.set(trade.link_group_id, [])
      }
      linkGroups.get(trade.link_group_id)!.push(trade)
    }
  })

  // Generate connectors for each link group
  Array.from(linkGroups.entries()).forEach(([groupId, groupTrades], groupIndex) => {
    if (groupTrades.length >= 2) {
      const color = linkColors[groupIndex % linkColors.length]
      
      // Sort trades by their position in the displayed list
      const sortedTrades = groupTrades.sort((a, b) => {
        const aIndex = trades.value.findIndex(t => t.id === a.id)
        const bIndex = trades.value.findIndex(t => t.id === b.id)
        return aIndex - bIndex
      })

      // Get positions for all trades in group
      const positions: Array<{ trade: Trade, tableBorderX: number, y: number }> = []
      
      sortedTrades.forEach(trade => {
        const ref = tradeRefs.value[trade.id]
        if (ref) {
          const rect = ref.getBoundingClientRect()
          const svgRect = connectorSvg.value?.getBoundingClientRect()
          const tableElement = ref.closest('table')
          
          if (svgRect && tableElement) {
            const tableRect = tableElement.getBoundingClientRect()
            positions.push({
              trade,
              tableBorderX: tableRect.left - svgRect.left,
              y: rect.top - svgRect.top + rect.height / 2
            })
          }
        }
      })

      if (positions.length >= 2) {
        // Circuit board connector positioning
        const baseTrunkDistance = 30
        const trunkOffsetIncrement = 20
        const trunkX = positions[0].tableBorderX - baseTrunkDistance - (groupIndex * trunkOffsetIncrement)
        
        const junctionDots: Array<{ x: number, y: number }> = []

        if (positions.length === 2) {
          // Direct connection for 2 trades
          const [first, last] = positions
          const path = `M ${first.tableBorderX},${first.y} L ${trunkX + 5},${first.y} Q ${trunkX},${first.y} ${trunkX},${first.y + 5} L ${trunkX},${last.y - 5} Q ${trunkX},${last.y} ${trunkX + 5},${last.y} L ${last.tableBorderX},${last.y}`
          
          connectorList.push({
            path,
            color,
            startDot: { x: first.tableBorderX, y: first.y },
            endDot: { x: last.tableBorderX, y: last.y },
            junctionDots,
            groupIndex
          })
        } else {
          // Circuit board branching for 3+ trades
          const firstPos = positions[0]
          const lastPos = positions[positions.length - 1]
          const middleTrades = positions.slice(1, -1)

          // Main trunk connector (first to last)
          const trunkPath = `M ${firstPos.tableBorderX},${firstPos.y} L ${trunkX + 5},${firstPos.y} Q ${trunkX},${firstPos.y} ${trunkX},${firstPos.y + 5} L ${trunkX},${lastPos.y - 5} Q ${trunkX},${lastPos.y} ${trunkX + 5},${lastPos.y} L ${lastPos.tableBorderX},${lastPos.y}`
          
          connectorList.push({
            path: trunkPath,
            color,
            startDot: { x: firstPos.tableBorderX, y: firstPos.y },
            endDot: { x: lastPos.tableBorderX, y: lastPos.y },
            junctionDots,
            groupIndex
          })

          // Branch lines for middle trades (sidelines to trunk)
          middleTrades.forEach(pos => {
            const branchPath = `M ${pos.tableBorderX},${pos.y} L ${trunkX + 5},${pos.y} Q ${trunkX},${pos.y} ${trunkX},${pos.y}`
            
            // Add junction dot where branch meets trunk
            junctionDots.push({ x: trunkX, y: pos.y })
            
            connectorList.push({
              path: branchPath,
              color,
              startDot: { x: pos.tableBorderX, y: pos.y },
              endDot: { x: trunkX, y: pos.y, hidden: true }, junctionDots: [],
              groupIndex
            })
          })
        }
      }
    }
  })

  return connectorList
})

// Get the effective remaining quantity for a trade (considering linked trades)
const getEffectiveQuantity = (trade: Trade) => {
  if (!trade.link_group_id) {
    // Unlinked trade - return original quantity
    return trade.quantity || 0
  }
  
  // For linked trades, calculate net position across all trades in the group
  let netPosition = 0
  allTrades.value.forEach(t => {
    if (t.link_group_id === trade.link_group_id) {
      const quantity = parseFloat(String(t.quantity)) || 0
      if (t.action === 'BUY') {
        netPosition += quantity
      } else if (t.action === 'SELL') {
        netPosition -= quantity
      }
    }
  })
  
  // Return the absolute net position (remaining shares to trade)
  return Math.abs(netPosition)
}

const formatQuantity = (quantity: number | string) => {
  // Convert to number if it's a string
  const numQuantity = typeof quantity === 'string' ? parseFloat(quantity) : quantity
  if (isNaN(numQuantity)) return '0'
  return numQuantity === Math.floor(numQuantity) ? numQuantity.toString() : numQuantity.toFixed(4)
}

const formatPrice = (price: any) => {
  if (price === null || price === undefined) return 'N/A'
  // Convert to number if it's a string
  const numPrice = typeof price === 'string' ? parseFloat(price) : price
  return isNaN(numPrice) ? 'N/A' : numPrice.toFixed(2)
}

// Helper functions for enhanced features
const hasTakeProfitLevels = (trade: Trade) => {
  return trade.take_profit_levels && trade.take_profit_levels.length > 0
}

const hasStopLoss = (trade: Trade) => {
  return trade.stop_loss && trade.stop_loss > 0
}

const hasEnhancedFeatures = (trade: Trade) => {
  return hasTakeProfitLevels(trade) || hasStopLoss(trade)
}

// Trade details modal functions
const openTradeDetailsModal = (trade: Trade) => {
  selectedTradeForDetails.value = trade
  showTradeDetailsModal.value = true
}

const closeTradeDetailsModal = () => {
  showTradeDetailsModal.value = false
  selectedTradeForDetails.value = null
}

// Position card visual styling based on floating P&L
// 🎨 Gradient borders from header (slate) to P&L color (green/red)
const getPositionCardStyle = (position: Trade) => {
  const floatingPnl = getFloatingPnl(position)
  
  if (floatingPnl > 0) {
    // Positive P&L: Gradient from slate (header) to green (positive)
    return 'shadow-lg shadow-green-600/15 gradient-border-positive hover:shadow-xl hover:shadow-green-600/25'
  } else if (floatingPnl < 0) {
    // Negative P&L: Gradient from slate (header) to red (negative)
    return 'shadow-lg shadow-red-600/15 gradient-border-negative hover:shadow-xl hover:shadow-red-600/25'
  } else {
    // Neutral P&L: Uniform slate border (no gradient needed)
    return 'shadow-lg shadow-slate-500/10 border-2 border-slate-300 hover:shadow-xl hover:shadow-slate-500/20 hover:border-slate-400'
  }
}

// Sell All functionality
const openSellAllModal = (position: Trade) => {
  // Enhance the position object with effective quantity for linked trades
  const enhancedPosition = {
    ...position,
    effective_quantity: getEffectiveQuantity(position)
  }
  selectedTradeForSellAll.value = enhancedPosition
  showSellAllModal.value = true
  closeAllDropdowns()
}

const executeSellAll = async (data: any) => {
  try {
    console.log('🎯 Executing Sell All for trade:', data.tradeId)
    
    const response = await axios.post(`/api/trades/${data.tradeId}/sell-all`)
    const result = response.data
    console.log('✅ Sell All executed:', result)
    
    // Show success notification
    notifications.value.push({
      id: Date.now(),
      data: {
        type: 'success',
        message: `Sell All executed: ${result.shares_sold} shares at $${result.sell_price.toFixed(2)}. P&L: ${result.realized_pnl >= 0 ? '+' : ''}$${result.realized_pnl.toFixed(2)}`,
        trade_id: data.tradeId,
        status: 'executed',
        fill_price: result.sell_price,
        quantity: result.shares_sold
      }
    })
    
    // Close modal
    showSellAllModal.value = false
    selectedTradeForSellAll.value = null
    
    // Refresh trades to show the changes
    await fetchTrades()
    
  } catch (error: any) {
    console.error('❌ Error executing sell all:', error)
    
    const errorMessage = error.response?.data?.detail || error.message || 'Failed to execute sell all order'
    
    notifications.value.push({
      id: Date.now(),
      data: {
        type: 'error',
        message: `Sell All failed: ${errorMessage}`,
        trade_id: data.tradeId,
        status: 'error'
      }
    })
  }
}

const formatTime = (date: Date) => {
  return new Intl.DateTimeFormat('en-US', {
    hour: 'numeric',
    minute: '2-digit',
    second: '2-digit'
  }).format(date)
}

// Trade selection functions
const toggleTradeSelection = (tradeId: number) => {
  if (selectedTrades.value.has(tradeId)) {
    selectedTrades.value.delete(tradeId)
  } else {
    selectedTrades.value.add(tradeId)
  }
}

const clearSelection = () => {
  selectedTrades.value.clear()
}

const selectAll = () => {
  trades.value.forEach(trade => {
    selectedTrades.value.add(trade.id)
  })
}

// Trade linking functions
const linkSelectedTrades = async () => {
  if (selectedTrades.value.size < 2) {
    alert('Please select at least 2 trades to link')
    return
  }
  
  try {
    linkingTrades.value = true
    const tradeIds = Array.from(selectedTrades.value)
    
    const response = await axios.post('/api/trades/link', tradeIds)
    
    // Refresh trades to show the linking
    await fetchTrades()
    clearSelection()
    
    alert(`Successfully linked ${tradeIds.length} trades`)
  } catch (error) {
    console.error('Error linking trades:', error)
    alert('Error linking trades')
  } finally {
    linkingTrades.value = false
  }
}

const unlinkSelectedTrades = async () => {
  if (selectedTrades.value.size === 0) {
    alert('Please select trades to unlink')
    return
  }
  
  try {
    linkingTrades.value = true
    const tradeIds = Array.from(selectedTrades.value)
    
    await axios.post('/api/trades/unlink', tradeIds)
    
    // Refresh trades to show the unlinking
    await fetchTrades()
    clearSelection()
    
    alert(`Successfully unlinked ${tradeIds.length} trades`)
  } catch (error) {
    console.error('Error unlinking trades:', error)
    alert('Error unlinking trades')
  } finally {
    linkingTrades.value = false
  }
}

const fetchTrades = async () => {
  try {
    const response = await axios.get('/api/trades')
    allTrades.value = response.data
    applyStatusFilter()
    
    // Update table height for connectors after DOM updates
    await nextTick()
    updateTableHeight()
  } catch (error) {
    console.error('Error fetching trades:', error)
  }
}

const applyStatusFilter = () => {
  if (selectedStatuses.value.length === 0) {
    trades.value = []
  } else {
    trades.value = allTrades.value.filter(trade => selectedStatuses.value.includes(trade.status))
  }
}

const onStatusFilterChange = () => {
  applyStatusFilter()
  // Save filter to localStorage
  localStorage.setItem('tradesStatusFilter', statusFilter.value)
}

// Multi-select status filter functions
const getStatusLabel = (status: string) => {
  const option = statusOptions.find(opt => opt.value === status)
  return option ? option.label : status
}

const toggleStatus = (status: string) => {
  const index = selectedStatuses.value.indexOf(status)
  if (index > -1) {
    selectedStatuses.value.splice(index, 1)
  } else {
    selectedStatuses.value.push(status)
  }
  applyStatusFilter()
}

const selectAllStatuses = () => {
  selectedStatuses.value = statusOptions.map(opt => opt.value)
  applyStatusFilter()
}

const clearAllStatuses = () => {
  selectedStatuses.value = []
  applyStatusFilter()
}

const handleDropdownBlur = (event: FocusEvent) => {
  // Close dropdown if focus moves outside
  setTimeout(() => {
    const dropdown = (event.target as HTMLElement)?.closest('.relative')
    if (!dropdown?.contains(document.activeElement)) {
      showStatusDropdown.value = false
    }
  }, 150)
}

// Update table height for SVG connectors
const updateTableHeight = () => {
  if (connectorSvg.value?.parentElement) {
    const tableElement = connectorSvg.value.parentElement.querySelector('table')
    if (tableElement) {
      tableHeight.value = tableElement.offsetHeight
    }
  }
}

// Force update of connector positions
const updateConnectorPositions = () => {
  // Update table height first
  updateTableHeight()
  
  // Trigger connector recalculation by incrementing the reactive trigger
  connectorUpdateTrigger.value++
}

const syncTrades = async () => {
  syncing.value = true
  try {
    const response = await axios.get('/api/trades/sync')
    lastSync.value = new Date()
    
    // Refresh trades after sync
    await fetchTrades()
    
    // Only log when there are actual updates
    if (response.data.trades_updated > 0) {
      console.log(`Synced ${response.data.trades_updated} trades with broker`)
    }
  } catch (error) {
    console.error('Error syncing trades:', error)
    // Only show alert for actual errors, not for successful syncs
    // alert('Failed to sync trades with broker')
  } finally {
    syncing.value = false  // Make sure to stop the spinner
  }
}

const checkNotifications = async () => {
  try {
    const response = await axios.get('/api/notifications/trades?unread_only=true')
    const newNotifications = response.data
    
    if (newNotifications.length > 0) {
      notifications.value = newNotifications
      streamConnected.value = true
      
      // Process each notification
      for (const notification of newNotifications) {
        const notifData = notification.data
        
        // Update trade in the list
        const tradeIndex = trades.value.findIndex(t => t.id === notifData.trade_id)
        if (tradeIndex !== -1) {
          // Update trade status and highlight it
          trades.value[tradeIndex] = {
            ...trades.value[tradeIndex],
            status: notifData.status,
            entry_price: notifData.fill_price || trades.value[tradeIndex].entry_price,
            quantity: notifData.quantity || trades.value[tradeIndex].quantity,
            justUpdated: true
          }
          
          // Remove highlight after 3 seconds
          setTimeout(() => {
            if (trades.value[tradeIndex]) {
              trades.value[tradeIndex].justUpdated = false
            }
          }, 3000)
        }
        
        // Mark notification as read
        try {
          await axios.post(`/api/notifications/trades/${notification.id}/read`)
        } catch (error) {
          console.error('Error marking notification as read:', error)
        }
      }
      
      // Refresh trades to get latest data
      if (newNotifications.some((n: Notification) => ['order_filled', 'order_partial_fill'].includes(n.data.type))) {
        await fetchTrades()
      }
      
      // Auto-dismiss notifications after 5 seconds
      setTimeout(() => {
        dismissNotifications()
      }, 5000)
    }
  } catch (error) {
    console.error('Error checking notifications:', error)
    streamConnected.value = false
  }
}

const dismissNotifications = () => {
  notifications.value = []
}

// Track real market prices separately from fallback prices
const realMarketPrices = ref<{[symbol: string]: number}>({})

// Get stable current price to prevent jitter
const getStableCurrentPrice = (position: any) => {
  const symbol = position.symbol
  const entryPrice = Number(position.entry_price || position.broker_fill_price || 0)
  const currentPrice = Number(position.current_price || 0)
  
  // If we have a real market price that's different from entry, use it
  if (realMarketPrices.value[symbol] && realMarketPrices.value[symbol] !== entryPrice) {
    return realMarketPrices.value[symbol]
  }
  
  // If current_price looks like real market data (significantly different from entry), use it
  if (currentPrice > 0 && Math.abs(currentPrice - entryPrice) > 0.01) {
    realMarketPrices.value[symbol] = currentPrice
    return currentPrice
  }
  
  // Otherwise use entry_price as fallback
  return entryPrice
}

// Update current market prices for open positions
const updateCurrentPrices = async () => {
  try {
    // Get symbols from open positions - reduced logging to minimize DevTools noise
    const symbols = openPositions.value.map(pos => pos.symbol).filter(Boolean)
    
    if (symbols.length === 0) {
      return
    }
    
    const uniqueSymbols = [...new Set(symbols)]
    
    const response = await axios.post('/api/trades/current-prices', {
      symbols: uniqueSymbols // Remove duplicates
    })
    
    const priceData = response.data
    
    // Update current prices in trades (only with real market data)
    trades.value.forEach(trade => {
      if (priceData[trade.symbol]) {
        const newPrice = priceData[trade.symbol]
        const entryPrice = Number(trade.entry_price || trade.broker_fill_price || 0)
        
        // Only update if it's significantly different from entry price (real market data)
        if (Math.abs(newPrice - entryPrice) > 0.01) {
          trade.current_price = newPrice
          realMarketPrices.value[trade.symbol] = newPrice
        }
      }
    })
    
    // Update current prices in allTrades (only with real market data)
    allTrades.value.forEach(trade => {
      if (priceData[trade.symbol]) {
        const newPrice = priceData[trade.symbol]
        const entryPrice = Number(trade.entry_price || trade.broker_fill_price || 0)
        
        // Only update if it's significantly different from entry price
        if (Math.abs(newPrice - entryPrice) > 0.01) {
          trade.current_price = newPrice
          realMarketPrices.value[trade.symbol] = newPrice
        }
      }
    })
  } catch (error) {
    console.error('Error updating current prices:', error)
  }
}

const openCloseTradeModal = (trade: Trade) => {
  // Create a signal-like object for the modal
  // When closing a trade, we need to SELL if we bought, or BUY if we sold (short)
  const closeAction = trade.action === 'BUY' ? 'SELL' : 'BUY'
  
  selectedTrade.value = {
    id: 0, // 0 indicates this is a new order
    symbol: trade.symbol,
    action: closeAction,
    quantity: trade.quantity, // Default to closing the full position
    source: 'close_position',
    original_trade_id: trade.id // Store reference to the trade being closed
  }
  
  showCloseModal.value = true
}

const closeModal = () => {
  showCloseModal.value = false
  selectedTrade.value = null
}

const onTradeExecuted = async (result: any) => {
  alert(`Trade closed successfully! Order ID: ${result.broker_order_id}`)
  await fetchTrades()
}

const showCreateTradeModal = () => {
  // Create a new trade object for the modal
  selectedTradeToCreate.value = {
    id: 0, // 0 indicates this is a new order
    symbol: '',
    action: 'BUY',
    quantity: 100, // Default quantity
    source: 'manual_create'
  }
  
  showCreateModal.value = true
}

const closeCreateModal = () => {
  showCreateModal.value = false
  selectedTradeToCreate.value = null
}

const onTradeCreated = async (result: any) => {
  alert(`Trade created successfully! Order ID: ${result.broker_order_id}`)
  await fetchTrades()
  closeCreateModal()
}

onMounted(() => {
  // Initialize from localStorage (view and status filter)
  initializeFromStorage()
  
  // If no saved statuses, default to all statuses selected
  if (selectedStatuses.value.length === 0) {
    selectedStatuses.value = statusOptions.map(opt => opt.value)
  }
  
  fetchTrades()
  
  // Check for notifications every 3 seconds
  notificationInterval = setInterval(() => {
    checkNotifications()
  }, 3000)
  
  // Update current market prices every 2 seconds
  priceUpdateInterval = setInterval(() => {
    updateCurrentPrices()
  }, 2000)
  
  // Fallback sync every 30 seconds
  syncInterval = setInterval(() => {
    syncTrades()
  }, 30000)
  
  // Initial sync
  syncTrades()
  
  // Check notifications immediately
  checkNotifications()
  
  // Update current prices immediately
  updateCurrentPrices()
  
  // Listen for account switches
  window.addEventListener('account-switched', fetchTrades)
  
  // Close dropdowns when clicking outside
  document.addEventListener('click', closeAllDropdowns)
})

onUnmounted(() => {
  if (syncInterval) {
    clearInterval(syncInterval)
  }
  if (notificationInterval) {
    clearInterval(notificationInterval)
  }
  if (priceUpdateInterval) {
    clearInterval(priceUpdateInterval)
  }
  
  // Clean up event listeners
  window.removeEventListener('account-switched', fetchTrades)
  document.removeEventListener('click', closeAllDropdowns)
})
</script> 
