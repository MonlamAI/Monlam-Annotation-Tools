<template>
  <v-container fluid class="pa-6">
    <!-- Welcome Section -->
    <v-row class="mb-6">
      <v-col cols="12">
        <h1 class="text-h4 monlam-gold">
          བཀྲ་ཤིས་བདེ་ལེགས། Welcome, {{ username }}!
        </h1>
        <p class="text-body-1 text-grey mt-2">
          Select a project to start annotating
        </p>
      </v-col>
    </v-row>
    
    <!-- Quick Stats -->
    <v-row class="mb-6">
      <v-col cols="12" sm="6" md="3">
        <v-card class="hover-lift">
          <v-card-text class="text-center">
            <v-icon size="48" color="primary">mdi-folder-multiple</v-icon>
            <div class="text-h4 mt-2">{{ projectCount }}</div>
            <div class="text-caption text-grey">Projects</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" sm="6" md="3">
        <v-card class="hover-lift">
          <v-card-text class="text-center">
            <v-icon size="48" color="success">mdi-check-circle</v-icon>
            <div class="text-h4 mt-2">{{ totalApproved }}</div>
            <div class="text-caption text-grey">Approved</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" sm="6" md="3">
        <v-card class="hover-lift">
          <v-card-text class="text-center">
            <v-icon size="48" color="warning">mdi-clock-outline</v-icon>
            <div class="text-h4 mt-2">{{ totalPending }}</div>
            <div class="text-caption text-grey">Pending</div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" sm="6" md="3">
        <v-card class="hover-lift">
          <v-card-text class="text-center">
            <v-icon size="48" color="info">mdi-send</v-icon>
            <div class="text-h4 mt-2">{{ totalSubmitted }}</div>
            <div class="text-caption text-grey">Submitted</div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
    
    <!-- Projects List -->
    <v-row>
      <v-col cols="12">
        <v-card>
          <v-card-title class="d-flex align-center">
            <span class="monlam-gold">Your Projects</span>
            <v-spacer />
            <v-btn color="primary" to="/projects">
              View All
            </v-btn>
          </v-card-title>
          
          <v-card-text>
            <v-row v-if="loading">
              <v-col cols="12" class="text-center">
                <v-progress-circular indeterminate color="primary" />
              </v-col>
            </v-row>
            
            <v-row v-else-if="projects.length === 0">
              <v-col cols="12" class="text-center py-8">
                <v-icon size="64" color="grey-lighten-1">mdi-folder-open-outline</v-icon>
                <p class="text-h6 mt-4 text-grey">No projects yet</p>
                <v-btn color="primary" class="mt-4" to="/projects">
                  Create Your First Project
                </v-btn>
              </v-col>
            </v-row>
            
            <v-row v-else>
              <v-col 
                v-for="project in projects.slice(0, 6)" 
                :key="project.id"
                cols="12" 
                sm="6" 
                md="4"
              >
                <v-card 
                  class="hover-lift"
                  :to="`/projects/${project.id}`"
                >
                  <v-card-title>
                    {{ project.tibetan_name || project.name }}
                  </v-card-title>
                  <v-card-subtitle>
                    {{ project.name }}
                  </v-card-subtitle>
                  <v-card-text>
                    <v-chip size="small" class="mr-2">
                      {{ project.project_type }}
                    </v-chip>
                    <v-chip size="small" color="primary" variant="outlined">
                      {{ project.member_count }} members
                    </v-chip>
                  </v-card-text>
                </v-card>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useProjectStore } from '@/stores/project'

const authStore = useAuthStore()
const projectStore = useProjectStore()

const username = computed(() => authStore.username)
const projects = computed(() => projectStore.projects)
const loading = computed(() => projectStore.loading)
const projectCount = computed(() => projects.value.length)

// TODO: Get these from actual data
const totalApproved = ref(0)
const totalPending = ref(0)
const totalSubmitted = ref(0)

onMounted(async () => {
  await projectStore.fetchProjects()
})
</script>

