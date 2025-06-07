<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Navigation -->
    <nav class="bg-white shadow-sm">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between h-16">
          <div class="flex">
            <div class="flex-shrink-0 flex items-center">
              <!-- Logo -->
              <div class="h-8 w-8 bg-gradient-to-r from-primary-500 to-primary-600 rounded-full flex items-center justify-center mr-3 shadow-sm">
                <svg class="h-4 w-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"/>
                </svg>
              </div>
              <h1 class="text-xl font-bold text-primary-600">Social Trading</h1>
            </div>
            <div class="hidden sm:ml-6 sm:flex sm:items-center sm:space-x-8">
              <!-- Dashboard with icon -->
              <router-link
                to="/"
                class="border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 inline-flex items-center px-1 pt-1 pb-1 border-b-2 text-sm font-medium"
                active-class="border-primary-500 text-gray-900"
              >
                <HomeIcon class="h-5 w-5" />
              </router-link>
              
              <!-- Signals -->
              <router-link
                to="/signals"
                class="border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 inline-flex items-center px-1 pt-1 pb-1 border-b-2 text-sm font-medium space-x-1"
                active-class="border-primary-500 text-gray-900"
              >
                <ChartBarIcon class="h-5 w-5" />
                <span>Signals</span>
              </router-link>
              
              <!-- Trades -->
              <router-link
                to="/trades"
                class="border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 inline-flex items-center px-1 pt-1 pb-1 border-b-2 text-sm font-medium space-x-1"
                active-class="border-primary-500 text-gray-900"
              >
                <CurrencyDollarIcon class="h-5 w-5" />
                <span>Trades</span>
              </router-link>
              
              <!-- Positions -->
              <router-link
                to="/positions"
                class="border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 inline-flex items-center px-1 pt-1 pb-1 border-b-2 text-sm font-medium space-x-1"
                active-class="border-primary-500 text-gray-900"
              >
                <BanknotesIcon class="h-5 w-5" />
                <span>Positions</span>
              </router-link>
              
              <!-- More Dropdown -->
              <div class="relative dropdown-container">
                <button
                  @click="showMoreDropdown = !showMoreDropdown"
                  class="border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 inline-flex items-center px-1 pt-1 pb-1 border-b-2 text-sm font-medium focus:outline-none space-x-1"
                  :class="isMoreRouteActive ? 'border-primary-500 text-gray-900' : ''"
                >
                  <EllipsisHorizontalIcon class="h-5 w-5" />
                  <span>More</span>
                  <ChevronDownIcon class="h-4 w-4" />
                </button>
                
                <!-- More Dropdown Menu -->
                <div
                  v-if="showMoreDropdown"
                  @click.stop
                  class="origin-top-right absolute right-0 mt-2 w-56 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 focus:outline-none z-10"
                >
                  <div class="py-1">
                    <!-- Levels Monitoring -->
                    <router-link
                      to="/monitoring"
                      @click="showMoreDropdown = false"
                      class="group flex items-center px-4 py-2 text-sm hover:bg-gray-100 border-l-4 border-transparent"
                      :class="$route.path === '/monitoring' ? 'text-gray-900 bg-gray-50 border-l-primary-500' : 'text-gray-700'"
                    >
                      <ChartBarIcon class="h-5 w-5 mr-3" :class="$route.path === '/monitoring' ? 'text-primary-500' : 'text-gray-400 group-hover:text-gray-500'" />
                      Levels Monitoring
                    </router-link>
                    
                    <!-- Scripts Manager -->
                    <router-link
                      to="/script-manager"
                      @click="showMoreDropdown = false"
                      class="group flex items-center px-4 py-2 text-sm hover:bg-gray-100 border-l-4 border-transparent"
                      :class="$route.path === '/script-manager' ? 'text-gray-900 bg-gray-50 border-l-primary-500' : 'text-gray-700'"
                    >
                      <CommandLineIcon class="h-5 w-5 mr-3" :class="$route.path === '/script-manager' ? 'text-primary-500' : 'text-gray-400 group-hover:text-gray-500'" />
                      Scripts Manager
                    </router-link>
                    
                    <!-- Database Compare -->
                    <router-link
                      to="/database-compare"
                      @click="showMoreDropdown = false"
                      class="group flex items-center px-4 py-2 text-sm hover:bg-gray-100 border-l-4 border-transparent"
                      :class="$route.path === '/database-compare' ? 'text-gray-900 bg-gray-50 border-l-primary-500' : 'text-gray-700'"
                    >
                      <CircleStackIcon class="h-5 w-5 mr-3" :class="$route.path === '/database-compare' ? 'text-primary-500' : 'text-gray-400 group-hover:text-gray-500'" />
                      Database Compare
                    </router-link>
                    
                    <!-- Settings -->
                    <router-link
                      to="/settings"
                      @click="showMoreDropdown = false"
                      class="group flex items-center px-4 py-2 text-sm hover:bg-gray-100 border-l-4 border-transparent"
                      :class="$route.path === '/settings' ? 'text-gray-900 bg-gray-50 border-l-primary-500' : 'text-gray-700'"
                    >
                      <CogIcon class="h-5 w-5 mr-3" :class="$route.path === '/settings' ? 'text-primary-500' : 'text-gray-400 group-hover:text-gray-500'" />
                      Settings
                    </router-link>
                    
                    <!-- Separator -->
                    <div class="border-t border-gray-100 my-1"></div>
                    
                    <!-- Logout -->
                    <button
                      v-if="isAuthenticated"
                      @click="logout"
                      class="group flex items-center w-full px-4 py-2 text-sm text-red-600 hover:bg-red-50 hover:text-red-700 border-l-4 border-transparent"
                    >
                      <ArrowRightOnRectangleIcon class="h-5 w-5 mr-3 text-red-500 group-hover:text-red-600" />
                      Logout
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div class="flex items-center space-x-4">
            <!-- Mobile menu button (visible on small screens) -->
            <div class="sm:hidden">
              <button
                @click="showMobileMenu = !showMobileMenu"
                class="inline-flex items-center justify-center p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-primary-500"
              >
                <Bars3Icon v-if="!showMobileMenu" class="h-6 w-6" />
                <XMarkIcon v-else class="h-6 w-6" />
              </button>
            </div>
            <!-- Account Switcher -->
            <div v-if="isAuthenticated" class="relative dropdown-container">
              <button
                @click="showAccountDropdown = !showAccountDropdown"
                class="flex items-center text-sm rounded-full focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
              >
                <div class="px-3 py-1 bg-gray-100 rounded-md flex items-center space-x-2 hover:bg-gray-200">
                  <span
                    :class="[
                      'inline-block w-2 h-2 rounded-full',
                      accountStore.activeAccountType === 'live' ? 'bg-green-500' : 'bg-yellow-500'
                    ]"
                  ></span>
                  <span class="text-sm font-medium text-gray-700">{{ accountStore.activeAccountName }}</span>
                  <ChevronDownIcon class="ml-1 h-5 w-5 text-gray-400" />
                </div>
              </button>
              
              <!-- Account Dropdown -->
              <div
                v-if="showAccountDropdown"
                @click.stop
                class="origin-top-right absolute right-0 mt-2 w-56 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 focus:outline-none z-10"
              >
                <div class="py-1">
                  <div class="px-4 py-2 text-xs text-gray-500 font-medium uppercase tracking-wide">
                    Switch Account
                  </div>
                  <div
                    v-for="account in accountStore.accounts"
                    :key="account.id"
                    @click="switchAccount(account.id)"
                    class="px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 cursor-pointer flex items-center justify-between"
                    :class="account.id === accountStore.activeAccountId ? 'bg-gray-50' : ''"
                  >
                    <div class="flex items-center space-x-2">
                      <span
                        :class="[
                          'inline-block w-2 h-2 rounded-full',
                          account.account_type === 'live' ? 'bg-green-500' : 'bg-yellow-500'
                        ]"
                      ></span>
                      <span>{{ account.name }}</span>
                    </div>
                    <CheckIcon
                      v-if="account.id === accountStore.activeAccountId"
                      class="h-4 w-4 text-primary-600"
                    />
                  </div>
                  <div class="border-t border-gray-100 mt-1 pt-1">
                    <router-link
                      to="/settings"
                      @click="showAccountDropdown = false"
                      class="group flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                    >
                      <CogIcon class="h-4 w-4 mr-2 text-gray-400 group-hover:text-gray-500" />
                      Manage Accounts
                    </router-link>
                  </div>
                </div>
              </div>
            </div>

            <button
              v-if="!isAuthenticated"
              @click="$router.push('/login')"
              class="bg-primary-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-primary-700 flex items-center space-x-1"
            >
              <ArrowRightOnRectangleIcon class="h-4 w-4" />
              <span>Login</span>
            </button>
          </div>
        </div>
      </div>
      
      <!-- Mobile menu overlay (visible on small screens when open) -->
      <div
        v-if="showMobileMenu"
        class="sm:hidden fixed inset-x-0 top-16 bg-white shadow-lg border-t border-gray-200 z-30"
      >
        <div class="px-4 py-3 space-y-1">
          <!-- Dashboard -->
          <router-link
            to="/"
            @click="showMobileMenu = false"
            class="flex items-center px-3 py-2 rounded-md text-base font-medium text-gray-600 hover:text-gray-900 hover:bg-gray-50 space-x-3"
            active-class="text-primary-600 bg-primary-50"
          >
            <HomeIcon class="h-5 w-5" />
            <span>Dashboard</span>
          </router-link>
          
          <!-- Signals -->
          <router-link
            to="/signals"
            @click="showMobileMenu = false"
            class="flex items-center px-3 py-2 rounded-md text-base font-medium text-gray-600 hover:text-gray-900 hover:bg-gray-50 space-x-3"
            active-class="text-primary-600 bg-primary-50"
          >
            <ChartBarIcon class="h-5 w-5" />
            <span>Signals</span>
          </router-link>
          
          <!-- Trades -->
          <router-link
            to="/trades"
            @click="showMobileMenu = false"
            class="flex items-center px-3 py-2 rounded-md text-base font-medium text-gray-600 hover:text-gray-900 hover:bg-gray-50 space-x-3"
            active-class="text-primary-600 bg-primary-50"
          >
            <CurrencyDollarIcon class="h-5 w-5" />
            <span>Trades</span>
          </router-link>
          
          <!-- Positions -->
          <router-link
            to="/positions"
            @click="showMobileMenu = false"
            class="flex items-center px-3 py-2 rounded-md text-base font-medium text-gray-600 hover:text-gray-900 hover:bg-gray-50 space-x-3"
            active-class="text-primary-600 bg-primary-50"
          >
            <BanknotesIcon class="h-5 w-5" />
            <span>Positions</span>
          </router-link>
          
          <!-- Separator -->
          <div class="border-t border-gray-200 my-3"></div>
          
          <!-- Levels Monitoring -->
          <router-link
            to="/monitoring"
            @click="showMobileMenu = false"
            class="flex items-center px-3 py-2 rounded-md text-base font-medium text-gray-600 hover:text-gray-900 hover:bg-gray-50 space-x-3"
            active-class="text-primary-600 bg-primary-50"
          >
            <ChartBarIcon class="h-5 w-5" />
            <span>Levels Monitoring</span>
          </router-link>
          
          <!-- Scripts Manager -->
          <router-link
            to="/script-manager"
            @click="showMobileMenu = false"
            class="flex items-center px-3 py-2 rounded-md text-base font-medium text-gray-600 hover:text-gray-900 hover:bg-gray-50 space-x-3"
            active-class="text-primary-600 bg-primary-50"
          >
            <CommandLineIcon class="h-5 w-5" />
            <span>Scripts Manager</span>
          </router-link>
          
          <!-- Settings -->
          <router-link
            to="/settings"
            @click="showMobileMenu = false"
            class="flex items-center px-3 py-2 rounded-md text-base font-medium text-gray-600 hover:text-gray-900 hover:bg-gray-50 space-x-3"
            active-class="text-primary-600 bg-primary-50"
          >
            <CogIcon class="h-5 w-5" />
            <span>Settings</span>
          </router-link>
          
          <!-- Logout -->
          <button
            v-if="isAuthenticated"
            @click="logout"
            class="w-full flex items-center px-3 py-2 rounded-md text-base font-medium text-red-600 hover:text-red-700 hover:bg-red-50 space-x-3"
          >
            <ArrowRightOnRectangleIcon class="h-5 w-5 text-red-500" />
            <span>Logout</span>
          </button>
        </div>
      </div>
    </nav>

    <!-- Main Content -->
    <main>
      <router-view />
    </main>

    <!-- Error Display Component -->
    <ErrorDisplay />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useAccountStore } from '@/stores/account'
import ErrorDisplay from '@/components/ErrorDisplay.vue'
import { HomeIcon, ChartBarIcon, CurrencyDollarIcon, BanknotesIcon, EllipsisHorizontalIcon, ChevronDownIcon, CheckIcon, CogIcon, CommandLineIcon, CircleStackIcon, ArrowRightOnRectangleIcon, Bars3Icon, XMarkIcon } from '@heroicons/vue/24/outline'

const router = useRouter()
const authStore = useAuthStore()
const accountStore = useAccountStore()

const showAccountDropdown = ref(false)
const showMoreDropdown = ref(false)
const showMobileMenu = ref(false)
const isAuthenticated = computed(() => authStore.isAuthenticated)
const isMoreRouteActive = computed(() => {
  const path = router.currentRoute.value.path
  return path === '/monitoring' || path === '/script-manager' || path === '/database-compare' || path === '/settings'
})

const logout = () => {
  authStore.logout()
  accountStore.clearActiveAccount()
  router.push('/login')
}

const switchAccount = async (accountId: number) => {
  showAccountDropdown.value = false
  try {
    await accountStore.activateAccount(accountId)
    // Emit an event that components can listen to for account changes
    window.dispatchEvent(new CustomEvent('account-switched', { detail: { accountId } }))
  } catch (error) {
    console.error('Error switching account:', error)
  }
}

// Close dropdowns when clicking outside
const closeDropdowns = (event: Event) => {
  // Only close if the click is not on dropdown buttons or dropdown content
  const target = event.target as HTMLElement
  if (!target.closest('.dropdown-container')) {
    showAccountDropdown.value = false
    showMoreDropdown.value = false
    showMobileMenu.value = false
  }
}

// Load account data when authenticated
onMounted(async () => {
  if (isAuthenticated.value) {
    await accountStore.fetchActiveAccount()
    await accountStore.fetchAccounts()
  }
  
  // Add click listener for closing dropdowns
  document.addEventListener('click', closeDropdowns)
})

onUnmounted(() => {
  document.removeEventListener('click', closeDropdowns)
})
</script> 