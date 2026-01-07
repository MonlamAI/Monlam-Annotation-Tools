import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

// Views
import LoginView from '@/views/LoginView.vue'
import DashboardView from '@/views/DashboardView.vue'
import ProjectListView from '@/views/ProjectListView.vue'
import ProjectDetailView from '@/views/ProjectDetailView.vue'
import DatasetView from '@/views/DatasetView.vue'
import AnnotationView from '@/views/AnnotationView.vue'
import CompletionDashboardView from '@/views/CompletionDashboardView.vue'
import SettingsView from '@/views/SettingsView.vue'

const routes = [
  {
    path: '/login',
    name: 'login',
    component: LoginView,
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    name: 'dashboard',
    component: DashboardView,
    meta: { requiresAuth: true }
  },
  {
    path: '/projects',
    name: 'projects',
    component: ProjectListView,
    meta: { requiresAuth: true }
  },
  {
    path: '/projects/:projectId',
    name: 'project-detail',
    component: ProjectDetailView,
    meta: { requiresAuth: true }
  },
  {
    path: '/projects/:projectId/dataset',
    name: 'dataset',
    component: DatasetView,
    meta: { requiresAuth: true }
  },
  {
    path: '/projects/:projectId/annotation/:exampleId?',
    name: 'annotation',
    component: AnnotationView,
    meta: { requiresAuth: true }
  },
  // Metrics / Completion Dashboard (enhanced metrics view)
  {
    path: '/projects/:projectId/metrics',
    name: 'metrics',
    component: CompletionDashboardView,
    meta: { requiresAuth: true }
  },
  {
    path: '/projects/:projectId/settings',
    name: 'settings',
    component: SettingsView,
    meta: { requiresAuth: true }
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Navigation guard
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next({ name: 'login', query: { redirect: to.fullPath } })
  } else if (to.name === 'login' && authStore.isAuthenticated) {
    next({ name: 'dashboard' })
  } else {
    next()
  }
})

export default router

