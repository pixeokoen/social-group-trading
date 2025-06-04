<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Navigation -->
    <nav class="bg-white shadow-sm">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between h-16">
          <div class="flex">
            <div class="flex-shrink-0 flex items-center">
              <h1 class="text-xl font-bold text-primary-600">Social Trading</h1>
            </div>
            <div class="hidden sm:ml-6 sm:flex sm:space-x-8">
              <router-link
                to="/"
                class="border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium"
                active-class="border-primary-500 text-gray-900"
              >
                Dashboard
              </router-link>
              <router-link
                to="/signals"
                class="border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium"
                active-class="border-primary-500 text-gray-900"
              >
                Signals
              </router-link>
              <router-link
                to="/trades"
                class="border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium"
                active-class="border-primary-500 text-gray-900"
              >
                Trades
              </router-link>
              <router-link
                to="/positions"
                class="border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium"
                active-class="border-primary-500 text-gray-900"
              >
                Positions
              </router-link>
              <router-link
                to="/settings"
                class="border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium"
                active-class="border-primary-500 text-gray-900"
              >
                Settings
              </router-link>
            </div>
          </div>
          <div class="flex items-center space-x-4">
            <!-- Account Switcher -->
            <div v-if="isAuthenticated" class="relative">
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
                  <svg class="ml-1 h-5 w-5 text-gray-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clip-rule="evenodd" />
                  </svg>
                </div>
              </button>
              
              <!-- Dropdown -->
              <div
                v-if="showAccountDropdown"
                @click.away="showAccountDropdown = false"
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
                    <svg
                      v-if="account.id === accountStore.activeAccountId"
                      class="h-4 w-4 text-primary-600"
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 20 20"
                      fill="currentColor"
                    >
                      <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
                    </svg>
                  </div>
                  <div class="border-t border-gray-100 mt-1 pt-1">
                    <router-link
                      to="/settings"
                      @click="showAccountDropdown = false"
                      class="px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 block"
                    >
                      Manage Accounts
                    </router-link>
                  </div>
                </div>
              </div>
            </div>

            <button
              v-if="!isAuthenticated"
              @click="$router.push('/login')"
              class="bg-primary-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-primary-700"
            >
              Login
            </button>
            <button
              v-else
              @click="logout"
              class="text-gray-500 hover:text-gray-700 px-4 py-2 text-sm font-medium"
            >
              Logout
            </button>
          </div>
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
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useAccountStore } from '@/stores/account'
import ErrorDisplay from '@/components/ErrorDisplay.vue'

const router = useRouter()
const authStore = useAuthStore()
const accountStore = useAccountStore()

const showAccountDropdown = ref(false)
const isAuthenticated = computed(() => authStore.isAuthenticated)

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

// Load account data when authenticated
onMounted(async () => {
  if (isAuthenticated.value) {
    await accountStore.fetchActiveAccount()
    await accountStore.fetchAccounts()
  }
})
</script> 