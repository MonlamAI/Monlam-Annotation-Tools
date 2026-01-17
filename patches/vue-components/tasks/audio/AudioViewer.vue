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
      // Show card for everyone if we have projectId and exampleId
      // Card may be empty for non-annotated examples, but it should always be visible
      return !!(this.projectId && this.exampleId)
    },
    
    statusText() {
      // If no data yet, show loading or default message
      if (!this.statusData) {
        if (this.isLoadingStatus) {
          return 'Loading...'
        }
        return 'Not annotated yet'
      }
      
      // For annotators: Show "Submitted" if they've submitted, otherwise show nothing
      if (this.userRole === 'annotator') {
        if (this.statusData && this.statusData.is_submitted) {
          return 'Submitted'
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
      
      // For unknown roles or when role is not set: Show basic status
      // Try to show submitted/approved info if available
      const parts = []
      if (this.submittedBy) {
        parts.push(`Submitted: ${this.submittedBy}`)
      }
      if (this.approvedBy) {
        parts.push(`Approved: ${this.approvedBy}`)
      }
      if (parts.length === 0) {
        return 'Not annotated yet'
      }
      return parts.join(' | ')
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
      
      let userData = null
      
      try {
        // First, check if user is superuser and get user info
        try {
          const userResp = await fetch('/v1/me')
          if (userResp.ok) {
            userData = await userResp.json()
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
            console.log('[AudioViewer] Set role to project_admin for superuser (from approval API)')
          }
          
          // If still no role, try to get from members API as fallback
          if (!this.userRole && userData) {
            try {
              const membersResp = await fetch(`/v1/projects/${this.projectId}/members/`)
              if (membersResp.ok) {
                const membersData = await membersResp.json()
                const currentUserMember = membersData.results?.find(m => m.username === userData.username)
                if (currentUserMember && currentUserMember.role) {
                  const roleName = currentUserMember.role.name?.toLowerCase() || ''
                  if (roleName.includes('admin') || roleName === 'project_admin') {
                    this.userRole = 'project_admin'
                  } else if (roleName.includes('approver') || roleName === 'annotation_approver') {
                    this.userRole = 'annotation_approver'
                  } else if (roleName.includes('manager') || roleName === 'project_manager') {
                    this.userRole = 'project_manager'
                  }
                  console.log('[AudioViewer] User role from members API (fallback):', this.userRole)
                }
              }
            } catch (e) {
              console.error('[AudioViewer] Error fetching members in approval success path:', e)
            }
          }
          
          console.log('[AudioViewer] Final user role:', this.userRole)
          
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
          
          // Try to determine user role from project members API
          try {
            const membersResp = await fetch(`/v1/projects/${this.projectId}/members/`)
            if (membersResp.ok) {
              const membersData = await membersResp.json()
              // Find current user in members list
              const currentUserMember = membersData.results?.find(m => m.username === userData?.username)
              if (currentUserMember && currentUserMember.role) {
                const roleName = currentUserMember.role.name?.toLowerCase() || ''
                // Map role names to our role constants
                if (roleName.includes('admin') || roleName === 'project_admin') {
                  this.userRole = 'project_admin'
                } else if (roleName.includes('approver') || roleName === 'annotation_approver') {
                  this.userRole = 'annotation_approver'
                } else if (roleName.includes('manager') || roleName === 'project_manager') {
                  this.userRole = 'project_manager'
                } else if (roleName.includes('annotator')) {
                  this.userRole = 'annotator'
                }
                console.log('[AudioViewer] User role from members API:', this.userRole)
              }
            }
          } catch (e) {
            console.error('[AudioViewer] Error fetching members:', e)
          }
          
          // If still no role and user is superuser, set as project_admin
          if (!this.userRole && this.isSuperuser) {
            this.userRole = 'project_admin'
            console.log('[AudioViewer] Set role to project_admin for superuser')
          }
          
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
