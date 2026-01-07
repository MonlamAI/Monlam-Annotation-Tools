<template>
  <div class="dataset-table">
    <v-data-table-server
      v-model:items-per-page="itemsPerPage"
      v-model:page="page"
      :headers="headers"
      :items="examples"
      :items-length="totalCount"
      :loading="loading"
      :search="search"
      class="elevation-1"
      item-value="id"
      @update:options="loadItems"
    >
      <!-- ID Column -->
      <template #item.id="{ item }">
        <span class="font-weight-medium">#{{ item.id }}</span>
      </template>
      
      <!-- Text Column -->
      <template #item.display_text="{ item }">
        <div class="text-truncate tibetan-text" style="max-width: 400px;">
          {{ item.display_text || item.text || item.upload_name }}
        </div>
      </template>
      
      <!-- Annotated By Column -->
      <template #item.annotated_by="{ item }">
        <template v-if="item.annotated_by">
          <v-chip size="small" color="primary" variant="outlined">
            <v-icon start size="small">mdi-account</v-icon>
            {{ item.annotated_by.username }}
          </v-chip>
        </template>
        <span v-else class="text-grey">—</span>
      </template>
      
      <!-- Reviewed By Column -->
      <template #item.reviewed_by="{ item }">
        <template v-if="item.reviewed_by">
          <v-chip size="small" color="success" variant="outlined">
            <v-icon start size="small">mdi-account-check</v-icon>
            {{ item.reviewed_by.username }}
          </v-chip>
        </template>
        <span v-else class="text-grey">—</span>
      </template>
      
      <!-- Status Column -->
      <template #item.status="{ item }">
        <span :class="['status-badge', item.status || 'pending']">
          <v-icon v-if="item.status === 'approved'" size="x-small">mdi-check</v-icon>
          <v-icon v-else-if="item.status === 'rejected'" size="x-small">mdi-close</v-icon>
          <v-icon v-else-if="item.status === 'submitted'" size="x-small">mdi-send</v-icon>
          <v-icon v-else-if="item.status === 'in_progress'" size="x-small">mdi-pencil</v-icon>
          <v-icon v-else size="x-small">mdi-clock-outline</v-icon>
          {{ item.status_display || 'Pending' }}
        </span>
      </template>
      
      <!-- Actions Column -->
      <template #item.actions="{ item }">
        <v-btn
          size="small"
          color="primary"
          variant="text"
          :to="`/projects/${projectId}/annotation/${item.id}`"
        >
          <v-icon start>mdi-pencil</v-icon>
          Annotate
        </v-btn>
      </template>
      
      <!-- Top toolbar -->
      <template #top>
        <v-toolbar flat>
          <v-toolbar-title class="monlam-gold">
            གཞི་གྲངས། Dataset
          </v-toolbar-title>
          
          <v-spacer />
          
          <!-- Status Filter -->
          <v-select
            v-model="statusFilter"
            :items="statusOptions"
            label="Filter by Status"
            density="compact"
            hide-details
            clearable
            class="mr-4"
            style="max-width: 200px;"
          />
          
          <!-- Search -->
          <v-text-field
            v-model="search"
            prepend-inner-icon="mdi-magnify"
            label="Search"
            density="compact"
            hide-details
            single-line
            clearable
            style="max-width: 300px;"
          />
        </v-toolbar>
      </template>
      
      <!-- Empty state -->
      <template #no-data>
        <div class="text-center pa-8">
          <v-icon size="64" color="grey-lighten-1">mdi-database-off</v-icon>
          <p class="text-h6 mt-4 text-grey">No examples found</p>
          <p class="text-body-2 text-grey">
            {{ statusFilter ? 'Try changing the status filter' : 'Upload a dataset to get started' }}
          </p>
        </div>
      </template>
    </v-data-table-server>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useExampleStore } from '@/stores/example'

const route = useRoute()
const exampleStore = useExampleStore()

const projectId = computed(() => route.params.projectId)

// Table state
const page = ref(1)
const itemsPerPage = ref(20)
const search = ref('')
const statusFilter = ref(null)
const loading = computed(() => exampleStore.loading)
const examples = computed(() => exampleStore.examples)
const totalCount = computed(() => exampleStore.totalCount)

// Table headers
const headers = [
  { title: 'ID', key: 'id', width: '80px', sortable: true },
  { title: 'Text', key: 'display_text', sortable: false },
  { title: 'Annotated By', key: 'annotated_by', width: '150px', sortable: false },
  { title: 'Reviewed By', key: 'reviewed_by', width: '150px', sortable: false },
  { title: 'Status', key: 'status', width: '140px', sortable: true },
  { title: 'Actions', key: 'actions', width: '120px', sortable: false, align: 'center' },
]

// Status options for filter
const statusOptions = [
  { title: 'Pending', value: 'pending' },
  { title: 'In Progress', value: 'in_progress' },
  { title: 'Submitted', value: 'submitted' },
  { title: 'Approved', value: 'approved' },
  { title: 'Rejected', value: 'rejected' },
]

// Load items
async function loadItems({ page: newPage, itemsPerPage: newItemsPerPage }) {
  exampleStore.currentPage = newPage
  exampleStore.pageSize = newItemsPerPage
  
  const params = {}
  if (statusFilter.value) {
    params.status = statusFilter.value
  }
  if (search.value) {
    params.search = search.value
  }
  
  await exampleStore.fetchExamples(projectId.value, params)
}

// Watch for filter changes
watch([statusFilter, search], () => {
  page.value = 1
  loadItems({ page: 1, itemsPerPage: itemsPerPage.value })
}, { debounce: 300 })
</script>

