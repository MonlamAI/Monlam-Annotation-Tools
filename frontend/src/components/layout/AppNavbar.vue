<template>
  <v-app-bar app elevation="2" class="monlam-navy-bg">
    <v-app-bar-nav-icon 
      v-if="$vuetify.display.mobile" 
      @click="toggleDrawer"
      color="white"
    />
    
    <router-link to="/" class="d-flex align-center text-decoration-none">
      <img src="/logo.svg" alt="Monlam" height="36" class="mr-2" />
      <v-app-bar-title class="monlam-gold text-h6 font-weight-bold">
        སྨོན་ལམ།
        <span class="text-caption text-white ml-2">Annotation Tools</span>
      </v-app-bar-title>
    </router-link>
    
    <v-spacer />
    
    <!-- Project selector if in a project context -->
    <v-menu v-if="currentProject">
      <template #activator="{ props }">
        <v-btn variant="text" color="white" v-bind="props">
          {{ currentProject.tibetan_name || currentProject.name }}
          <v-icon end>mdi-chevron-down</v-icon>
        </v-btn>
      </template>
      <v-list density="compact">
        <v-list-item 
          v-for="project in recentProjects" 
          :key="project.id"
          :to="`/projects/${project.id}`"
        >
          <v-list-item-title>{{ project.tibetan_name || project.name }}</v-list-item-title>
        </v-list-item>
        <v-divider />
        <v-list-item to="/projects">
          <v-list-item-title>View All Projects</v-list-item-title>
        </v-list-item>
      </v-list>
    </v-menu>
    
    <v-spacer />
    
    <!-- User menu -->
    <v-menu>
      <template #activator="{ props }">
        <v-btn variant="text" color="white" v-bind="props">
          <v-avatar size="32" color="primary" class="mr-2">
            <span class="text-caption">{{ userInitials }}</span>
          </v-avatar>
          {{ username }}
          <v-icon end>mdi-chevron-down</v-icon>
        </v-btn>
      </template>
      <v-list density="compact">
        <v-list-item to="/profile">
          <template #prepend>
            <v-icon>mdi-account</v-icon>
          </template>
          <v-list-item-title>Profile</v-list-item-title>
        </v-list-item>
        <v-list-item @click="logout">
          <template #prepend>
            <v-icon>mdi-logout</v-icon>
          </template>
          <v-list-item-title>Logout</v-list-item-title>
        </v-list-item>
      </v-list>
    </v-menu>
  </v-app-bar>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useProjectStore } from '@/stores/project'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const projectStore = useProjectStore()

const username = computed(() => authStore.username)
const userInitials = computed(() => {
  const name = authStore.user?.username || ''
  return name.substring(0, 2).toUpperCase()
})

const currentProject = computed(() => projectStore.currentProject)
const recentProjects = computed(() => projectStore.projects.slice(0, 5))

const emit = defineEmits(['toggle-drawer'])

function toggleDrawer() {
  emit('toggle-drawer')
}

async function logout() {
  await authStore.logout()
  router.push('/login')
}
</script>

