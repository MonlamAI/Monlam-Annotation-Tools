<template>
  <v-container fluid class="pa-6">
    <v-row v-if="loading">
      <v-col cols="12" class="text-center py-8">
        <v-progress-circular indeterminate color="primary" size="64" />
      </v-col>
    </v-row>
    
    <template v-else-if="project">
      <!-- Header -->
      <v-row class="mb-6">
        <v-col cols="12">
          <div class="d-flex align-center">
            <div>
              <h1 class="text-h4 monlam-gold">
                {{ project.tibetan_name || project.name }}
              </h1>
              <p v-if="project.tibetan_name" class="text-body-1 text-grey">
                {{ project.name }}
              </p>
            </div>
            <v-spacer />
            <v-chip class="mr-2">
              {{ formatProjectType(project.project_type) }}
            </v-chip>
            <v-btn
              v-if="canManage"
              variant="outlined"
              :to="`/projects/${projectId}/settings`"
            >
              <v-icon start>mdi-cog</v-icon>
              Settings
            </v-btn>
          </div>
        </v-col>
      </v-row>
      
      <!-- Quick Stats -->
      <v-row class="mb-6">
        <v-col cols="6" sm="3">
          <v-card class="hover-lift">
            <v-card-text class="text-center">
              <v-icon size="40" color="grey">mdi-file-document-multiple</v-icon>
              <div class="text-h5 mt-2">{{ stats.total || 0 }}</div>
              <div class="text-caption">Total Examples</div>
            </v-card-text>
          </v-card>
        </v-col>
        <v-col cols="6" sm="3">
          <v-card class="hover-lift">
            <v-card-text class="text-center">
              <v-icon size="40" color="warning">mdi-clock</v-icon>
              <div class="text-h5 mt-2">{{ stats.pending || 0 }}</div>
              <div class="text-caption">Pending</div>
            </v-card-text>
          </v-card>
        </v-col>
        <v-col cols="6" sm="3">
          <v-card class="hover-lift">
            <v-card-text class="text-center">
              <v-icon size="40" color="success">mdi-check-circle</v-icon>
              <div class="text-h5 mt-2">{{ stats.approved || 0 }}</div>
              <div class="text-caption">Approved</div>
            </v-card-text>
          </v-card>
        </v-col>
        <v-col cols="6" sm="3">
          <v-card class="hover-lift">
            <v-card-text class="text-center">
              <div class="text-h5 monlam-gold">{{ stats.completion_rate || 0 }}%</div>
              <div class="text-caption">Completion</div>
              <v-progress-linear
                :model-value="stats.completion_rate || 0"
                color="primary"
                height="8"
                rounded
                class="mt-2"
              />
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
      
      <!-- Quick Actions -->
      <v-row class="mb-6">
        <v-col cols="12">
          <v-card>
            <v-card-title>Quick Actions</v-card-title>
            <v-card-text>
              <v-row>
                <v-col cols="6" sm="4" md="2">
                  <v-btn
                    block
                    color="primary"
                    :to="`/projects/${projectId}/annotation`"
                  >
                    <v-icon start>mdi-pencil</v-icon>
                    Annotate
                  </v-btn>
                </v-col>
                <v-col cols="6" sm="4" md="2">
                  <v-btn
                    block
                    variant="outlined"
                    :to="`/projects/${projectId}/dataset`"
                  >
                    <v-icon start>mdi-database</v-icon>
                    Dataset
                  </v-btn>
                </v-col>
                <v-col cols="6" sm="4" md="2">
                  <v-btn
                    block
                    variant="outlined"
                    :to="`/monlam/${projectId}/completion`"
                  >
                    <v-icon start>mdi-chart-bar</v-icon>
                    Metrics
                  </v-btn>
                </v-col>
                <v-col v-if="canManage" cols="6" sm="4" md="2">
                  <v-btn
                    block
                    variant="outlined"
                    :to="`/projects/${projectId}/import`"
                  >
                    <v-icon start>mdi-upload</v-icon>
                    Import
                  </v-btn>
                </v-col>
                <v-col v-if="canManage" cols="6" sm="4" md="2">
                  <v-btn
                    block
                    variant="outlined"
                    :to="`/projects/${projectId}/export`"
                  >
                    <v-icon start>mdi-download</v-icon>
                    Export
                  </v-btn>
                </v-col>
              </v-row>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
      
      <!-- Guideline -->
      <v-row v-if="project.guideline">
        <v-col cols="12">
          <v-card>
            <v-card-title>Annotation Guideline</v-card-title>
            <v-card-text>
              <div class="tibetan-text" v-html="project.guideline"></div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </template>
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useProjectStore } from '@/stores/project'
import { useTrackingStore } from '@/stores/tracking'

const route = useRoute()
const projectStore = useProjectStore()
const trackingStore = useTrackingStore()

const projectId = computed(() => route.params.projectId)
const project = computed(() => projectStore.currentProject)
const loading = computed(() => projectStore.loading)
const stats = computed(() => trackingStore.summary || {})

const canManage = computed(() => {
  const role = project.value?.current_user_role
  return role === 'project_manager' || role === 'project_admin'
})

const projectTypes = {
  sequence_labeling: 'Sequence Labeling',
  document_classification: 'Document Classification',
  speech_to_text: 'Speech to Text',
  seq2seq: 'Sequence to Sequence',
  image_classification: 'Image Classification',
}

function formatProjectType(type) {
  return projectTypes[type] || type
}

onMounted(async () => {
  await projectStore.fetchProject(projectId.value)
  await trackingStore.fetchSummary(projectId.value)
})
</script>

