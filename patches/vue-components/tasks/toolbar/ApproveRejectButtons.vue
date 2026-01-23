<template>
  <div>
    <!-- Review Statistics Counter - Real-time project stats -->
    <v-card v-if="canApprove" class="mb-4" elevation="2" style="border: 2px solid #4CAF50; border-radius: 8px;">
      <v-card-title class="text-subtitle-1 font-weight-bold pa-3" style="background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%); color: white;">
        <v-icon left dark size="20">mdi-chart-box</v-icon>
        Project Review Statistics
      </v-card-title>
      <v-card-text class="pa-3">
        <div v-if="isLoadingStats" class="text-center py-2">
          <v-progress-circular indeterminate size="24" class="mr-2"></v-progress-circular>
          <span class="text-body-2">Loading statistics...</span>
        </div>
        <div v-else class="d-flex flex-wrap align-center">
          <v-chip
            color="success"
            text-color="white"
            class="mr-3 mb-2"
            style="font-size: 14px; height: 36px; padding: 0 16px; font-weight: 600;"
          >
            <v-icon left size="18">mdi-check-circle</v-icon>
            Approved: {{ reviewStats.approved_count || 0 }}
          </v-chip>
          <v-chip
            color="error"
            text-color="white"
            class="mr-3 mb-2"
            style="font-size: 14px; height: 36px; padding: 0 16px; font-weight: 600;"
          >
            <v-icon left size="18">mdi-close-circle</v-icon>
            Rejected: {{ reviewStats.rejected_count || 0 }}
          </v-chip>
          <v-chip
            color="info"
            text-color="white"
            class="mr-3 mb-2"
            style="font-size: 14px; height: 36px; padding: 0 16px; font-weight: 600;"
          >
            <v-icon left size="18">mdi-file-document</v-icon>
            Total: {{ reviewStats.total_examples || 0 }}
          </v-chip>
          <v-chip
            v-if="reviewStats.submitted_count !== undefined"
            color="warning"
            text-color="white"
            class="mb-2"
            style="font-size: 14px; height: 36px; padding: 0 16px; font-weight: 600;"
          >
            <v-icon left size="18">mdi-clock-outline</v-icon>
            Submitted: {{ reviewStats.submitted_count || 0 }}
          </v-chip>
        </div>
      </v-card-text>
    </v-card>

    <!-- Status Summary Card - Prominent display at the top -->
    <v-card class="mb-4" elevation="4" style="border: 2px solid #1976d2; border-radius: 8px;">
      <v-card-title class="text-h6 font-weight-bold pa-3" style="background: linear-gradient(135deg, #1976d2 0%, #1565c0 100%); color: white;">
        <v-icon left dark size="24">mdi-information</v-icon>
        Status Summary
      </v-card-title>
      <v-card-text class="pa-4">
        <div v-if="isLoadingStatus" class="text-center py-4">
          <v-progress-circular indeterminate size="32" class="mr-2"></v-progress-circular>
          <span class="text-body-1">Loading status...</span>
        </div>
        <div v-else>
          <!-- Submitted Status -->
          <div v-if="submittedBy" class="mb-3">
            <v-chip color="info" text-color="white" class="mr-3 mb-2" style="font-size: 14px; height: 32px; padding: 0 12px;">
              <v-icon left size="18">mdi-clock-outline</v-icon>
              Submitted
            </v-chip>
            <div class="mt-2">
              <span class="text-body-2">by <strong style="font-size: 15px;">{{ submittedBy }}</strong></span>
              <span v-if="annotatedAt" class="text-body-2 ml-3 text--secondary">
              at {{ formatDate(annotatedAt) }}
            </span>
            </div>
          </div>
          <div v-else-if="isSubmitted" class="mb-3">
            <v-chip color="info" text-color="white" class="mr-3 mb-2" style="font-size: 14px; height: 32px; padding: 0 12px;">
              <v-icon left size="18">mdi-clock-outline</v-icon>
              Submitted
            </v-chip>
            <div class="mt-2" v-if="annotatedAt">
              <span class="text-body-2 text--secondary">
              at {{ formatDate(annotatedAt) }}
            </span>
            </div>
          </div>
          
          <!-- Approved Status - Only show if status is actually approved/reviewed -->
          <div v-if="status === 'reviewed' || status === 'approved'">
            <!-- Show reviewedBy if available (from tracking API or approval chain fallback) -->
            <div v-if="reviewedBy" class="mb-3">
              <v-chip color="success" text-color="white" class="mr-3 mb-2" style="font-size: 14px; height: 32px; padding: 0 12px;">
                <v-icon left size="18">mdi-check-circle</v-icon>
                {{ status === 'reviewed' ? 'Reviewed' : 'Approved' }}
              </v-chip>
              <div class="mt-2">
                <span class="text-body-2">by <strong style="font-size: 15px;">{{ reviewedBy }}</strong></span>
                <span v-if="reviewedAt" class="text-body-2 ml-3 text--secondary">
                at {{ formatDate(reviewedAt) }}
              </span>
              </div>
            </div>
            <!-- Show approvedBy if available (from approval chain) and reviewedBy is not set -->
            <div v-else-if="approvedBy" class="mb-3">
              <v-chip color="success" text-color="white" class="mr-3 mb-2" style="font-size: 14px; height: 32px; padding: 0 12px;">
                <v-icon left size="18">mdi-check-circle</v-icon>
                {{ status === 'reviewed' ? 'Reviewed' : 'Approved' }}
              </v-chip>
              <div class="mt-2">
                <span class="text-body-2">by <strong style="font-size: 15px;">{{ approvedBy }}</strong></span>
                <span v-if="approvedAt" class="text-body-2 ml-3 text--secondary">
                  at {{ formatDate(approvedAt) }}
                </span>
                <span v-else-if="reviewedAt" class="text-body-2 ml-3 text--secondary">
                at {{ formatDate(reviewedAt) }}
              </span>
              </div>
            </div>
            <!-- Show project admin approval status if no specific reviewer info -->
            <div v-else-if="projectAdminApproved" class="mb-3">
              <v-chip color="success" text-color="white" class="mr-3 mb-2" style="font-size: 14px; height: 32px; padding: 0 12px;">
                <v-icon left size="18">mdi-check-circle</v-icon>
                {{ status === 'reviewed' ? 'Reviewed' : 'Final Approved' }}
              </v-chip>
              <div class="mt-2">
                <span class="text-body-2">by Project Admin</span>
              </div>
            </div>
            <!-- Show annotation approver approval status if no specific reviewer info -->
            <div v-else-if="annotationApproverApproved" class="mb-3">
              <v-chip color="success" text-color="white" class="mr-3 mb-2" style="font-size: 14px; height: 32px; padding: 0 12px;">
                <v-icon left size="18">mdi-check-circle</v-icon>
                {{ status === 'reviewed' ? 'Reviewed' : 'Approved' }}
              </v-chip>
              <div class="mt-2">
                <span class="text-body-2">by Annotation Approver</span>
              </div>
            </div>
            <!-- Fallback: show status without specific reviewer (should rarely happen) -->
            <div v-else class="mb-3">
              <v-chip color="success" text-color="white" class="mr-3 mb-2" style="font-size: 14px; height: 32px; padding: 0 12px;">
                <v-icon left size="18">mdi-check-circle</v-icon>
                {{ status === 'reviewed' ? 'Reviewed' : 'Approved' }}
              </v-chip>
              <div class="mt-2">
                <span class="text-body-2">by Reviewer</span>
              </div>
            </div>
          </div>
          
          <!-- Rejected Status -->
          <div v-if="status === 'rejected'">
            <!-- Show reviewedBy if available (from tracking API) -->
            <div v-if="reviewedBy" class="mb-3">
              <v-chip color="error" text-color="white" class="mr-3 mb-2" style="font-size: 14px; height: 32px; padding: 0 12px;">
                <v-icon left size="18">mdi-close-circle</v-icon>
                Rejected
              </v-chip>
              <div class="mt-2">
                <span class="text-body-2">by <strong style="font-size: 15px;">{{ reviewedBy }}</strong></span>
                <span v-if="reviewedAt" class="text-body-2 ml-3 text--secondary">
                  at {{ formatDate(reviewedAt) }}
                </span>
              </div>
            </div>
            <!-- Show rejectedBy if available (from approval chain) and reviewedBy is not set -->
            <div v-else-if="rejectedBy" class="mb-3">
              <v-chip color="error" text-color="white" class="mr-3 mb-2" style="font-size: 14px; height: 32px; padding: 0 12px;">
                <v-icon left size="18">mdi-close-circle</v-icon>
              Rejected
            </v-chip>
              <div class="mt-2">
                <span class="text-body-2">by <strong style="font-size: 15px;">{{ rejectedBy }}</strong></span>
                <span v-if="rejectedAt" class="text-body-2 ml-3 text--secondary">
                  at {{ formatDate(rejectedAt) }}
                </span>
                <span v-else-if="reviewedAt" class="text-body-2 ml-3 text--secondary">
              at {{ formatDate(reviewedAt) }}
            </span>
              </div>
            </div>
            <!-- Fallback: show rejection status without specific reviewer -->
            <div v-else class="mb-3">
              <v-chip color="error" text-color="white" class="mr-3 mb-2" style="font-size: 14px; height: 32px; padding: 0 12px;">
                <v-icon left size="18">mdi-close-circle</v-icon>
                Rejected
              </v-chip>
              <div class="mt-2">
                <span class="text-body-2">by Reviewer</span>
              </div>
            </div>
          </div>
          
          <!-- No Status -->
          <div v-if="!submittedBy && !approvedBy && !isSubmitted && !annotationApproverApproved && !projectAdminApproved && status !== 'reviewed' && status !== 'approved' && status !== 'rejected'">
            <v-chip color="grey" text-color="white" class="mb-2" style="font-size: 14px; height: 32px; padding: 0 12px;">
              <v-icon left size="18">mdi-information-outline</v-icon>
              Not submitted yet
            </v-chip>
          </div>
        </div>
      </v-card-text>
    </v-card>

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
        
        <div class="mb-3">
          <v-chip :color="statusColor" small class="mr-2">
            <v-icon small left>{{ statusIcon }}</v-icon>
            {{ status.toUpperCase() }}
          </v-chip>
          <!-- Show who did what and timestamps -->
          <div v-if="submittedBy || reviewedBy || annotatedAt || reviewedAt" class="mt-2">
            <div v-if="submittedBy && annotatedAt" class="text-caption text--secondary">
              <v-icon x-small>mdi-pencil</v-icon>
              Submitted by <strong>{{ submittedBy }}</strong> at {{ formatDate(annotatedAt) }}
            </div>
            <div v-else-if="annotatedAt" class="text-caption text--secondary">
              <v-icon x-small>mdi-pencil</v-icon>
              Submitted at {{ formatDate(annotatedAt) }}
            </div>
            <div v-if="reviewedBy && reviewedAt" class="text-caption text--secondary">
              <v-icon x-small>{{ status === 'rejected' ? 'mdi-close-circle' : 'mdi-check-circle' }}</v-icon>
              {{ status === 'rejected' ? 'Rejected' : 'Reviewed' }} by <strong>{{ reviewedBy }}</strong> at {{ formatDate(reviewedAt) }}
            </div>
            <div v-else-if="reviewedAt" class="text-caption text--secondary">
              <v-icon x-small>{{ status === 'rejected' ? 'mdi-close-circle' : 'mdi-check-circle' }}</v-icon>
              {{ status === 'rejected' ? 'Rejected' : 'Reviewed' }} at {{ formatDate(reviewedAt) }}
            </div>
          </div>
        </div>
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
      submittedBy: null,
      approvedBy: null,
      approvedAt: null,
      rejectedBy: null,
      rejectedAt: null,
      reviewedBy: null,
      annotatedAt: null,
      reviewedAt: null,
      isLoadingStatus: false,
      snackbar: false,
      snackbarText: '',
      snackbarColor: 'success',
      mdiCheckCircleOutline,
      mdiCloseCircleOutline,
      mdiClockOutline,
      mdiCheckCircle,
      mdiAlertCircle,
      // Review statistics
      reviewStats: {
        approved_count: 0,
        rejected_count: 0,
        total_examples: 0,
        submitted_count: 0,
        pending_count: 0
      },
      isLoadingStats: false,
      statsPollInterval: null
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
    // Validate exampleId
    if (!this.exampleId) {
      console.error('[Monlam Approve] exampleId is required but not provided')
      this.showSnackbar('⚠️ Example ID not found. Please reload the page.', 'warning')
      return
    }
    
    // Always fetch approval chain and status (visible to all users)
    this.isLoadingStatus = true
    // Fetch tracking API first to get primary data
    await this.fetchStatusSummary()
    // Then fetch approval chain and apply fallback if needed
    await this.fetchApprovalChain()
    // Apply fallback logic after both API calls complete
    this.applyApprovalChainFallback()
    await this.checkRole()
    if (this.canApprove) {
      await this.fetchStatus()
      // Apply fallback again after fetchStatus in case it overwrote something
      this.applyApprovalChainFallback()
      // Fetch review statistics and start polling
      await this.fetchReviewStats()
      this.startStatsPolling()
    }
    this.isLoadingStatus = false
  },

  beforeDestroy() {
    // Clean up polling interval
    if (this.statsPollInterval) {
      clearInterval(this.statsPollInterval)
      this.statsPollInterval = null
    }
  },

  watch: {
    async exampleId() {
      // Validate exampleId
      if (!this.exampleId) {
        return
      }
      
      // Always fetch approval chain and status (visible to all users)
      this.isLoadingStatus = true
      // Fetch tracking API first to get primary data
      await this.fetchStatusSummary()
      // Then fetch approval chain and apply fallback if needed
      await this.fetchApprovalChain()
      // Apply fallback logic after both API calls complete
      this.applyApprovalChainFallback()
      await this.checkRole()
      if (this.canApprove) {
        await this.fetchStatus()
        // Apply fallback again after fetchStatus in case it overwrote something
        this.applyApprovalChainFallback()
        // Refresh review statistics when example changes
        await this.fetchReviewStats()
      }
      this.isLoadingStatus = false
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
        if (!this.exampleId) {
          console.error('[Monlam Approve] Cannot fetch approval chain: exampleId is missing')
          return
        }
        
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
          
          // Extract approved/rejected by from approval chain
          // This will be used by applyApprovalChainFallback() method
          this.approvedBy = null // Reset first
          this.approvedAt = null // Reset timestamp
          this.rejectedBy = null // Reset first
          this.rejectedAt = null // Reset timestamp
          if (this.allApprovals && this.allApprovals.length > 0) {
            // Find the first annotation_approver who approved
            const approverApproval = this.allApprovals.find(
              ap => ap.approver_role === 'annotation_approver' && ap.status === 'approved'
            )
            if (approverApproval) {
              this.approvedBy = approverApproval.approver_username
              this.approvedAt = approverApproval.reviewed_at || null
            } else {
              // If no annotation approver, check for project admin approval
              const adminApproval = this.allApprovals.find(
                ap => ap.approver_role === 'project_admin' && ap.status === 'approved'
              )
              if (adminApproval) {
                this.approvedBy = adminApproval.approver_username
                this.approvedAt = adminApproval.reviewed_at || null
              }
            }
            
            // Find the first rejection (any role)
            const rejectionApproval = this.allApprovals.find(
              ap => ap.status === 'rejected'
            )
            if (rejectionApproval) {
              this.rejectedBy = rejectionApproval.approver_username
              this.rejectedAt = rejectionApproval.reviewed_at || null
            }
          }
          
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
        } else if (resp.status === 404) {
          // Example not found
          this.showSnackbar('⚠️ Example not found. Please ensure an example is loaded.', 'warning')
          this.allApprovals = []
        } else if (resp.status === 403) {
          // User doesn't have permission - silently fail
          // Approval chain just won't be displayed
          this.allApprovals = []
        }
      } catch (error) {
        console.error('[Monlam Approve] Error fetching approval chain:', error)
        // Don't show error to user, just don't display approval chain
        this.allApprovals = []
      }
    },

    applyApprovalChainFallback() {
      // Apply fallback logic: if reviewedBy is not set but we have approval chain data, use it
      if (!this.reviewedBy && this.allApprovals && this.allApprovals.length > 0) {
        // Priority: annotation_approver > project_admin > any other approver
        const approverApproval = this.allApprovals.find(
          ap => ap.approver_role === 'annotation_approver' && ap.status === 'approved'
        )
        if (approverApproval) {
          this.reviewedBy = approverApproval.approver_username
          this.reviewedAt = approverApproval.reviewed_at || this.reviewedAt
          return
        }
        
        const adminApproval = this.allApprovals.find(
          ap => ap.approver_role === 'project_admin' && ap.status === 'approved'
        )
        if (adminApproval) {
          this.reviewedBy = adminApproval.approver_username
          this.reviewedAt = adminApproval.reviewed_at || this.reviewedAt
          return
        }
        
        // Fallback: find ANY approval (for cases where status is 'reviewed' but no specific role)
        const anyApproval = this.allApprovals.find(
          ap => ap.status === 'approved'
        )
        if (anyApproval) {
          this.reviewedBy = anyApproval.approver_username
          this.reviewedAt = anyApproval.reviewed_at || this.reviewedAt
          return
        }
        
        // For rejections - set both reviewedBy (for display) and rejectedBy (for fallback)
        const rejectionApproval = this.allApprovals.find(
          ap => ap.status === 'rejected'
        )
        if (rejectionApproval) {
          // Set reviewedBy as primary (for consistent display)
          if (!this.reviewedBy) {
            this.reviewedBy = rejectionApproval.approver_username
            this.reviewedAt = rejectionApproval.reviewed_at || this.reviewedAt
          }
          // Also ensure rejectedBy is set (for fallback display)
          if (!this.rejectedBy) {
            this.rejectedBy = rejectionApproval.approver_username
            this.rejectedAt = rejectionApproval.reviewed_at || null
          }
        }
      }
    },

    async fetchStatusSummary() {
      // Fetch submitted by and timestamps from tracking API
      try {
        if (!this.exampleId) {
          console.error('[Monlam Approve] Cannot fetch status summary: exampleId is missing')
          return
        }
        
        const trackingResp = await fetch(
          `/v1/projects/${this.projectId}/tracking/${this.exampleId}/status/`
        )
        if (trackingResp.ok) {
          const trackingData = await trackingResp.json()
          // Get who submitted/confirmed (prefer annotated_by, fallback to confirmed_by)
          this.submittedBy = trackingData.annotated_by || trackingData.confirmed_by || null
          // Get who reviewed/approved - only overwrite if tracking API has a value
          // This preserves values set from approval chain fallback
          if (trackingData.reviewed_by) {
            this.reviewedBy = trackingData.reviewed_by
          }
          // Store timestamps for display - prefer tracking API timestamps
          if (trackingData.annotated_at) {
            this.annotatedAt = trackingData.annotated_at
          }
          if (trackingData.reviewed_at) {
            this.reviewedAt = trackingData.reviewed_at
          }
        }
      } catch (e) {
        console.error('[Monlam Approve] Error fetching tracking status:', e)
        // Don't show error, just leave submittedBy as null
      }
    },

    async fetchStatus() {
      try {
        if (!this.exampleId) {
          console.error('[Monlam Approve] Cannot fetch status: exampleId is missing')
          return
        }
        
        const resp = await fetch(
          `/v1/projects/${this.projectId}/tracking/${this.exampleId}/status/`
        )
        if (!resp.ok) {
          if (resp.status === 404) {
            this.showSnackbar('⚠️ Example not found. Please ensure an example is loaded.', 'warning')
          }
          return
        }
        
        const data = await resp.json()
        this.status = data.status || 'pending'
        // Also store timestamps and who did what for display
        // Only update if we have new data, preserve existing values from approval chain
        if (data.annotated_at) {
          this.annotatedAt = data.annotated_at
        }
        if (data.reviewed_at) {
          this.reviewedAt = data.reviewed_at
        }
        if (data.annotated_by || data.confirmed_by) {
        this.submittedBy = data.annotated_by || data.confirmed_by || this.submittedBy
        }
        // Only overwrite reviewedBy if tracking API has a value
        // This preserves values set from approval chain fallback
        if (data.reviewed_by) {
          this.reviewedBy = data.reviewed_by
        }
      } catch (error) {
        console.error('[Monlam Approve] Error fetching status:', error)
        this.showSnackbar('❌ Error loading status: ' + error.message, 'error')
      }
    },

    async handleApprove() {
      if (!this.exampleId) {
        this.showSnackbar('⚠️ Example ID not found. Please reload the page.', 'warning')
        return
      }
      
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
          // Refresh all data in correct order
          await this.fetchStatusSummary()
          await this.fetchApprovalChain()
          this.applyApprovalChainFallback()
          await this.fetchStatus()
          this.applyApprovalChainFallback()
          // Refresh review statistics after approval
          await this.fetchReviewStats()
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
      if (!this.exampleId) {
        this.showSnackbar('⚠️ Example ID not found. Please reload the page.', 'warning')
        return
      }
      
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
          // Refresh all data in correct order
          await this.fetchStatusSummary()
          await this.fetchApprovalChain()
          this.applyApprovalChainFallback()
          await this.fetchStatus()
          this.applyApprovalChainFallback()
          // Refresh review statistics after rejection
          await this.fetchReviewStats()
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
    },

    async fetchReviewStats() {
      // Fetch review statistics for the project
      try {
        this.isLoadingStats = true
        const resp = await fetch(
          `/v1/projects/${this.projectId}/tracking/review-stats/`
        )
        if (resp.ok) {
          const data = await resp.json()
          this.reviewStats = {
            approved_count: data.approved_count || 0,
            rejected_count: data.rejected_count || 0,
            total_examples: data.total_examples || 0,
            submitted_count: data.submitted_count || 0,
            pending_count: data.pending_count || 0
          }
        } else {
          console.error('[Monlam Approve] Error fetching review stats:', resp.status)
        }
      } catch (error) {
        console.error('[Monlam Approve] Error fetching review stats:', error)
        // Don't show error to user, just log it
      } finally {
        this.isLoadingStats = false
      }
    },

    startStatsPolling() {
      // Poll review statistics every 10 seconds for real-time updates
      // This ensures the counter updates even if other reviewers approve/reject examples
      if (this.statsPollInterval) {
        clearInterval(this.statsPollInterval)
      }
      
      this.statsPollInterval = setInterval(() => {
        if (this.canApprove && this.projectId) {
          this.fetchReviewStats()
        }
      }, 10000) // Poll every 10 seconds
    }
  }
})
</script>

