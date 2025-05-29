import { createRouter, createWebHistory } from 'vue-router'
import DashboardView from '@/views/DashboardView.vue'
import LoginView from '@/views/LoginView.vue'
import SignalsView from '@/views/SignalsView.vue'
import TradesView from '@/views/TradesView.vue'
import SettingsView from '@/views/SettingsView.vue'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: LoginView,
      meta: { requiresAuth: false }
    },
    {
      path: '/',
      redirect: '/dashboard'
    },
    {
      path: '/dashboard',
      name: 'dashboard',
      component: DashboardView,
      meta: { requiresAuth: true }
    },
    {
      path: '/signals',
      name: 'signals',
      component: SignalsView,
      meta: { requiresAuth: true }
    },
    {
      path: '/trades',
      name: 'trades',
      component: TradesView,
      meta: { requiresAuth: true }
    },
    {
      path: '/settings',
      name: 'settings',
      component: SettingsView,
      meta: { requiresAuth: true }
    }
  ]
})

// Navigation guard
router.beforeEach((to: any, from: any, next: any) => {
  const authStore = useAuthStore()
  const requiresAuth = to.matched.some((record: any) => record.meta.requiresAuth !== false)
  
  if (requiresAuth && !authStore.isAuthenticated) {
    next('/login')
  } else if (to.path === '/login' && authStore.isAuthenticated) {
    next('/dashboard')
  } else {
    next()
  }
})

export default router 