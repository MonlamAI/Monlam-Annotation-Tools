<template>
  <v-container fluid class="pa-6">
    <!-- Header with Actions -->
    <v-row class="mb-4">
      <v-col cols="12">
        <div class="d-flex align-center flex-wrap gap-3">
          <div class="text-h5 tibetan-text">
            <v-icon start>mdi-database</v-icon>
            གཞི་གྲངས། / Dataset
          </div>
          
          <v-spacer />
          
          <!-- Upload Button -->
          <JsonUploadDialog 
            :project-id="projectId"
            @uploaded="onDatasetUploaded"
          />
          
          <!-- Refresh Button -->
          <v-btn
            variant="outlined"
            :loading="refreshing"
            @click="refreshDataset"
          >
            <v-icon start>mdi-refresh</v-icon>
            བསྐྱར་གསོ། / Refresh
          </v-btn>
        </div>
      </v-col>
    </v-row>
    
    <!-- Success Message -->
    <v-row v-if="uploadSuccess" class="mb-4">
      <v-col cols="12">
        <v-alert type="success" variant="tonal" closable @click:close="uploadSuccess = null">
          <v-icon start>mdi-check-circle</v-icon>
          {{ uploadSuccess.imported }} དཔེ་མཚོན་ནང་འདྲེན་ལེགས་གྲུབ། / 
          {{ uploadSuccess.imported }} examples imported successfully!
        </v-alert>
      </v-col>
    </v-row>
    
    <!-- Dataset Table -->
    <DatasetTable ref="datasetTable" />
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useProjectStore } from '@/stores/project'
import { useExampleStore } from '@/stores/example'
import DatasetTable from '@/components/dataset/DatasetTable.vue'
import JsonUploadDialog from '@/components/upload/JsonUploadDialog.vue'

const route = useRoute()
const projectStore = useProjectStore()
const exampleStore = useExampleStore()

const projectId = computed(() => route.params.projectId)
const datasetTable = ref(null)
const refreshing = ref(false)
const uploadSuccess = ref(null)

async function refreshDataset() {
  refreshing.value = true
  try {
    await exampleStore.fetchExamples(projectId.value, {
      page: 1,
      forceRefresh: true
    })
  } finally {
    refreshing.value = false
  }
}

function onDatasetUploaded(result) {
  uploadSuccess.value = result
  refreshDataset()
  
  // Auto-hide after 5 seconds
  setTimeout(() => {
    uploadSuccess.value = null
  }, 5000)
}

onMounted(() => {
  if (!projectStore.currentProject || projectStore.currentProject.id !== parseInt(projectId.value)) {
    projectStore.fetchProject(projectId.value)
  }
})
</script>

<style scoped>
.tibetan-text {
  font-family: 'MonlamTBslim', sans-serif;
}
</style>

