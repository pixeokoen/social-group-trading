<template>
  <div class="py-6">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <!-- Header -->
      <div class="md:flex md:items-center md:justify-between mb-6">
        <div>
          <h1 class="text-2xl font-semibold text-gray-900">Database Compare</h1>
          <p class="mt-1 text-sm text-gray-600">
            Compare local database schema with remote databases and apply migrations.
          </p>
        </div>
        <button
          @click="showAddConnection = true"
          class="mt-3 md:mt-0 inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
        >
          <PlusIcon class="h-4 w-4 mr-2" />
          Add Connection
        </button>
      </div>

      <!-- Tabs -->
      <div class="bg-white shadow rounded-lg">
        <div class="border-b border-gray-200">
          <nav class="-mb-px flex">
            <button
              @click="activeTab = 'connections'"
              :class="[
                activeTab === 'connections'
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300',
                'py-4 px-6 border-b-2 font-medium text-sm transition-colors duration-200'
              ]"
            >
              Database Connections
            </button>
            <button
              @click="activeTab = 'comparisons'"
              :class="[
                activeTab === 'comparisons'
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300',
                'py-4 px-6 border-b-2 font-medium text-sm transition-colors duration-200'
              ]"
            >
              Schema Comparisons
            </button>
          </nav>
        </div>

        <div class="p-6">
          <!-- Database Connections Tab -->
          <div v-if="activeTab === 'connections'">
            <div v-if="connections.length === 0" class="text-center py-12">
              <CircleStackIcon class="mx-auto h-12 w-12 text-gray-400" />
              <h3 class="mt-2 text-sm font-medium text-gray-900">No database connections</h3>
              <p class="mt-1 text-sm text-gray-500">Get started by adding a database connection.</p>
            </div>

            <div v-else class="space-y-4">
              <div
                v-for="connection in connections"
                :key="connection.id"
                class="border rounded-lg p-4 hover:bg-gray-50"
              >
                <div class="flex items-start justify-between">
                  <div class="flex-1">
                    <div class="flex items-center space-x-3">
                      <h3 class="text-sm font-medium text-gray-900">{{ connection.name }}</h3>
                      <span
                        :class="[
                          'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
                          connection.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                        ]"
                      >
                        {{ connection.is_active ? 'Active' : 'Inactive' }}
                      </span>
                      <span
                        v-if="connection.test_result"
                        :class="[
                          'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
                          connection.test_result.includes('successful') ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                        ]"
                      >
                        {{ connection.test_result.includes('successful') ? 'Connected' : 'Failed' }}
                      </span>
                    </div>
                    <p class="mt-1 text-sm text-gray-500">
                      {{ connection.connection_type.toUpperCase() }} • {{ connection.host }}:{{ connection.port }}/{{ connection.database_name }}
                    </p>
                    <p v-if="connection.description" class="mt-1 text-sm text-gray-600">
                      {{ connection.description }}
                    </p>
                  </div>
                  <div class="flex items-center space-x-2 ml-4">
                    <button
                      @click="testConnection(connection.id)"
                      :disabled="testingConnection === connection.id"
                      class="inline-flex items-center px-3 py-1 border border-transparent text-sm font-medium rounded-md text-blue-700 bg-blue-100 hover:bg-blue-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <svg v-if="testingConnection !== connection.id" class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <svg v-else class="animate-spin w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      {{ testingConnection === connection.id ? 'Testing...' : 'Test' }}
                    </button>
                    <button
                      @click="compareSchema(connection)"
                      :disabled="comparingSchema === connection.id"
                      class="inline-flex items-center px-3 py-1 border border-transparent text-sm font-medium rounded-md text-green-700 bg-green-100 hover:bg-green-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <svg v-if="comparingSchema !== connection.id" class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7m0 10a2 2 0 002 2h2a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2h2a2 2 0 002-2z" />
                      </svg>
                      <svg v-else class="animate-spin w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 714 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      {{ comparingSchema === connection.id ? 'Comparing...' : 'Compare' }}
                    </button>
                    <button
                      @click="editConnection(connection)"
                      class="inline-flex items-center px-3 py-1 border border-transparent text-sm font-medium rounded-md text-gray-700 bg-gray-100 hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
                    >
                      <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                      </svg>
                      Edit
                    </button>
                    <button
                      @click="deleteConnection(connection.id)"
                      class="inline-flex items-center px-3 py-1 border border-transparent text-sm font-medium rounded-md text-red-700 bg-red-100 hover:bg-red-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                    >
                      <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                      Delete
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Schema Comparisons Tab -->
          <div v-if="activeTab === 'comparisons'">
            <div v-if="comparisons.length === 0" class="text-center py-12">
              <DocumentMagnifyingGlassIcon class="mx-auto h-12 w-12 text-gray-400" />
              <h3 class="mt-2 text-sm font-medium text-gray-900">No schema comparisons</h3>
              <p class="mt-1 text-sm text-gray-500">Run a comparison to see differences between databases.</p>
            </div>

            <div v-else class="space-y-4">
              <div
                v-for="comparison in comparisons"
                :key="comparison.id"
                class="border rounded-lg p-4"
              >
                <div class="flex items-start justify-between mb-4">
                  <div>
                    <h3 class="text-sm font-medium text-gray-900">{{ comparison.connection_name }}</h3>
                    <p class="text-xs text-gray-500">{{ new Date(comparison.created_at).toLocaleString() }}</p>
                  </div>
                  <div class="flex items-center space-x-2">
                    <span
                      :class="[
                        'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
                        comparison.status === 'applied' ? 'bg-green-100 text-green-800' :
                        comparison.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-gray-100 text-gray-800'
                      ]"
                    >
                      {{ comparison.status }}
                    </span>
                    <button
                      v-if="comparison.status === 'pending'"
                      @click="deleteComparison(comparison.id)"
                      class="inline-flex items-center p-1 border border-transparent text-sm rounded-full text-red-700 bg-red-100 hover:bg-red-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                      title="Delete comparison"
                    >
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  </div>
                </div>

                <!-- Differences Summary -->
                <div class="mb-4">
                  <h4 class="text-sm font-medium text-gray-700 mb-2">Differences Found</h4>
                  <div v-if="comparison.differences.length === 0" class="text-sm text-green-600">
                    ✅ No differences found - schemas are in sync
                  </div>
                  <div v-else class="space-y-2">
                    <div
                      v-for="(diff, index) in comparison.differences.slice(0, 3)"
                      :key="index"
                      :class="[
                        'text-sm p-2 rounded border-l-4',
                        diff.severity === 'high' ? 'border-red-400 bg-red-50 text-red-700' :
                        diff.severity === 'medium' ? 'border-yellow-400 bg-yellow-50 text-yellow-700' :
                        'border-blue-400 bg-blue-50 text-blue-700'
                      ]"
                    >
                      {{ diff.description }}
                    </div>
                    <div v-if="comparison.differences.length > 3" class="text-sm text-gray-500">
                      And {{ comparison.differences.length - 3 }} more differences...
                    </div>
                  </div>
                </div>

                <!-- Migration Suggestions -->
                <div v-if="comparison.suggested_migrations.length > 0">
                  <h4 class="text-sm font-medium text-gray-700 mb-2">
                    {{ comparison.status === 'applied' ? 'Applied Migrations' : 'Suggested Migrations' }}
                  </h4>
                  <div class="space-y-2 mb-4">
                    <div
                      v-for="(migration, index) in comparison.suggested_migrations.slice(0, 2)"
                      :key="index"
                      :class="[
                        'text-sm p-2 border rounded',
                        comparison.status === 'applied' ? 'bg-green-50 border-green-200' : 'bg-gray-50'
                      ]"
                    >
                      <div class="font-medium">{{ migration.action }}</div>
                      <div class="text-gray-600 text-xs mt-1">{{ migration.description }}</div>
                    </div>
                    <div v-if="comparison.suggested_migrations.length > 2" class="text-sm text-gray-500">
                      And {{ comparison.suggested_migrations.length - 2 }} more migrations...
                    </div>
                  </div>
                  
                  <!-- Show different buttons based on status -->
                  <button
                    v-if="comparison.status === 'pending'"
                    @click="showMigrationDetails(comparison)"
                    class="inline-flex items-center px-3 py-1 border border-primary-300 rounded text-sm text-primary-700 hover:bg-primary-50"
                  >
                    <EyeIcon class="h-4 w-4 mr-1" />
                    Review & Apply Migrations
                  </button>
                  
                  <button
                    v-if="comparison.status === 'applied'"
                    @click="viewAppliedMigrations(comparison)"
                    class="inline-flex items-center px-3 py-1 border border-green-300 rounded text-sm text-green-700 hover:bg-green-50"
                  >
                    <EyeIcon class="h-4 w-4 mr-1" />
                    View Applied Migrations
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Add Connection Modal -->
    <div v-if="showAddConnection" class="fixed z-10 inset-0 overflow-y-auto">
      <div class="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div class="fixed inset-0 transition-opacity" @click="showAddConnection = false">
          <div class="absolute inset-0 bg-gray-500 opacity-75"></div>
        </div>
        
        <div class="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
          <form @submit.prevent="createConnection">
            <div class="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
              <h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">Add Database Connection</h3>
              
              <div class="space-y-4">
                <div>
                  <label class="block text-sm font-medium text-gray-700">Connection Name</label>
                  <input
                    v-model="newConnection.name"
                    type="text"
                    required
                    class="mt-1 block w-full px-4 py-3 border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 text-base"
                    placeholder="Production Database"
                  />
                </div>
                
                <div>
                  <label class="block text-sm font-medium text-gray-700">Description</label>
                  <input
                    v-model="newConnection.description"
                    type="text"
                    class="mt-1 block w-full px-4 py-3 border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 text-base"
                    placeholder="Optional description"
                  />
                </div>
                
                <div class="grid grid-cols-2 gap-4">
                  <div>
                    <label class="block text-sm font-medium text-gray-700">Host</label>
                    <input
                      v-model="newConnection.host"
                      type="text"
                      required
                      class="mt-1 block w-full px-4 py-3 border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 text-base"
                      placeholder="localhost"
                    />
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-gray-700">Port</label>
                    <input
                      v-model="newConnection.port"
                      type="number"
                      required
                      class="mt-1 block w-full px-4 py-3 border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 text-base"
                      placeholder="5432"
                    />
                  </div>
                </div>
                
                <div>
                  <label class="block text-sm font-medium text-gray-700">Database Name</label>
                  <input
                    v-model="newConnection.database_name"
                    type="text"
                    required
                    class="mt-1 block w-full px-4 py-3 border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 text-base"
                    placeholder="social_trading"
                  />
                </div>
                
                <div>
                  <label class="block text-sm font-medium text-gray-700">Username</label>
                  <input
                    v-model="newConnection.username"
                    type="text"
                    required
                    class="mt-1 block w-full px-4 py-3 border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 text-base"
                    placeholder="postgres"
                  />
                </div>
                
                <div>
                  <label class="block text-sm font-medium text-gray-700">Password</label>
                  <input
                    v-model="newConnection.password"
                    type="password"
                    required
                    class="mt-1 block w-full px-4 py-3 border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 text-base"
                    placeholder="••••••••"
                  />
                </div>
              </div>
            </div>
            
            <div class="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
              <button
                type="submit"
                :disabled="loading"
                class="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-primary-600 text-base font-medium text-white hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:ml-3 sm:w-auto sm:text-sm disabled:opacity-50"
              >
                {{ loading ? 'Adding...' : 'Add Connection' }}
              </button>
              <button
                type="button"
                @click="showAddConnection = false"
                class="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- Edit Connection Modal -->
    <div v-if="showEditConnection" class="fixed z-10 inset-0 overflow-y-auto">
      <div class="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div class="fixed inset-0 transition-opacity" @click="showEditConnection = false">
          <div class="absolute inset-0 bg-gray-500 opacity-75"></div>
        </div>
        
        <div class="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
          <form @submit.prevent="updateConnection">
            <div class="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
              <h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">Edit Database Connection</h3>
              
              <div class="space-y-4" v-if="editingConnection">
                <div>
                  <label class="block text-sm font-medium text-gray-700">Connection Name</label>
                  <input
                    v-model="editingConnection.name"
                    type="text"
                    required
                    class="mt-1 block w-full px-4 py-3 border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 text-base"
                    placeholder="Production Database"
                  />
                </div>
                
                <div>
                  <label class="block text-sm font-medium text-gray-700">Description</label>
                  <input
                    v-model="editingConnection.description"
                    type="text"
                    class="mt-1 block w-full px-4 py-3 border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 text-base"
                    placeholder="Optional description"
                  />
                </div>
                
                <div class="grid grid-cols-2 gap-4">
                  <div>
                    <label class="block text-sm font-medium text-gray-700">Host</label>
                    <input
                      v-model="editingConnection.host"
                      type="text"
                      required
                      class="mt-1 block w-full px-4 py-3 border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 text-base"
                      placeholder="localhost"
                    />
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-gray-700">Port</label>
                    <input
                      v-model="editingConnection.port"
                      type="number"
                      required
                      class="mt-1 block w-full px-4 py-3 border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 text-base"
                      placeholder="5432"
                    />
                  </div>
                </div>
                
                <div>
                  <label class="block text-sm font-medium text-gray-700">Database Name</label>
                  <input
                    v-model="editingConnection.database_name"
                    type="text"
                    required
                    class="mt-1 block w-full px-4 py-3 border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 text-base"
                    placeholder="social_trading"
                  />
                </div>
                
                <div>
                  <label class="block text-sm font-medium text-gray-700">Username</label>
                  <input
                    v-model="editingConnection.username"
                    type="text"
                    required
                    class="mt-1 block w-full px-4 py-3 border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 text-base"
                    placeholder="postgres"
                  />
                </div>
                
                <div>
                  <label class="block text-sm font-medium text-gray-700">Password</label>
                  <input
                    v-model="editingConnection.password"
                    type="password"
                    class="mt-1 block w-full px-4 py-3 border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 text-base"
                    placeholder="Leave blank to keep existing password"
                  />
                </div>
              </div>
            </div>
            
            <div class="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
              <button
                type="submit"
                :disabled="loading"
                class="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-primary-600 text-base font-medium text-white hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:ml-3 sm:w-auto sm:text-sm disabled:opacity-50"
              >
                {{ loading ? 'Updating...' : 'Update Connection' }}
              </button>
              <button
                type="button"
                @click="showEditConnection = false"
                class="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- Error Modal -->
    <div v-if="showErrorModal" class="fixed z-20 inset-0 overflow-y-auto">
      <div class="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div class="fixed inset-0 transition-opacity" @click="showErrorModal = false">
          <div class="absolute inset-0 bg-gray-500 opacity-75"></div>
        </div>
        
        <div class="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-2xl sm:w-full">
          <div class="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
            <div class="flex">
              <div class="mx-auto flex-shrink-0 flex items-center justify-center h-12 w-12 rounded-full bg-red-100 sm:mx-0 sm:h-10 sm:w-10">
                <ExclamationTriangleIcon class="h-6 w-6 text-red-600" />
              </div>
              <div class="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left flex-1">
                <h3 class="text-lg leading-6 font-medium text-gray-900">
                  {{ errorModal.title }}
                </h3>
                <div class="mt-2">
                  <p class="text-sm text-gray-500 mb-3">{{ errorModal.message }}</p>
                  
                  <div v-if="errorModal.details && errorModal.details.length > 0" class="space-y-2">
                    <h4 class="text-sm font-medium text-gray-900">Details:</h4>
                    <div class="bg-red-50 border border-red-200 rounded-md p-3 max-h-60 overflow-y-auto">
                      <div v-for="(detail, index) in errorModal.details" :key="index" class="text-sm text-red-800 mb-2 last:mb-0">
                        <div class="font-medium">{{ detail.title }}</div>
                        <div class="font-mono text-xs mt-1 whitespace-pre-wrap">{{ detail.error }}</div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <div class="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
            <button
              @click="showErrorModal = false"
              class="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-red-600 text-base font-medium text-white hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 sm:ml-3 sm:w-auto sm:text-sm"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- View Applied Migrations Modal -->
    <div v-if="showViewModal" class="fixed z-10 inset-0 overflow-y-auto">
      <div class="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div class="fixed inset-0 transition-opacity" @click="showViewModal = false">
          <div class="absolute inset-0 bg-gray-500 opacity-75"></div>
        </div>
        
        <div class="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-4xl sm:w-full">
          <div class="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
            <h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">Applied Migrations</h3>
            
            <div v-if="viewingComparison" class="space-y-4">
              <div class="bg-green-50 border border-green-200 rounded-md p-4">
                <div class="flex">
                  <svg class="h-5 w-5 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
                  </svg>
                  <div class="ml-3">
                    <h3 class="text-sm font-medium text-green-800">
                      Migrations Successfully Applied
                    </h3>
                    <div class="mt-2 text-sm text-green-700">
                      <p>These migrations were applied on {{ new Date(viewingComparison.created_at).toLocaleString() }}</p>
                    </div>
                  </div>
                </div>
              </div>

              <div class="space-y-3">
                <div
                  v-for="(migration, index) in viewingComparison.suggested_migrations"
                  :key="index"
                  class="border border-green-200 rounded-lg p-4 bg-green-50"
                >
                  <div class="flex items-start">
                    <svg class="h-4 w-4 text-green-600 mt-1 mr-3" fill="currentColor" viewBox="0 0 20 20">
                      <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
                    </svg>
                    <div class="flex-1">
                      <div class="text-sm font-medium text-gray-900">
                        {{ migration.action }}
                      </div>
                      <p class="text-sm text-gray-600 mt-1">{{ migration.description }}</p>
                      <div class="mt-2">
                        <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                          Applied Successfully
                        </span>
                      </div>
                      <pre class="mt-2 text-xs bg-gray-100 p-2 rounded overflow-x-auto">{{ migration.sql }}</pre>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <div class="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
            <button
              @click="showViewModal = false"
              class="w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:ml-3 sm:w-auto sm:text-sm"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Migration Details Modal -->
    <div v-if="showMigrationModal" class="fixed z-10 inset-0 overflow-y-auto">
      <div class="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div class="fixed inset-0 transition-opacity" @click="showMigrationModal = false">
          <div class="absolute inset-0 bg-gray-500 opacity-75"></div>
        </div>
        
        <div class="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-4xl sm:w-full">
          <div class="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
            <h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">Migration Details</h3>
            
            <div v-if="selectedComparison" class="space-y-4">
              <div class="bg-yellow-50 border border-yellow-200 rounded-md p-4">
                <div class="flex">
                  <ExclamationTriangleIcon class="h-5 w-5 text-yellow-400" />
                  <div class="ml-3">
                    <h3 class="text-sm font-medium text-yellow-800">
                      Review migrations carefully
                    </h3>
                    <div class="mt-2 text-sm text-yellow-700">
                      <p>These migrations will modify the remote database structure. Always backup your database before applying migrations.</p>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Select All Button -->
              <div class="flex justify-between items-center">
                <button
                  @click="toggleSelectAll"
                  class="inline-flex items-center px-3 py-1 border border-gray-300 rounded text-sm text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                >
                  <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  {{ allSelected ? 'Deselect All' : 'Select All' }}
                </button>
                <span class="text-sm text-gray-500">
                  {{ selectedMigrations.length }} of {{ selectedComparison?.suggested_migrations?.length || 0 }} selected
                </span>
              </div>

              <div class="space-y-3">
                <div
                  v-for="(migration, index) in selectedComparison.suggested_migrations"
                  :key="index"
                  class="border rounded-lg p-4"
                >
                  <div class="flex items-start">
                    <input
                      :id="`migration-${index}`"
                      v-model="selectedMigrations"
                      :value="index"
                      type="checkbox"
                      class="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded mt-1"
                    />
                    <div class="ml-3 flex-1">
                      <label :for="`migration-${index}`" class="text-sm font-medium text-gray-900 cursor-pointer">
                        {{ migration.action }}
                      </label>
                      <p class="text-sm text-gray-600 mt-1">{{ migration.description }}</p>
                      <div class="mt-2">
                        <span
                          :class="[
                            'inline-flex items-center px-2 py-0.5 rounded text-xs font-medium',
                            migration.risk_level === 'high' ? 'bg-red-100 text-red-800' :
                            migration.risk_level === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                            'bg-green-100 text-green-800'
                          ]"
                        >
                          {{ migration.risk_level }} risk
                        </span>
                      </div>
                      <pre class="mt-2 text-xs bg-gray-100 p-2 rounded overflow-x-auto">{{ migration.sql }}</pre>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <div class="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
            <button
              @click="applyMigrations"
              :disabled="selectedMigrations.length === 0 || applyingMigrations"
              class="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-primary-600 text-base font-medium text-white hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:ml-3 sm:w-auto sm:text-sm disabled:opacity-50"
            >
              {{ applyingMigrations ? 'Applying...' : `Apply ${selectedMigrations.length} Migration(s)` }}
            </button>
            <button
              type="button"
              @click="showMigrationModal = false"
              class="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import axios from '@/plugins/axios'
import {
  CircleStackIcon, PlusIcon, DocumentMagnifyingGlassIcon,
  EyeIcon, ExclamationTriangleIcon
} from '@heroicons/vue/24/outline'

const activeTab = ref('connections')
const connections = ref<any[]>([])
const comparisons = ref<any[]>([])
const showAddConnection = ref(false)
const showEditConnection = ref(false)
const showMigrationModal = ref(false)
const loading = ref(false)
const editingConnection = ref<any>(null)
const testingConnection = ref<number | null>(null)
const comparingSchema = ref<number | null>(null)
const selectedComparison = ref<any>(null)
const selectedMigrations = ref<number[]>([])
const applyingMigrations = ref(false)
const showErrorModal = ref(false)
const errorModal = ref<{
  title: string
  message: string
  details: Array<{title: string, error: string}>
}>({
  title: '',
  message: '',
  details: []
})
const showViewModal = ref(false)
const viewingComparison = ref<any>(null)

const newConnection = ref({
  name: '',
  description: '',
  host: '',
  port: 5432,
  database_name: '',
  username: '',
  password: ''
})

const fetchConnections = async () => {
  try {
    const response = await axios.get('/api/database-connections')
    connections.value = response.data
  } catch (error: any) {
    console.error('Error fetching connections:', error)
  }
}

const fetchComparisons = async () => {
  try {
    const response = await axios.get('/api/schema-comparisons')
    comparisons.value = response.data
  } catch (error: any) {
    console.error('Error fetching comparisons:', error)
  }
}

const createConnection = async () => {
  loading.value = true
  try {
    await axios.post('/api/database-connections', newConnection.value)
    showAddConnection.value = false
    newConnection.value = {
      name: '',
      description: '',
      host: '',
      port: 5432,
      database_name: '',
      username: '',
      password: ''
    }
    await fetchConnections()
  } catch (error: any) {
    console.error('Error creating connection:', error)
    alert('Failed to create connection: ' + (error.response?.data?.detail || error.message))
  } finally {
    loading.value = false
  }
}

const testConnection = async (connectionId: number) => {
  testingConnection.value = connectionId
  try {
    const response = await axios.post(`/api/database-connections/${connectionId}/test`)
    const connection = connections.value.find((c: any) => c.id === connectionId)
    if (connection) {
      connection.test_result = response.data.message
    }
    
    if (response.data.success) {
      alert('Connection successful!')
    } else {
      alert('Connection failed: ' + response.data.message)
    }
  } catch (error: any) {
    console.error('Error testing connection:', error)
    alert('Failed to test connection: ' + (error.response?.data?.detail || error.message))
  } finally {
    testingConnection.value = null
  }
}

const compareSchema = async (connection: any) => {
  comparingSchema.value = connection.id
  try {
    await axios.post(`/api/database-connections/${connection.id}/compare`, {
      connection_id: connection.id,
      comparison_type: 'full'
    })
    await fetchComparisons()
    activeTab.value = 'comparisons'
    alert('Schema comparison completed!')
  } catch (error: any) {
    console.error('Error comparing schema:', error)
    alert('Failed to compare schema: ' + (error.response?.data?.detail || error.message))
  } finally {
    comparingSchema.value = null
  }
}

const showMigrationDetails = (comparison: any) => {
  selectedComparison.value = comparison
  selectedMigrations.value = []
  showMigrationModal.value = true
}

const viewAppliedMigrations = (comparison: any) => {
  viewingComparison.value = comparison
  showViewModal.value = true
}

const showError = (title: string, message: string, details: Array<{title: string, error: string}> = []) => {
  errorModal.value = {
    title,
    message,
    details
  }
  showErrorModal.value = true
}

const parseErrorDetails = (errors: string[]): Array<{title: string, error: string}> => {
  return errors.map((error, index) => {
    // Parse error messages like "Migration 0: syntax error at or near..."
    const match = error.match(/^Migration (\d+): (.+)$/)
    if (match) {
      return {
        title: `Migration ${match[1]}`,
        error: match[2]
      }
    }
    return {
      title: `Error ${index + 1}`,
      error: error
    }
  })
}

const applyMigrations = async () => {
  if (!selectedComparison.value || selectedMigrations.value.length === 0) return
  
  applyingMigrations.value = true
  try {
    const response = await axios.post(`/api/schema-comparisons/${selectedComparison.value.id}/apply`, {
      migration_indices: selectedMigrations.value,
      confirm_destructive: true
    })
    
    if (response.data.success) {
      alert('Migrations applied successfully!')
      showMigrationModal.value = false
      await fetchComparisons()
    } else {
      // Show detailed error modal instead of alert
      const errorDetails = parseErrorDetails(response.data.errors || [])
      showError(
        'Migration Errors',
        `${response.data.errors?.length || 0} migration(s) failed. Please review the errors below:`,
        errorDetails
      )
    }
  } catch (error: any) {
    console.error('Error applying migrations:', error)
    showError(
      'Application Error',
      'Failed to apply migrations due to a system error.',
      [{
        title: 'System Error',
        error: error.response?.data?.detail || error.message || 'Unknown error occurred'
      }]
    )
  } finally {
    applyingMigrations.value = false
  }
}

const editConnection = (connection: any) => {
  editingConnection.value = { ...connection }
  showEditConnection.value = true
}

const updateConnection = async () => {
  if (!editingConnection.value) return
  
  loading.value = true
  try {
    await axios.put(`/api/database-connections/${editingConnection.value.id}`, editingConnection.value)
    showEditConnection.value = false
    editingConnection.value = null
    await fetchConnections()
    alert('Connection updated successfully!')
  } catch (error: any) {
    console.error('Error updating connection:', error)
    alert('Failed to update connection: ' + (error.response?.data?.detail || error.message))
  } finally {
    loading.value = false
  }
}

const deleteConnection = async (connectionId: number) => {
  if (!confirm('Are you sure you want to delete this connection? This will also delete any associated schema comparisons.')) {
    return
  }
  
  try {
    await axios.delete(`/api/database-connections/${connectionId}`)
    await fetchConnections()
    await fetchComparisons()
    alert('Connection deleted successfully!')
  } catch (error: any) {
    console.error('Error deleting connection:', error)
    alert('Failed to delete connection: ' + (error.response?.data?.detail || error.message))
  }
}

const deleteComparison = async (comparisonId: number) => {
  if (!confirm('Are you sure you want to delete this comparison? This action cannot be undone.')) {
    return
  }
  
  try {
    await axios.delete(`/api/schema-comparisons/${comparisonId}`)
    await fetchComparisons()
    alert('Comparison deleted successfully!')
  } catch (error: any) {
    console.error('Error deleting comparison:', error)
    alert('Failed to delete comparison: ' + (error.response?.data?.detail || error.message))
  }
}

// Computed property to check if all migrations are selected
const allSelected = computed(() => {
  if (!selectedComparison.value?.suggested_migrations) return false
  const totalMigrations = selectedComparison.value.suggested_migrations.length
  return selectedMigrations.value.length === totalMigrations && totalMigrations > 0
})

const toggleSelectAll = () => {
  if (!selectedComparison.value?.suggested_migrations) return
  
  if (allSelected.value) {
    // Deselect all
    selectedMigrations.value = []
  } else {
    // Select all
    const allIndices = selectedComparison.value.suggested_migrations.map((_: any, index: number) => index)
    selectedMigrations.value = allIndices
  }
}

onMounted(() => {
  fetchConnections()
  fetchComparisons()
})
</script> 