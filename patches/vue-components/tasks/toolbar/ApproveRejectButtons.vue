<template>
  <div>
    <!-- Approval Chain Display -->
    <v-card v-if="allApprovals && allApprovals.length > 0" class="mt-4">
      <v-card-title class="text-subtitle-1 font-weight-bold pa-3" style="background-color: #4CAF50; color: white;">
        <v-icon left dark>mdi-account-check</v-icon>
        Approval Chain
      </v-card-title>
      <v-card-text class="pa-3">
        <div v-for="(approval, index) in allApprovals" :key="index" class="mb-2">
          <v-chip
            :color="getApprovalStatusColor(approval.status)"
            dark
            small
            class="mb-1"
          >
            <v-icon small left>{{ getApprovalStatusIcon(approval.status) }}</v-icon>
            {{ getRoleLabel(approval.approver_role) }} - {{ approval.status.toUpperCase() }}
          </v-chip>
          <div class="text-caption">
            <strong>{{ approval.approver_username }}</strong>
            <span v-if="approval.reviewed_at"> - {{ formatDate(approval.reviewed_at) }}</span>
          </div>
          <div v-if="approval.review_notes" class="text-caption text--secondary mt-1" style="font-style: italic;">
            <v-icon x-small>mdi-note-text</v-icon>
            {{ approval.review_notes }}
          </div>
          <v-divider v-if="index < allApprovals.length - 1" class="mt-2"></v-divider>
        </div>
      </v-card-text>
    </v-card>

    <!-- Review Actions -->
    <v-card v-if="canApprove" class="mt-4 pa-4">
      <v-card-title class="text-subtitle-1 font-weight-bold">
        Review Actions
      </v-card-title>
      <v-card-text>
        <!-- Show message if annotation approver but example not submitted -->
        <v-alert
          v-if="userRole === 'annotation_approver' && !isSubmitted"
          type="info"
          text
          dense
          class="mb-3"
        >
          <strong>ℹ️ Waiting for Submission:</strong> This example must be submitted by an annotator before you can review it.
        </v-alert>
        
        <!-- Show message if project admin but approver hasn't approved yet -->
        <v-alert
          v-else-if="userRole === 'project_admin' && !annotationApproverApproved"
          type="info"
          text
          dense
          class="mb-3"
        >
          <strong>ℹ️ Waiting for Approver:</strong> This example must be approved by an annotation approver before you can review it.
        </v-alert>
        
        <!-- Show message if project admin can review (approver has approved) -->
        <v-alert
          v-else-if="annotationApproverApproved && userRole === 'project_admin'"
          type="warning"
          text
          dense
          class="mb-3"
        >
          <strong>⚠️ Second-Level Review:</strong> This annotation has been approved by an annotation approver. As a project admin, you can review and approve or reject it.
        </v-alert>
        
        <v-chip :color="statusColor" small class="mb-3">
          <v-icon small left>{{ statusIcon }}</v-icon>
          {{ status.toUpperCase() }}
        </v-chip>
        <v-row>
          <v-col cols="6">
            <v-btn
              block
              color="success"
              :loading="approving"
              :disabled="!canReviewNow || approving || rejecting || (currentUserApproval && currentUserApproval.status === 'approved')"
              @click="handleApprove"
            >
              <v-icon left>{{ mdiCheckCircleOutline }}</v-icon>
              {{ currentUserApproval && currentUserApproval.status === 'approved' ? 'Approved' : 'Approve' }}
            </v-btn>
          </v-col>
          <v-col cols="6">
            <v-btn
              block
              color="error"
              :loading="rejecting"
              :disabled="!canReviewNow || approving || rejecting || (currentUserApproval && currentUserApproval.status === 'rejected')"
              @click="handleReject"
            >
              <v-icon left>{{ mdiCloseCircleOutline }}</v-icon>
              {{ currentUserApproval && currentUserApproval.status === 'rejected' ? 'Rejected' : 'Reject' }}
            </v-btn>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <!-- Snackbar for notifications -->
    <v-snackbar
      v-model="snackbar"
      :color="snackbarColor"
      :timeout="3000"
      top
    >
      {{ snackbarText }}
      <template v-slot:action="{ attrs }">
        <v-btn
          text
          v-bind="attrs"
          @click="snackbar = false"
        >
          Close
        </v-btn>
      </template>
    </v-snackbar>
  </div>
</template>

<script>
import Vue from 'vue'
import {
  mdiCheckCircleOutline,
  mdiCloseCircleOutline,
  mdiClockOutline,
  mdiCheckCircle,
  mdiAlertCircle
} from '@mdi/js'

export default Vue.extend({
  props: {
    projectId: {
      type: String,
      required: true
    },
    exampleId: {
      type: Number,
      required: true
    }
  },

  data() {
    return {
      canApprove: false,
      status: 'pending',
      approving: false,
      rejecting: false,
      allApprovals: [],
      annotationApproverApproved: false,
      projectAdminApproved: false,
      currentUserApproval: null,
      userRole: null,
      canReviewNow: false,
      isSubmitted: false,
      snackbar: false,
      snackbarText: '',
      snackbarColor: 'success',
      mdiCheckCircleOutline,
      mdiCloseCircleOutline,
      mdiClockOutline,
      mdiCheckCircle,
      mdiAlertCircle
    }
  },

  computed: {
    statusColor() {
      const colors = {
        pending: 'grey',
        in_progress: 'blue',
        submitted: 'orange',
        approved: 'success',
        rejected: 'error'
      }
      return colors[this.status] || 'grey'
    },
    statusIcon() {
      const icons = {
        pending: this.mdiClockOutline,
        in_progress: this.mdiClockOutline,
        submitted: this.mdiClockOutline,
        approved: this.mdiCheckCircle,
        rejected: this.mdiAlertCircle
      }
      return icons[this.status] || this.mdiClockOutline
    }
  },

  async mounted() {
    // Always fetch approval chain (visible to all users)
    await this.fetchApprovalChain()
    await this.checkRole()
    if (this.canApprove) {
      await this.fetchStatus()
    }
  },

  watch: {
    exampleId() {
      this.fetchApprovalChain()
      if (this.canApprove) {
        this.fetchStatus()
      }
    }
  },

  methods: {
    async checkRole() {
      try {
        const userResp = await fetch('/v1/me')
        const user = await userResp.json()

        const membersResp = await fetch(`/v1/projects/${this.projectId}/members`)
        const membersData = await membersResp.json()
        const members = membersData.results || []

        const currentMember = members.find((m) => m.user === user.id)
        if (!currentMember) return

        const roleResp = await fetch(`/v1/roles/${currentMember.role}`)
        const roleData = await roleResp.json()

        const allowedRoles = ['annotation_approver', 'project_manager', 'project_admin']
        this.canApprove = allowedRoles.includes(roleData.name)
        this.userRole = roleData.name
      } catch (error) {
        console.error('[Monlam Approve] Error checking role:', error)
      }
    },

    async fetchApprovalChain() {
      try {
        const resp = await fetch(
          `/v1/projects/${this.projectId}/assignments/approver-completion/${this.exampleId}/`
        )
        if (resp.ok) {
          const data = await resp.json()
          this.allApprovals = data.all_approvals || []
          this.annotationApproverApproved = data.annotation_approver_approved || false
          this.projectAdminApproved = data.project_admin_approved || false
          this.canReviewNow = data.can_review_now || false
          this.isSubmitted = data.is_submitted || false
          this.userRole = data.user_role || null
          
          // Find current user's approval
          try {
            const currentUserResp = await fetch('/v1/me')
            if (currentUserResp.ok) {
              const currentUser = await currentUserResp.json()
              this.currentUserApproval = this.allApprovals.find(
                (ap) => ap.approver_id === currentUser.id
              ) || null
            }
          } catch (userError) {
            console.error('[Monlam Approve] Error fetching current user:', userError)
          }
        } else if (resp.status === 403 || resp.status === 404) {
          // User doesn't have permission or endpoint doesn't exist - silently fail
          // Approval chain just won't be displayed
          this.allApprovals = []
        }
      } catch (error) {
        console.error('[Monlam Approve] Error fetching approval chain:', error)
        // Don't show error to user, just don't display approval chain
        this.allApprovals = []
      }
    },

    async fetchStatus() {
      try {
        const resp = await fetch(
          `/v1/projects/${this.projectId}/tracking/${this.exampleId}/status/`
        )
        const data = await resp.json()
        this.status = data.status || 'pending'
      } catch (error) {
        console.error('[Monlam Approve] Error fetching status:', error)
      }
    },

    async handleApprove() {
      this.approving = true
      try {
        const resp = await fetch(
          `/v1/projects/${this.projectId}/assignments/approver-completion/${this.exampleId}/approve/`,
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'X-CSRFToken': this.getCsrfToken()
            },
            body: JSON.stringify({ notes: '' })
          }
        )

        if (resp.ok) {
          this.$emit('approved')
          await this.fetchApprovalChain()
          await this.fetchStatus()
          this.showSnackbar('✅ Example approved successfully!', 'success')
        } else {
          const data = await resp.json()
          const errorMsg = data.error || data.detail || 'Unknown error'
          // Show specific message based on error type
          if (data.requires_approver_approval) {
            this.showSnackbar('⚠️ ' + errorMsg, 'warning')
          } else if (data.requires_submission) {
            this.showSnackbar('⚠️ ' + errorMsg, 'warning')
          } else {
            this.showSnackbar('❌ Error: ' + errorMsg, 'error')
          }
        }
      } catch (error) {
        this.showSnackbar('❌ Network error: ' + error.message, 'error')
      } finally {
        this.approving = false
      }
    },

    async handleReject() {
      this.rejecting = true
      try {
        const resp = await fetch(
          `/v1/projects/${this.projectId}/assignments/approver-completion/${this.exampleId}/reject/`,
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'X-CSRFToken': this.getCsrfToken()
            },
            body: JSON.stringify({ notes: '' })
          }
        )

        if (resp.ok) {
          this.$emit('rejected')
          await this.fetchApprovalChain()
          await this.fetchStatus()
          this.showSnackbar('✅ Example rejected. Annotator will see it again for revision.', 'warning')
        } else {
          const data = await resp.json()
          const errorMsg = data.error || data.detail || 'Unknown error'
          // Show specific message based on error type
          if (data.requires_approver_approval) {
            this.showSnackbar('⚠️ ' + errorMsg, 'warning')
          } else if (data.requires_submission) {
            this.showSnackbar('⚠️ ' + errorMsg, 'warning')
          } else {
            this.showSnackbar('❌ Error: ' + errorMsg, 'error')
          }
        }
      } catch (error) {
        this.showSnackbar('❌ Network error: ' + error.message, 'error')
      } finally {
        this.rejecting = false
      }
    },

    showSnackbar(text, color = 'success') {
      this.snackbarText = text
      this.snackbarColor = color
      this.snackbar = true
    },

    getApprovalStatusColor(status) {
      if (status === 'approved') return 'success'
      if (status === 'rejected') return 'error'
      return 'grey'
    },

    getApprovalStatusIcon(status) {
      if (status === 'approved') return this.mdiCheckCircle
      if (status === 'rejected') return this.mdiAlertCircle
      return this.mdiClockOutline
    },

    getRoleLabel(role) {
      if (role === 'project_admin') return '👑 Admin'
      if (role === 'annotation_approver') return '✓ Approver'
      return 'Reviewer'
    },

    formatDate(dateString) {
      if (!dateString) return ''
      const date = new Date(dateString)
      return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    },

    getCsrfToken() {
      const token = document.querySelector('[name=csrfmiddlewaretoken]')
      return token ? token.value : ''
    }
  }
})
</script>

