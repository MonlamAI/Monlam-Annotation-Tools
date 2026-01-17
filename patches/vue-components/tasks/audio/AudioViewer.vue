<template>
  <div>
    <div id="waveform" />
    <v-row no-gutters align="center" class="mb-3 mt-1">
      <v-col md="8">
        <v-slider
          v-model="zoom"
          min="0"
          max="500"
          step="10"
          :append-icon="mdiMagnifyPlusOutline"
          :prepend-icon="mdiMagnifyMinusOutline"
          hide-details
          @click:append="zoomIn"
          @click:prepend="zoomOut"
          @change="onChangeZoom"
        />
      </v-col>
      <v-col md="2">
        <v-slider
          v-model="volume"
          min="0"
          max="1"
          step="0.1"
          :append-icon="mdiVolumeHigh"
          hide-details
          @change="onChangeVolume"
        />
      </v-col>
      <v-col md="2">
        <v-select
          v-model="speed"
          :items="speeds"
          label="Speed"
          dense
          outlined
          hide-details
          @change="onChangeSpeed"
        />
      </v-col>
    </v-row>
    <div class="d-flex align-center flex-wrap" style="gap: 12px;">
      <v-btn color="primary" class="text-capitalize" @click="play">
        <v-icon v-if="!isPlaying" left>
          {{ mdiPlayCircleOutline }}
        </v-icon>
        <v-icon v-else left>
          {{ mdiPauseCircleOutline }}
        </v-icon>
        <span v-if="!isPlaying">Play</span>
        <span v-else>Pause</span>
      </v-btn>
      
      <!-- Status Card -->
      <v-chip
        v-if="projectId && exampleId && showStatusCard"
        :color="statusCardColor || 'grey'"
        text-color="white"
        small
        outlined
        class="status-chip"
        style="max-width: 300px;"
      >
        <v-icon left small>{{ statusIcon || 'mdi-information-outline' }}</v-icon>
        <span class="status-text">{{ statusText || (isLoadingStatus ? 'Loading...' : 'Not submitted yet') }}</span>
      </v-chip>
    </div>
    <v-checkbox
      v-model="autoLoop"
      label="Auto Loop"
      class="mt-2"
      hide-details
      dense
    />
  </div>
</template>

<script>
import Vue from 'vue'
import WaveSurfer from 'wavesurfer.js'
import {
  mdiPlayCircleOutline,
  mdiPauseCircleOutline,
  mdiVolumeHigh,
  mdiMagnifyPlusOutline,
  mdiMagnifyMinusOutline
} from '@mdi/js'

export default Vue.extend({
  props: {
    source: {
      type: String,
      default: '',
      required: true
    },
    projectId: {
      type: [String, Number],
      default: null
    },
    exampleId: {
      type: [String, Number],
      default: null
    }
  },

  data() {
    return {
      wavesurfer: null,
      isPlaying: false,
      zoom: 0,
      volume: 0.6,
      speed: 1,
      speeds: [0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0],
      autoLoop: false,
      mdiPlayCircleOutline,
      mdiPauseCircleOutline,
      mdiVolumeHigh,
      mdiMagnifyPlusOutline,
      mdiMagnifyMinusOutline,
      // Status card data
      statusData: null,
      userRole: null,
      isSuperuser: false,
      submittedBy: null,
      approvedBy: null,
      isLoadingStatus: false
    }
  },

  computed: {
    showStatusCard() {
      // Show card if we have projectId and exampleId
      if (!this.projectId || !this.exampleId) return false
      
      // Superusers should always see the card (like project admins)
      if (this.isSuperuser) {
        return true
      }
      
      // For annotators: Only show if submitted
      if (this.userRole === 'annotator') {
        return this.statusData && this.statusData.is_submitted
      }
      
      // For approvers and admins: Always show (even if no data yet or still loading)
      if (this.userRole === 'annotation_approver' || 
          this.userRole === 'project_admin' || 
          this.userRole === 'project_manager') {
        return true
      }
      
      // If we're still loading and don't know the role yet, show the card
      // (it will update once we get the role)
      if (this.isLoadingStatus) {
        return true
      }
      
      // For unknown roles, show if we have data or if we have submittedBy/approvedBy
      return !!this.statusData || !!this.submittedBy || !!this.approvedBy
    },
    
    statusText() {
      // For annotators: Only show "Submitted" if they've submitted
      if (this.userRole === 'annotator') {
        if (this.statusData && this.statusData.is_submitted) {
          return 'Submitted'
        }
        return '' // Empty for annotators who haven't submitted
      }
      
      // If no data yet, show loading or default message
      if (!this.statusData) {
        if (this.isLoadingStatus) {
          return 'Loading...'
        }
        return 'Not submitted yet'
      }
      
      // For superusers: Show who submitted AND who approved (like project admin)
      if (this.isSuperuser) {
        const parts = []
        if (this.submittedBy) {
          parts.push(`Submitted: ${this.submittedBy}`)
        }
        if (this.approvedBy) {
          parts.push(`Approved: ${this.approvedBy}`)
        }
        if (parts.length === 0) {
          return 'Not submitted yet'
        }
        return parts.join(' | ')
      }
      
      // For annotation approvers: Show who submitted
      if (this.userRole === 'annotation_approver') {
        if (this.submittedBy) {
          return `Submitted by: ${this.submittedBy}`
        }
        return 'Not submitted yet'
      }
      
      // For project admins: Show who submitted AND who approved
      if (this.userRole === 'project_admin') {
        const parts = []
        if (this.submittedBy) {
          parts.push(`Submitted: ${this.submittedBy}`)
        }
        if (this.approvedBy) {
          parts.push(`Approved: ${this.approvedBy}`)
        }
        if (parts.length === 0) {
          return 'Not submitted yet'
        }
        return parts.join(' | ')
      }
      
      // For project managers: Same as admin
      if (this.userRole === 'project_manager') {
        const parts = []
        if (this.submittedBy) {
          parts.push(`Submitted: ${this.submittedBy}`)
        }
        if (this.approvedBy) {
          parts.push(`Approved: ${this.approvedBy}`)
        }
        if (parts.length === 0) {
          return 'Not submitted yet'
        }
        return parts.join(' | ')
      }
      
      return ''
    },
    
    statusIcon() {
      if (!this.statusData) return 'mdi-information-outline'
      
      if (this.approvedBy) {
        return 'mdi-check-circle'
      }
      if (this.submittedBy) {
        return 'mdi-clock-outline'
      }
      return 'mdi-information-outline'
    },
    
    statusCardColor() {
      if (!this.statusData) return 'grey'
      
      if (this.approvedBy) {
        return 'success'
      }
      if (this.submittedBy) {
        return 'info'
      }
      return 'grey'
    }
  },

  watch: {
    source() {
      this.load()
      this.isPlaying = false
    },
    exampleId() {
      if (this.projectId && this.exampleId) {
        this.fetchStatusData()
      }
    },
    projectId() {
      if (this.projectId && this.exampleId) {
        this.fetchStatusData()
      }
    }
  },

  mounted() {
    this.wavesurfer = WaveSurfer.create({
      container: '#waveform',
      backend: 'MediaElement'
    })
    this.load()
    
    // Add event listener for when audio finishes
    this.wavesurfer.on('finish', () => {
      this.isPlaying = false
      if (this.autoLoop) {
        // Restart from beginning
        this.wavesurfer.seekTo(0)
        this.wavesurfer.play()
        this.isPlaying = true
      }
    })
    
    // Add event listener for play/pause state
    this.wavesurfer.on('pause', () => {
      this.isPlaying = false
    })
    this.wavesurfer.on('play', () => {
      this.isPlaying = true
    })
    
    // Fetch status data if projectId and exampleId are provided
    if (this.projectId && this.exampleId) {
      this.fetchStatusData()
    }
  },

  methods: {
    load() {
      this.wavesurfer.load(this.source)
    },
    play() {
      this.isPlaying = !this.isPlaying
      this.wavesurfer.playPause()
    },
    zoomOut() {
      this.zoom = this.zoom - 10 || 0
      this.onChangeZoom(this.zoom)
    },
    zoomIn() {
      this.zoom = this.zoom + 10 || 500
      this.onChangeZoom(this.zoom)
    },
    onChangeVolume(value) {
      this.wavesurfer.setVolume(value)
    },
    onChangeZoom(value) {
      this.wavesurfer.zoom(value)
    },
    onChangeSpeed(value) {
      this.wavesurfer.setPlaybackRate(value)
    },
    
    async fetchStatusData() {
      if (!this.projectId || !this.exampleId) {
        console.log('[AudioViewer] Missing projectId or exampleId:', { projectId: this.projectId, exampleId: this.exampleId })
        return
      }
      
      console.log('[AudioViewer] Fetching status data for:', { projectId: this.projectId, exampleId: this.exampleId })
      this.isLoadingStatus = true
      
      try {
        // First, check if user is superuser
        try {
          const userResp = await fetch('/v1/me')
          if (userResp.ok) {
            const userData = await userResp.json()
            this.isSuperuser = userData.is_superuser || false
            console.log('[AudioViewer] Is superuser:', this.isSuperuser)
          }
        } catch (e) {
          console.error('[AudioViewer] Error fetching user info:', e)
        }
        
        // Fetch approval status
        const approvalResp = await fetch(
          `/v1/projects/${this.projectId}/assignments/approver-completion/${this.exampleId}/`
        )
        
        console.log('[AudioViewer] Approval API response:', approvalResp.status, approvalResp.ok)
        
        if (approvalResp.ok) {
          const approvalData = await approvalResp.json()
          console.log('[AudioViewer] Approval data:', approvalData)
          this.statusData = approvalData
          this.userRole = approvalData.user_role || null
          // If superuser and no role, treat as project_admin
          if (this.isSuperuser && !this.userRole) {
            this.userRole = 'project_admin'
          }
          console.log('[AudioViewer] User role:', this.userRole)
          
          // Extract submitted by from tracking API
          try {
            const trackingResp = await fetch(
              `/v1/projects/${this.projectId}/tracking/${this.exampleId}/status/`
            )
            if (trackingResp.ok) {
              const trackingData = await trackingResp.json()
              this.submittedBy = trackingData.annotated_by || null
            }
          } catch (e) {
            console.error('[AudioViewer] Error fetching tracking status:', e)
          }
          
          // Extract approved by from approval chain
          if (approvalData.all_approvals && approvalData.all_approvals.length > 0) {
            // Find the first annotation_approver who approved
            const approverApproval = approvalData.all_approvals.find(
              ap => ap.approver_role === 'annotation_approver' && ap.status === 'approved'
            )
            if (approverApproval) {
              this.approvedBy = approverApproval.approver_username
            }
          }
        } else if (approvalResp.status === 403 || approvalResp.status === 404) {
          // User doesn't have permission or endpoint doesn't exist
          // Still set statusData to empty object so card can show "Not submitted yet"
          this.statusData = { is_submitted: false }
          // Try to get user role from tracking API
          try {
            const trackingResp = await fetch(
              `/v1/projects/${this.projectId}/tracking/${this.exampleId}/status/`
            )
            if (trackingResp.ok) {
              const trackingData = await trackingResp.json()
              this.submittedBy = trackingData.annotated_by || null
              if (this.submittedBy) {
                this.statusData.is_submitted = true
              }
            }
          } catch (e) {
            console.error('[AudioViewer] Error fetching tracking status:', e)
          }
        }
      } catch (error) {
        console.error('[AudioViewer] Error fetching status:', error)
        // Set empty status data so card can still show "Not submitted yet"
        this.statusData = { is_submitted: false }
      } finally {
        this.isLoadingStatus = false
        console.log('[AudioViewer] Final state:', {
          showStatusCard: this.showStatusCard,
          statusText: this.statusText,
          userRole: this.userRole,
          statusData: this.statusData
        })
      }
    }
  }
})
</script>

<style scoped>
.status-chip {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.status-text {
  display: inline-block;
  max-width: 250px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
@media (max-width: 600px) {
  .status-chip {
    max-width: 200px;
  }
  .status-text {
    max-width: 150px;
  }
}
</style>
