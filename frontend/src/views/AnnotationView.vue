<template>
  <v-container fluid class="pa-6">
    <!-- Navigation Header -->
    <v-row class="mb-4">
      <v-col cols="12">
        <div class="d-flex align-center">
          <v-btn
            icon
            variant="text"
            :disabled="!hasPrevious"
            @click="navigatePrevious"
          >
            <v-icon>mdi-chevron-left</v-icon>
          </v-btn>
          
          <span class="text-h6 mx-4">
            Example #{{ currentExample?.id || '—' }}
            <span class="text-caption text-grey">
              ({{ currentIndex + 1 }} / {{ totalCount }})
            </span>
          </span>
          
          <v-btn
            icon
            variant="text"
            :disabled="!hasNext"
            @click="navigateNext"
          >
            <v-icon>mdi-chevron-right</v-icon>
          </v-btn>
          
          <v-spacer />
          
          <v-btn
            variant="outlined"
            :to="`/projects/${projectId}/dataset`"
          >
            <v-icon start>mdi-view-list</v-icon>
            Dataset
          </v-btn>
        </div>
      </v-col>
    </v-row>
    
    <!-- Loading State -->
    <v-row v-if="loading">
      <v-col cols="12" class="text-center py-8">
        <v-progress-circular indeterminate color="primary" size="64" />
      </v-col>
    </v-row>
    
    <!-- No Examples -->
    <v-row v-else-if="!currentExample">
      <v-col cols="12" class="text-center py-8">
        <v-icon size="80" color="grey-lighten-1">mdi-check-all</v-icon>
        <p class="text-h5 mt-4 text-grey">All done!</p>
        <p class="text-body-2 text-grey">
          No more examples to annotate
        </p>
        <v-btn
          color="primary"
          class="mt-4"
          :to="`/projects/${projectId}/dataset`"
        >
          View Dataset
        </v-btn>
      </v-col>
    </v-row>
    
    <!-- Annotation Content -->
    <template v-else>
      <!-- S3 Audio Player for STT Projects -->
      <v-row v-if="isSttProject && audioUrl" class="mb-4">
        <v-col cols="12">
          <S3AudioPlayer 
            :audio-url="audioUrl"
            :auto-play="true"
            :auto-loop="true"
            @play="onAudioPlay"
            @pause="onAudioPause"
            @ended="onAudioEnded"
          />
        </v-col>
      </v-row>
      
      <!-- Text Display -->
      <v-row class="mb-4">
        <v-col cols="12">
          <v-card>
            <v-card-title v-if="isSttProject">Audio Transcript</v-card-title>
            <v-card-title v-else>Text</v-card-title>
            <v-card-text>
              <div class="tibetan-text text-h6 pa-4 bg-grey-lighten-4 rounded">
                {{ currentExample.text || currentExample.display_text }}
              </div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
      
      <!-- Annotation Input (varies by project type) -->
      <v-row class="mb-4">
        <v-col cols="12">
          <v-card>
            <v-card-title>Annotation</v-card-title>
            <v-card-text>
              <!-- Text Label (for STT/Seq2Seq) -->
              <template v-if="isSttProject || isSeq2SeqProject">
                <v-textarea
                  v-model="annotationText"
                  label="Enter transcription / translation"
                  rows="4"
                  class="tibetan-text"
                  :placeholder="isSttProject ? 'བོད་ཡིག་ཡིག་སྒྱུར།' : 'Enter text...'"
                />
              </template>
              
              <!-- Category Labels (for Classification) -->
              <template v-else-if="isClassificationProject">
                <div class="d-flex flex-wrap gap-2">
                  <v-chip
                    v-for="label in labels"
                    :key="label.id"
                    :color="selectedLabels.includes(label.id) ? label.background_color : 'grey-lighten-2'"
                    :text-color="selectedLabels.includes(label.id) ? label.text_color : 'black'"
                    size="large"
                    @click="toggleLabel(label.id)"
                  >
                    {{ label.tibetan_text || label.text }}
                  </v-chip>
                </div>
              </template>
              
              <!-- Placeholder for other project types -->
              <template v-else>
                <p class="text-grey">
                  Annotation interface for {{ project?.project_type }} coming soon...
                </p>
              </template>
            </v-card-text>
            
            <v-card-actions>
              <v-spacer />
              <v-btn variant="text" @click="skipExample">
                Skip
              </v-btn>
              <v-btn 
                color="primary" 
                :loading="saving"
                @click="saveAndNext"
              >
                Save & Next
              </v-btn>
            </v-card-actions>
          </v-card>
        </v-col>
      </v-row>
      
      <!-- Review Notes (if rejected) -->
      <v-row v-if="reviewNotes" class="mb-4">
        <v-col cols="12">
          <v-alert type="warning" variant="tonal">
            <strong>Review Notes:</strong> {{ reviewNotes }}
          </v-alert>
        </v-col>
      </v-row>
    </template>
    
    <!-- Approve/Reject Buttons (for reviewers) -->
    <ApproveRejectButtons 
      v-if="currentExample"
      :example-id="currentExample.id"
      @status-changed="onStatusChanged"
    />
  </v-container>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount, inject } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useProjectStore } from '@/stores/project'
import { useExampleStore } from '@/stores/example'
import { useTrackingStore } from '@/stores/tracking'
import api from '@/services/api'
import S3AudioPlayer from '@/components/annotation/S3AudioPlayer.vue'
import ApproveRejectButtons from '@/components/annotation/ApproveRejectButtons.vue'

const route = useRoute()
const router = useRouter()
const projectStore = useProjectStore()
const exampleStore = useExampleStore()
const trackingStore = useTrackingStore()
const snackbar = inject('snackbar')

const projectId = computed(() => route.params.projectId)
const exampleId = computed(() => route.params.exampleId)
const project = computed(() => projectStore.currentProject)
const currentExample = computed(() => exampleStore.currentExample)
const loading = computed(() => exampleStore.loading)
const totalCount = computed(() => exampleStore.totalCount)
const reviewNotes = computed(() => trackingStore.trackingStatus?.review_notes)

// Audio URL - from meta.audio_url or file_url
const audioUrl = computed(() => {
  if (!currentExample.value) return null
  // Check audio_url in serializer (extracted from meta)
  if (currentExample.value.audio_url) return currentExample.value.audio_url
  // Fallback to meta fields
  const meta = currentExample.value.meta || {}
  return meta.audio_url || meta.audio || meta.audio_link || 
         meta.file_name || meta.s3_url || meta.media_url || 
         currentExample.value.file_url || null
})

// Annotation state
const annotationText = ref('')
const selectedLabels = ref([])
const labels = ref([])
const saving = ref(false)

// Navigation
const currentIndex = computed(() => {
  if (!currentExample.value) return 0
  return exampleStore.examples.findIndex(e => e.id === currentExample.value.id)
})
const hasPrevious = computed(() => currentIndex.value > 0 || exampleStore.currentPage > 1)
const hasNext = computed(() => 
  currentIndex.value < exampleStore.examples.length - 1 || 
  (exampleStore.currentPage * exampleStore.pageSize) < totalCount.value
)

// Project type checks
const isSttProject = computed(() => project.value?.project_type === 'speech_to_text')
const isSeq2SeqProject = computed(() => project.value?.project_type === 'seq2seq')
const isClassificationProject = computed(() => 
  project.value?.project_type === 'document_classification'
)

// Methods
async function loadExample(id) {
  if (id) {
    await exampleStore.fetchExample(projectId.value, id)
    await trackingStore.fetchTrackingStatus(projectId.value, id)
    // Acquire lock
    await trackingStore.acquireLock(projectId.value, id)
  } else {
    // Load first available example
    await exampleStore.fetchExamples(projectId.value)
    if (exampleStore.examples.length > 0) {
      const firstExample = exampleStore.examples[0]
      router.replace(`/projects/${projectId.value}/annotation/${firstExample.id}`)
    }
  }
}

async function navigatePrevious() {
  const prevExample = await exampleStore.getPreviousExample(projectId.value, currentExample.value.id)
  if (prevExample) {
    await releaseLock()
    router.push(`/projects/${projectId.value}/annotation/${prevExample.id}`)
  }
}

async function navigateNext() {
  const nextExample = await exampleStore.getNextExample(projectId.value, currentExample.value.id)
  if (nextExample) {
    await releaseLock()
    router.push(`/projects/${projectId.value}/annotation/${nextExample.id}`)
  }
}

function toggleLabel(labelId) {
  const index = selectedLabels.value.indexOf(labelId)
  if (index === -1) {
    selectedLabels.value.push(labelId)
  } else {
    selectedLabels.value.splice(index, 1)
  }
}

async function saveAndNext() {
  if (!currentExample.value) return
  
  saving.value = true
  try {
    // Save annotation based on project type
    if (isSttProject.value || isSeq2SeqProject.value) {
      await api.post(`/projects/${projectId.value}/examples/${currentExample.value.id}/text-labels/`, {
        text: annotationText.value
      })
    } else if (isClassificationProject.value) {
      for (const labelId of selectedLabels.value) {
        await api.post(`/projects/${projectId.value}/examples/${currentExample.value.id}/categories/`, {
          label: labelId
        })
      }
    }
    
    // Mark as submitted
    await trackingStore.markSubmitted(projectId.value, currentExample.value.id)
    
    snackbar.message = 'Annotation saved!'
    snackbar.color = 'success'
    snackbar.show = true
    
    // Clear and navigate to next
    annotationText.value = ''
    selectedLabels.value = []
    await navigateNext()
  } catch (error) {
    snackbar.message = 'Failed to save annotation'
    snackbar.color = 'error'
    snackbar.show = true
  } finally {
    saving.value = false
  }
}

function skipExample() {
  navigateNext()
}

async function releaseLock() {
  if (currentExample.value) {
    await trackingStore.releaseLock(projectId.value, currentExample.value.id)
  }
}

function onStatusChanged(newStatus) {
  // Refresh example list after status change
  exampleStore.fetchExamples(projectId.value)
}

// Audio event handlers
function onAudioPlay() {
  console.log('Audio playing')
}

function onAudioPause() {
  console.log('Audio paused')
}

function onAudioEnded() {
  console.log('Audio ended (will auto-loop if enabled)')
}

// Watch for route changes
watch(() => route.params.exampleId, async (newId) => {
  if (newId) {
    await loadExample(newId)
  }
})

// Lifecycle
onMounted(async () => {
  await projectStore.fetchProject(projectId.value)
  await loadExample(exampleId.value)
  
  // Load labels for classification projects
  if (isClassificationProject.value) {
    try {
      const response = await api.get(`/projects/${projectId.value}/category-types/`)
      labels.value = response.data.results || response.data
    } catch (e) {
      console.error('Failed to load labels:', e)
    }
  }
})

onBeforeUnmount(() => {
  releaseLock()
})
</script>

