<template>
  <v-app>
    <AppNavbar v-if="isAuthenticated" />
    <AppSidebar v-if="isAuthenticated && showSidebar" />
    
    <v-main>
      <router-view />
    </v-main>
    
    <v-snackbar
      v-model="snackbar.show"
      :color="snackbar.color"
      :timeout="3000"
      location="top"
    >
      {{ snackbar.message }}
      <template #actions>
        <v-btn variant="text" @click="snackbar.show = false">
          Close
        </v-btn>
      </template>
    </v-snackbar>
  </v-app>
</template>

<script setup>
import { computed, reactive } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import AppNavbar from '@/components/layout/AppNavbar.vue'
import AppSidebar from '@/components/layout/AppSidebar.vue'

const route = useRoute()
const authStore = useAuthStore()

const isAuthenticated = computed(() => authStore.isAuthenticated)
const showSidebar = computed(() => {
  return route.meta.showSidebar !== false && route.params.projectId
})

const snackbar = reactive({
  show: false,
  message: '',
  color: 'success'
})

// Provide snackbar to child components
provide('snackbar', snackbar)
</script>

<script>
import { provide } from 'vue'
export default {
  name: 'App'
}
</script>

