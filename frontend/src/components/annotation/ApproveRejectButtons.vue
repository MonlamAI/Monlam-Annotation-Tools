<template>
  <div v-if="canReview" class="approve-reject-container">
    <!-- Status Display -->
    <div class="status-info">
      <div class="status-label">Status</div>
      <div class="status-value">
        <span :class="['status-badge', status]">
          {{ statusDisplay }}
        </span>
      </div>
      <div v-if="annotatedBy" class="annotator-name">
        by {{ annotatedBy }}
      </div>
    </div>
    
    <!-- Review Notes (for rejected) -->
    <div v-if="status === 'rejected' && reviewNotes" class="review-notes">
      <v-tooltip location="top">
        <template #activator="{ props }">
          <v-icon v-bind="props" color="error" size="small">mdi-alert-circle</v-icon>
        </template>
        <span>{{ reviewNotes }}</span>
      </v-tooltip>
    </div>
    
    <!-- Action Buttons -->
    <div class="action-buttons">
      <v-btn
        color="success"
        :loading="approving"
        :disabled="status === 'approved' || status === 'pending'"
        @click="handleApprove"
      >
        <v-icon start>mdi-check</v-icon>
        Approve
      </v-btn>
      
      <v-btn
        color="error"
        :loading="rejecting"
        :disabled="status === 'rejected' || status === 'pending'"
        @click="openRejectDialog"
      >
        <v-icon start>mdi-close</v-icon>
        Reject
      </v-btn>
    </div>
    
    <!-- Reject Dialog -->
    <v-dialog v-model="rejectDialog" max-width="500">
      <v-card>
        <v-card-title class="text-h6">
          <v-icon color="error" class="mr-2">mdi-alert</v-icon>
          Reject Annotation
        </v-card-title>
        <v-card-text>
          <p class="mb-4">Please provide a reason for rejection (required):</p>
          <v-textarea
            v-model="rejectNotes"
            label="Rejection Reason"
            placeholder="Explain why this annotation is being rejected..."
            :rules="[v => !!v || 'Rejection reason is required']"
            rows="3"
            counter
            autofocus
          />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="rejectDialog = false">
            Cancel
          </v-btn>
          <v-btn 
            color="error" 
            :disabled="!rejectNotes.trim()"
            :loading="rejecting"
            @click="handleReject"
          >
            Reject
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
    
    <!-- Approve Dialog (optional notes) -->
    <v-dialog v-model="approveDialog" max-width="500">
      <v-card>
        <v-card-title class="text-h6">
          <v-icon color="success" class="mr-2">mdi-check-circle</v-icon>
          Approve Annotation
        </v-card-title>
        <v-card-text>
          <p class="mb-4">Add approval notes (optional):</p>
          <v-textarea
            v-model="approveNotes"
            label="Approval Notes"
            placeholder="Any comments about this annotation..."
            rows="2"
          />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="approveDialog = false">
            Cancel
          </v-btn>
          <v-btn 
            color="success" 
            :loading="approving"
            @click="confirmApprove"
          >
            Approve
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount, inject } from 'vue'
import { useRoute } from 'vue-router'
import { useTrackingStore } from '@/stores/tracking'
import { useProjectStore } from '@/stores/project'

const props = defineProps({
  exampleId: {
    type: [Number, String],
    required: true
  }
})

const emit = defineEmits(['status-changed'])

const route = useRoute()
const trackingStore = useTrackingStore()
const projectStore = useProjectStore()
const snackbar = inject('snackbar')

const projectId = computed(() => route.params.projectId)

// State
const approving = ref(false)
const rejecting = ref(false)
const rejectDialog = ref(false)
const approveDialog = ref(false)
const rejectNotes = ref('')
const approveNotes = ref('')

// Computed
const canReview = computed(() => {
  const role = projectStore.currentProject?.current_user_role
  return ['approver', 'project_manager', 'project_admin'].includes(role)
})

const status = computed(() => trackingStore.trackingStatus?.status || 'pending')
const statusDisplay = computed(() => trackingStore.trackingStatus?.status_display || 'Pending')
const annotatedBy = computed(() => trackingStore.trackingStatus?.annotated_by)
const reviewNotes = computed(() => trackingStore.trackingStatus?.review_notes)

// Methods
async function fetchStatus() {
  await trackingStore.fetchTrackingStatus(projectId.value, props.exampleId)
}

function handleApprove() {
  approveNotes.value = ''
  approveDialog.value = true
}

async function confirmApprove() {
  approving.value = true
  try {
    const result = await trackingStore.approve(
      projectId.value, 
      props.exampleId, 
      approveNotes.value
    )
    
    if (result.success) {
      snackbar.message = '✅ Example approved successfully!'
      snackbar.color = 'success'
      snackbar.show = true
      approveDialog.value = false
      emit('status-changed', 'approved')
    } else {
      snackbar.message = result.error
      snackbar.color = 'error'
      snackbar.show = true
    }
  } finally {
    approving.value = false
  }
}

function openRejectDialog() {
  rejectNotes.value = ''
  rejectDialog.value = true
}

async function handleReject() {
  if (!rejectNotes.value.trim()) {
    snackbar.message = 'Rejection reason is required'
    snackbar.color = 'error'
    snackbar.show = true
    return
  }

  rejecting.value = true
  try {
    const result = await trackingStore.reject(
      projectId.value, 
      props.exampleId, 
      rejectNotes.value
    )
    
    if (result.success) {
      snackbar.message = '✅ Example rejected. Annotator will see it for revision.'
      snackbar.color = 'success'
      snackbar.show = true
      rejectDialog.value = false
      emit('status-changed', 'rejected')
    } else {
      snackbar.message = result.error
      snackbar.color = 'error'
      snackbar.show = true
    }
  } finally {
    rejecting.value = false
  }
}

// Watch for example changes
watch(() => props.exampleId, async (newId) => {
  if (newId) {
    await fetchStatus()
  }
}, { immediate: true })

// Fetch status on mount
onMounted(() => {
  if (props.exampleId) {
    fetchStatus()
  }
})
</script>

<style scoped>
.review-notes {
  display: flex;
  align-items: center;
  padding: 0 8px;
}
</style>

