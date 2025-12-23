<template>
  <v-container fluid>
    <v-card>
      <v-card-title>
        <v-icon left color="orange">mdi-clipboard-check</v-icon>
        Review Queue
        <v-spacer />
        <v-chip color="orange" dark>
          {{ items.length }} Pending Review
        </v-chip>
      </v-card-title>

      <v-card-text v-if="loading">
        <v-skeleton-loader type="list-item-avatar-three-line@3" />
      </v-card-text>

      <v-card-text v-else-if="items.length === 0">
        <v-alert type="success" outlined>
          <v-icon left>mdi-check-circle</v-icon>
          All caught up! No items pending review.
        </v-alert>
      </v-card-text>

      <v-list v-else three-line>
        <template v-for="(item, index) in items">
          <v-list-item :key="item.id">
            <!-- Audio Player -->
            <v-list-item-avatar size="80" tile>
              <audio 
                :src="item.filename" 
                controls 
                style="width: 200px; height: 40px;"
              />
            </v-list-item-avatar>

            <!-- Content -->
            <v-list-item-content>
              <v-list-item-title class="tibetan-text">
                {{ item.text || '(No transcript)' }}
              </v-list-item-title>
              <v-list-item-subtitle>
                <v-chip x-small outlined class="mr-2">
                  <v-icon x-small left>mdi-account</v-icon>
                  {{ item.assigned_to || 'Unknown' }}
                </v-chip>
                <v-chip x-small outlined>
                  ID: {{ item.id }}
                </v-chip>
              </v-list-item-subtitle>
            </v-list-item-content>

            <!-- Actions -->
            <v-list-item-action>
              <div class="d-flex flex-column">
                <v-btn
                  color="success"
                  small
                  class="mb-2"
                  :loading="reviewingId === item.id"
                  @click="review(item.id, 'approve')"
                >
                  <v-icon left small>mdi-check</v-icon>
                  Approve
                </v-btn>
                <v-btn
                  color="error"
                  small
                  outlined
                  :loading="reviewingId === item.id"
                  @click="openRejectDialog(item)"
                >
                  <v-icon left small>mdi-close</v-icon>
                  Reject
                </v-btn>
              </div>
            </v-list-item-action>
          </v-list-item>

          <v-divider v-if="index < items.length - 1" :key="'d-' + item.id" />
        </template>
      </v-list>

      <!-- Bulk Actions -->
      <v-card-actions v-if="items.length > 0">
        <v-spacer />
        <v-btn
          color="success"
          :loading="bulkApproving"
          @click="bulkApprove"
        >
          <v-icon left>mdi-check-all</v-icon>
          Approve All ({{ items.length }})
        </v-btn>
      </v-card-actions>
    </v-card>

    <!-- Reject Dialog -->
    <v-dialog v-model="rejectDialog" max-width="500">
      <v-card>
        <v-card-title>Reject Annotation</v-card-title>
        <v-card-text>
          <p>Please provide feedback for the annotator:</p>
          <v-textarea
            v-model="rejectNotes"
            label="Feedback / Notes"
            outlined
            rows="3"
            placeholder="What needs to be fixed..."
          />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn text @click="rejectDialog = false">Cancel</v-btn>
          <v-btn
            color="error"
            :loading="reviewingId === rejectItem?.id"
            @click="confirmReject"
          >
            Reject
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Snackbar -->
    <v-snackbar v-model="snackbar.show" :color="snackbar.color" timeout="3000">
      {{ snackbar.message }}
    </v-snackbar>
  </v-container>
</template>

<script>
export default {
  name: 'ReviewQueue',

  props: {
    projectId: {
      type: Number,
      required: true
    }
  },

  data() {
    return {
      items: [],
      loading: true,
      reviewingId: null,
      bulkApproving: false,
      rejectDialog: false,
      rejectItem: null,
      rejectNotes: '',
      snackbar: {
        show: false,
        message: '',
        color: 'success'
      }
    }
  },

  async mounted() {
    await this.loadQueue()
  },

  methods: {
    async loadQueue() {
      this.loading = true
      try {
        const response = await this.$axios.$get(
          `/projects/${this.projectId}/examples/review-queue/`
        )
        this.items = response
      } catch (error) {
        console.error('Failed to load review queue:', error)
      } finally {
        this.loading = false
      }
    },

    async review(exampleId, action, notes = '') {
      this.reviewingId = exampleId
      try {
        await this.$axios.$post(
          `/projects/${this.projectId}/examples/${exampleId}/review/`,
          { action, notes }
        )
        
        // Remove from list
        this.items = this.items.filter(i => i.id !== exampleId)
        
        this.showSnackbar(
          action === 'approve' ? 'Approved!' : 'Rejected',
          action === 'approve' ? 'success' : 'warning'
        )
      } catch (error) {
        this.showSnackbar('Failed to submit review', 'error')
      } finally {
        this.reviewingId = null
      }
    },

    openRejectDialog(item) {
      this.rejectItem = item
      this.rejectNotes = ''
      this.rejectDialog = true
    },

    async confirmReject() {
      if (!this.rejectItem) return
      await this.review(this.rejectItem.id, 'reject', this.rejectNotes)
      this.rejectDialog = false
      this.rejectItem = null
    },

    async bulkApprove() {
      this.bulkApproving = true
      try {
        for (const item of this.items) {
          await this.$axios.$post(
            `/projects/${this.projectId}/examples/${item.id}/review/`,
            { action: 'approve' }
          )
        }
        this.items = []
        this.showSnackbar('All items approved!', 'success')
      } catch (error) {
        this.showSnackbar('Failed to approve some items', 'error')
        await this.loadQueue()
      } finally {
        this.bulkApproving = false
      }
    },

    showSnackbar(message, color) {
      this.snackbar = { show: true, message, color }
    }
  }
}
</script>

<style scoped>
.tibetan-text {
  font-family: 'MonlamTBslim', 'Noto Sans Tibetan', sans-serif;
  font-size: 1.2em;
  line-height: 1.8;
}
</style>

