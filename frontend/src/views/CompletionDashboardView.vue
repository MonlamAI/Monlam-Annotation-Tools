<template>
  <v-container fluid class="pa-6">
    <!-- Header -->
    <v-row class="mb-6">
      <v-col cols="12">
        <div class="d-flex align-center">
          <v-btn
            icon
            variant="text"
            :to="`/projects/${projectId}`"
          >
            <v-icon>mdi-arrow-left</v-icon>
          </v-btn>
          <div class="ml-4">
            <h1 class="text-h4 monlam-gold">
              {{ project?.tibetan_name || project?.name }}
            </h1>
            <p class="text-body-2 text-grey">Completion Dashboard - འགྲུབ་ཚད་བཀོད་ཁྲ།</p>
          </div>
        </div>
      </v-col>
    </v-row>
    
    <!-- Loading State -->
    <v-row v-if="loading">
      <v-col cols="12" class="text-center py-8">
        <v-progress-circular indeterminate color="primary" size="64" />
      </v-col>
    </v-row>
    
    <template v-else>
      <!-- Overall Progress -->
      <v-row class="mb-6">
        <v-col cols="12">
          <v-card>
            <v-card-title class="monlam-gold">
              📊 Overall Progress
            </v-card-title>
            <v-card-text>
              <!-- Progress Bar -->
              <div class="completion-progress mb-4">
                <div 
                  class="progress-fill" 
                  :style="{ width: `${summary?.completion_rate || 0}%` }"
                ></div>
              </div>
              <div class="text-center text-h4 monlam-gold mb-6">
                {{ summary?.completion_rate || 0 }}% Complete
              </div>
              
              <!-- Stats Cards -->
              <v-row>
                <v-col cols="6" sm="4" md="2">
                  <v-card flat class="text-center pa-4 bg-grey-lighten-3 hover-lift">
                    <div class="text-h5">{{ summary?.total || 0 }}</div>
                    <div class="text-caption">Total</div>
                  </v-card>
                </v-col>
                <v-col cols="6" sm="4" md="2">
                  <v-card flat class="text-center pa-4 status-pending hover-lift">
                    <div class="text-h5">{{ summary?.pending || 0 }}</div>
                    <div class="text-caption">Pending</div>
                  </v-card>
                </v-col>
                <v-col cols="6" sm="4" md="2">
                  <v-card flat class="text-center pa-4 status-in_progress hover-lift">
                    <div class="text-h5">{{ summary?.in_progress || 0 }}</div>
                    <div class="text-caption">In Progress</div>
                  </v-card>
                </v-col>
                <v-col cols="6" sm="4" md="2">
                  <v-card flat class="text-center pa-4 status-submitted hover-lift">
                    <div class="text-h5">{{ summary?.submitted || 0 }}</div>
                    <div class="text-caption">Submitted</div>
                  </v-card>
                </v-col>
                <v-col cols="6" sm="4" md="2">
                  <v-card flat class="text-center pa-4 status-approved hover-lift">
                    <div class="text-h5">{{ summary?.approved || 0 }}</div>
                    <div class="text-caption">Approved</div>
                  </v-card>
                </v-col>
                <v-col cols="6" sm="4" md="2">
                  <v-card flat class="text-center pa-4 status-rejected hover-lift">
                    <div class="text-h5">{{ summary?.rejected || 0 }}</div>
                    <div class="text-caption">Rejected</div>
                  </v-card>
                </v-col>
              </v-row>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
      
      <!-- Performance Tables -->
      <v-row>
        <!-- Annotator Performance -->
        <v-col cols="12" md="6">
          <v-card>
            <v-card-title class="monlam-gold">
              ✍️ Annotator Performance
            </v-card-title>
            <v-card-text>
              <v-table v-if="annotatorStats.length > 0">
                <thead>
                  <tr>
                    <th>Annotator</th>
                    <th class="text-right">Completed</th>
                    <th class="text-right">Approved</th>
                    <th class="text-right">Rejected</th>
                    <th class="text-right">Success Rate</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="stat in annotatorStats" :key="stat.annotated_by__id">
                    <td>{{ stat.annotated_by__username }}</td>
                    <td class="text-right">{{ stat.completed }}</td>
                    <td class="text-right text-success">{{ stat.approved }}</td>
                    <td class="text-right text-error">{{ stat.rejected }}</td>
                    <td class="text-right">
                      <v-chip 
                        size="small" 
                        :color="stat.success_rate >= 90 ? 'success' : stat.success_rate >= 70 ? 'warning' : 'error'"
                      >
                        {{ stat.success_rate }}%
                      </v-chip>
                    </td>
                  </tr>
                </tbody>
              </v-table>
              <div v-else class="text-center text-grey py-8">
                No annotations yet
              </div>
            </v-card-text>
          </v-card>
        </v-col>
        
        <!-- Reviewer Performance -->
        <v-col cols="12" md="6">
          <v-card>
            <v-card-title class="monlam-gold">
              ✅ Reviewer Performance
            </v-card-title>
            <v-card-text>
              <v-table v-if="reviewerStats.length > 0">
                <thead>
                  <tr>
                    <th>Reviewer</th>
                    <th class="text-right">Reviewed</th>
                    <th class="text-right">Approved</th>
                    <th class="text-right">Rejected</th>
                    <th class="text-right">Approval Rate</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="stat in reviewerStats" :key="stat.reviewed_by__id">
                    <td>{{ stat.reviewed_by__username }}</td>
                    <td class="text-right">{{ stat.reviewed }}</td>
                    <td class="text-right text-success">{{ stat.approved }}</td>
                    <td class="text-right text-error">{{ stat.rejected }}</td>
                    <td class="text-right">
                      <v-chip size="small" color="primary">
                        {{ stat.approval_rate }}%
                      </v-chip>
                    </td>
                  </tr>
                </tbody>
              </v-table>
              <div v-else class="text-center text-grey py-8">
                No reviews yet
              </div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
      
      <!-- Actions -->
      <v-row class="mt-6">
        <v-col cols="12">
          <v-card>
            <v-card-actions>
              <v-btn 
                color="primary" 
                variant="outlined"
                :to="`/projects/${projectId}`"
              >
                <v-icon start>mdi-arrow-left</v-icon>
                Back to Project
              </v-btn>
              <v-spacer />
              <v-btn 
                color="primary"
                @click="exportReport"
              >
                <v-icon start>mdi-download</v-icon>
                Export Report
              </v-btn>
            </v-card-actions>
          </v-card>
        </v-col>
      </v-row>
    </template>
  </v-container>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useProjectStore } from '@/stores/project'
import { useTrackingStore } from '@/stores/tracking'

const route = useRoute()
const projectStore = useProjectStore()
const trackingStore = useTrackingStore()

const projectId = computed(() => route.params.projectId)
const project = computed(() => projectStore.currentProject)
const loading = computed(() => trackingStore.loading)
const summary = computed(() => trackingStore.summary)
const annotatorStats = computed(() => trackingStore.annotatorStats)
const reviewerStats = computed(() => trackingStore.reviewerStats)

function exportReport() {
  // Export tracking data as CSV
  window.open(`/v1/projects/${projectId.value}/tracking/export/?format=csv`, '_blank')
}

onMounted(async () => {
  await projectStore.fetchProject(projectId.value)
  await Promise.all([
    trackingStore.fetchSummary(projectId.value),
    trackingStore.fetchAnnotatorStats(projectId.value),
    trackingStore.fetchReviewerStats(projectId.value),
  ])
})
</script>

<style scoped>
.status-pending { background-color: #e0e0e0 !important; color: #666; }
.status-in_progress { background-color: #2196f3 !important; color: white; }
.status-submitted { background-color: #ff9800 !important; color: white; }
.status-approved { background-color: #4caf50 !important; color: white; }
.status-rejected { background-color: #f44336 !important; color: white; }
</style>

