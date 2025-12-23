<template>
  <v-card class="assignment-panel">
    <v-card-title class="headline">
      <v-icon left>mdi-account-multiple</v-icon>
      Task Assignment
    </v-card-title>

    <v-card-text>
      <!-- Stats -->
      <v-row class="mb-4">
        <v-col cols="3">
          <v-card outlined class="text-center pa-2">
            <div class="text-h4">{{ stats.total }}</div>
            <div class="caption">Total</div>
          </v-card>
        </v-col>
        <v-col cols="3">
          <v-card outlined class="text-center pa-2" color="grey lighten-3">
            <div class="text-h4">{{ stats.unassigned }}</div>
            <div class="caption">Unassigned</div>
          </v-card>
        </v-col>
        <v-col cols="3">
          <v-card outlined class="text-center pa-2" color="blue lighten-4">
            <div class="text-h4">{{ stats.assigned }}</div>
            <div class="caption">Assigned</div>
          </v-card>
        </v-col>
        <v-col cols="3">
          <v-card outlined class="text-center pa-2" color="green lighten-4">
            <div class="text-h4">{{ stats.completed }}</div>
            <div class="caption">Completed</div>
          </v-card>
        </v-col>
      </v-row>

      <!-- Auto-assign section -->
      <v-divider class="my-4" />
      <h3>Auto-Assign Tasks</h3>
      <p class="caption">Distribute unassigned items evenly among selected annotators.</p>

      <v-select
        v-model="selectedAnnotators"
        :items="annotators"
        item-text="username"
        item-value="id"
        label="Select Annotators"
        multiple
        chips
        deletable-chips
        outlined
        dense
      />

      <v-btn
        color="primary"
        :disabled="selectedAnnotators.length === 0 || stats.unassigned === 0"
        :loading="assigning"
        @click="autoAssign"
      >
        <v-icon left>mdi-auto-fix</v-icon>
        Auto-Assign {{ stats.unassigned }} Items
      </v-btn>

      <!-- Manual assignment section -->
      <v-divider class="my-4" />
      <h3>Manual Assignment</h3>
      <p class="caption">Select items in the dataset table, then assign to a user.</p>

      <v-row>
        <v-col cols="8">
          <v-select
            v-model="assignTo"
            :items="annotators"
            item-text="username"
            item-value="id"
            label="Assign to"
            outlined
            dense
            clearable
          />
        </v-col>
        <v-col cols="4">
          <v-btn
            color="secondary"
            :disabled="selectedItems.length === 0"
            :loading="assigning"
            @click="manualAssign"
            block
          >
            Assign {{ selectedItems.length }} Items
          </v-btn>
        </v-col>
      </v-row>

      <!-- Assignment table -->
      <v-divider class="my-4" />
      <h3>Current Assignments</h3>

      <v-simple-table dense>
        <thead>
          <tr>
            <th>Annotator</th>
            <th>Assigned</th>
            <th>In Progress</th>
            <th>Submitted</th>
            <th>Approved</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in assignmentSummary" :key="user.id">
            <td>{{ user.username }}</td>
            <td>{{ user.assigned }}</td>
            <td>{{ user.in_progress }}</td>
            <td>{{ user.submitted }}</td>
            <td>{{ user.approved }}</td>
          </tr>
        </tbody>
      </v-simple-table>
    </v-card-text>

    <!-- Snackbar for feedback -->
    <v-snackbar v-model="snackbar.show" :color="snackbar.color" timeout="3000">
      {{ snackbar.message }}
    </v-snackbar>
  </v-card>
</template>

<script>
export default {
  name: 'AssignmentPanel',
  
  props: {
    projectId: {
      type: Number,
      required: true
    },
    selectedItems: {
      type: Array,
      default: () => []
    }
  },

  data() {
    return {
      annotators: [],
      selectedAnnotators: [],
      assignTo: null,
      assigning: false,
      stats: {
        total: 0,
        unassigned: 0,
        assigned: 0,
        completed: 0
      },
      assignmentSummary: [],
      snackbar: {
        show: false,
        message: '',
        color: 'success'
      }
    }
  },

  async mounted() {
    await this.loadAnnotators()
    await this.loadStats()
  },

  methods: {
    async loadAnnotators() {
      try {
        const response = await this.$axios.$get(
          `/projects/${this.projectId}/members/`
        )
        this.annotators = response.filter(m => 
          m.role.name.toLowerCase() === 'annotator'
        )
      } catch (error) {
        console.error('Failed to load annotators:', error)
      }
    },

    async loadStats() {
      try {
        const response = await this.$axios.$get(
          `/projects/${this.projectId}/examples/assignment-stats/`
        )
        this.stats = response.stats
        this.assignmentSummary = response.by_user
      } catch (error) {
        console.error('Failed to load stats:', error)
      }
    },

    async autoAssign() {
      this.assigning = true
      try {
        const response = await this.$axios.$post(
          `/projects/${this.projectId}/examples/auto-assign/`,
          { user_ids: this.selectedAnnotators }
        )
        this.showSnackbar(`Assigned ${response.assigned} items`, 'success')
        await this.loadStats()
        this.$emit('assigned')
      } catch (error) {
        this.showSnackbar('Failed to assign', 'error')
      } finally {
        this.assigning = false
      }
    },

    async manualAssign() {
      if (this.selectedItems.length === 0) return
      
      this.assigning = true
      try {
        const response = await this.$axios.$post(
          `/projects/${this.projectId}/examples/assign/`,
          {
            example_ids: this.selectedItems,
            user_id: this.assignTo
          }
        )
        this.showSnackbar(`Assigned ${response.assigned} items`, 'success')
        await this.loadStats()
        this.$emit('assigned')
      } catch (error) {
        this.showSnackbar('Failed to assign', 'error')
      } finally {
        this.assigning = false
      }
    },

    showSnackbar(message, color) {
      this.snackbar = { show: true, message, color }
    }
  }
}
</script>

<style scoped>
.assignment-panel {
  margin-bottom: 20px;
}
</style>

