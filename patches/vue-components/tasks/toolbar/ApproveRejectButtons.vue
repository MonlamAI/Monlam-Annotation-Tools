<template>
  <v-card v-if="canApprove" class="mt-4 pa-4">
    <v-card-title class="text-subtitle-1 font-weight-bold">
      Review Actions
    </v-card-title>
    <v-card-text>
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
            :disabled="approving || rejecting"
            @click="handleApprove"
          >
            <v-icon left>{{ mdiCheckCircleOutline }}</v-icon>
            Approve
          </v-btn>
        </v-col>
        <v-col cols="6">
          <v-btn
            block
            color="error"
            :loading="rejecting"
            :disabled="approving || rejecting"
            @click="handleReject"
          >
            <v-icon left>{{ mdiCloseCircleOutline }}</v-icon>
            Reject
          </v-btn>
        </v-col>
      </v-row>
    </v-card-text>
  </v-card>
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
    await this.checkRole()
    if (this.canApprove) {
      await this.fetchStatus()
    }
  },

  watch: {
    exampleId() {
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
      } catch (error) {
        console.error('[Monlam Approve] Error checking role:', error)
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
      const notes = prompt('Approval notes (optional):')
      if (notes === null) return

      this.approving = true
      try {
        const resp = await fetch(
          `/v1/projects/${this.projectId}/tracking/${this.exampleId}/approve/`,
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'X-CSRFToken': this.getCsrfToken()
            },
            body: JSON.stringify({ review_notes: notes })
          }
        )

        if (resp.ok) {
          this.$emit('approved')
          await this.fetchStatus()
          alert('✅ Example approved successfully!')
        } else {
          const data = await resp.json()
          alert('❌ Error: ' + (data.error || 'Unknown error'))
        }
      } catch (error) {
        alert('❌ Network error: ' + error.message)
      } finally {
        this.approving = false
      }
    },

    async handleReject() {
      const notes = prompt('Rejection reason (required):')
      if (!notes) {
        alert('Rejection reason is required.')
        return
      }

      this.rejecting = true
      try {
        const resp = await fetch(
          `/v1/projects/${this.projectId}/tracking/${this.exampleId}/reject/`,
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'X-CSRFToken': this.getCsrfToken()
            },
            body: JSON.stringify({ review_notes: notes })
          }
        )

        if (resp.ok) {
          this.$emit('rejected')
          await this.fetchStatus()
          alert('✅ Example rejected. Annotator will see it again for revision.')
        } else {
          const data = await resp.json()
          alert('❌ Error: ' + (data.error || 'Unknown error'))
        }
      } catch (error) {
        alert('❌ Network error: ' + error.message)
      } finally {
        this.rejecting = false
      }
    },

    getCsrfToken() {
      const token = document.querySelector('[name=csrfmiddlewaretoken]')
      return token ? token.value : ''
    }
  }
})
</script>

