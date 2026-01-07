<template>
  <v-dialog v-model="dialog" max-width="700" persistent>
    <template v-slot:activator="{ props }">
      <v-btn
        v-bind="props"
        color="primary"
        variant="elevated"
        class="upload-btn"
      >
        <v-icon start>mdi-upload</v-icon>
        JSON ནང་འདྲེན། / Import JSON
      </v-btn>
    </template>

    <v-card class="upload-dialog">
      <v-card-title class="d-flex align-center pa-4 bg-primary">
        <v-icon start color="white">mdi-file-upload</v-icon>
        <span class="text-white">གཞི་གྲངས་ནང་འདྲེན། / Import Dataset</span>
        <v-spacer />
        <v-btn icon variant="text" @click="closeDialog" color="white">
          <v-icon>mdi-close</v-icon>
        </v-btn>
      </v-card-title>

      <v-card-text class="pa-4">
        <!-- Step 1: File Selection -->
        <div v-if="step === 1">
          <div class="text-h6 mb-3">ཡིག་ཆ་འདེམས། / Select File</div>
          
          <v-file-input
            v-model="selectedFile"
            accept=".json,.jsonl"
            label="JSON/JSONL ཡིག་ཆ།"
            prepend-icon="mdi-file-document"
            variant="outlined"
            show-size
            clearable
            @update:model-value="onFileSelected"
          >
            <template v-slot:append>
              <v-chip v-if="selectedFile" color="success" size="small">
                {{ fileFormat.toUpperCase() }}
              </v-chip>
            </template>
          </v-file-input>

          <!-- Format Info -->
          <v-expansion-panels class="mt-4">
            <v-expansion-panel>
              <v-expansion-panel-title>
                <v-icon start>mdi-information</v-icon>
                ཡིག་ཆའི་རྣམ་གཞག། / File Format
              </v-expansion-panel-title>
              <v-expansion-panel-text>
                <div class="text-body-2">
                  <p class="mb-2"><strong>JSON Array Format:</strong></p>
                  <pre class="code-block">[
  {"text": "Hello", "audio_url": "https://s3.../audio.mp3"},
  {"sentence": "World", "audio": "https://s3.../audio2.mp3"}
]</pre>
                  
                  <p class="mb-2 mt-3"><strong>JSONL Format (one per line):</strong></p>
                  <pre class="code-block">{"text": "Hello", "audio_url": "https://s3.../audio.mp3"}
{"text": "World", "audio_url": "https://s3.../audio2.mp3"}</pre>

                  <p class="mt-3 text-caption">
                    Supported fields: <code>text</code>, <code>sentence</code>, <code>content</code>, 
                    <code>audio_url</code>, <code>audio</code>, <code>audio_link</code>, <code>file_name</code>
                  </p>
                </div>
              </v-expansion-panel-text>
            </v-expansion-panel>
          </v-expansion-panels>

          <!-- Preview Button -->
          <div class="mt-4 d-flex justify-end">
            <v-btn
              color="primary"
              :disabled="!selectedFile"
              :loading="isPreviewLoading"
              @click="previewFile"
            >
              <v-icon start>mdi-eye</v-icon>
              སྔོན་ལྟ། / Preview
            </v-btn>
          </div>
        </div>

        <!-- Step 2: Preview -->
        <div v-if="step === 2">
          <div class="d-flex align-center mb-3">
            <v-btn icon variant="text" @click="step = 1">
              <v-icon>mdi-arrow-left</v-icon>
            </v-btn>
            <div class="text-h6 ml-2">སྔོན་ལྟ། / Preview</div>
          </div>

          <!-- Preview Stats -->
          <v-alert 
            v-if="previewData" 
            :type="previewData.errors.length ? 'warning' : 'success'"
            variant="tonal"
            class="mb-3"
          >
            <div class="d-flex align-center">
              <v-icon start>mdi-file-document-multiple</v-icon>
              <span>
                ཐོ་ཁྲ་ཡོངས་བསྡོམས། / Total Records: <strong>{{ previewData.total_records }}</strong>
              </span>
            </div>
            <div v-if="previewData.errors.length" class="mt-2">
              <v-icon start size="small">mdi-alert</v-icon>
              ནོར་འཁྲུལ། / Errors: {{ previewData.errors.length }}
            </div>
          </v-alert>

          <!-- Errors List -->
          <v-alert
            v-if="previewData?.errors.length"
            type="error"
            variant="tonal"
            class="mb-3"
          >
            <div class="text-subtitle-2 mb-2">ནོར་འཁྲུལ། / Errors:</div>
            <ul class="error-list">
              <li v-for="(err, i) in previewData.errors.slice(0, 5)" :key="i">
                {{ err }}
              </li>
              <li v-if="previewData.errors.length > 5">
                ...and {{ previewData.errors.length - 5 }} more
              </li>
            </ul>
          </v-alert>

          <!-- Preview Table -->
          <v-table v-if="previewData?.preview.length" density="compact" class="preview-table">
            <thead>
              <tr>
                <th width="50">#</th>
                <th>ཡི་གེ། / Text</th>
                <th width="150">སྒྲ། / Audio</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(item, index) in previewData.preview" :key="index">
                <td>{{ index + 1 }}</td>
                <td class="text-truncate" style="max-width: 300px;">
                  {{ item.text || '(empty)' }}
                </td>
                <td>
                  <v-chip v-if="item.audio_url" size="small" color="success" variant="tonal">
                    <v-icon start size="small">mdi-music</v-icon>
                    Yes
                  </v-chip>
                  <span v-else class="text-grey">—</span>
                </td>
              </tr>
            </tbody>
          </v-table>

          <div class="mt-4 d-flex justify-end gap-2">
            <v-btn variant="outlined" @click="step = 1">
              སླར་ལོག / Back
            </v-btn>
            <v-btn
              color="primary"
              :loading="isUploading"
              :disabled="!previewData || previewData.total_records === 0"
              @click="uploadFile"
            >
              <v-icon start>mdi-upload</v-icon>
              ནང་འདྲེན། / Import {{ previewData?.total_records || 0 }} records
            </v-btn>
          </div>
        </div>

        <!-- Step 3: Success -->
        <div v-if="step === 3" class="text-center py-6">
          <v-icon color="success" size="64">mdi-check-circle</v-icon>
          <div class="text-h5 mt-4">
            ནང་འདྲེན་ལེགས་གྲུབ། / Import Successful!
          </div>
          <div class="text-body-1 mt-2">
            {{ uploadResult?.imported }} དཔེ་མཚོན་ནང་འདྲེན་བྱས་ཟིན།
            <br />
            {{ uploadResult?.imported }} examples imported successfully
          </div>
          <v-btn color="primary" class="mt-4" @click="closeDialog">
            སྒོ་རྒྱག / Close
          </v-btn>
        </div>
      </v-card-text>

      <!-- Loading Overlay -->
      <v-overlay
        :model-value="isUploading"
        contained
        class="align-center justify-center"
      >
        <v-progress-circular indeterminate size="64" color="primary" />
        <div class="mt-3 text-white">ནང་འདྲེན་བྱེད་བཞིན། / Importing...</div>
      </v-overlay>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, computed } from 'vue'
import api from '@/services/api'

const props = defineProps({
  projectId: {
    type: [Number, String],
    required: true
  }
})

const emit = defineEmits(['uploaded'])

// State
const dialog = ref(false)
const step = ref(1)
const selectedFile = ref(null)
const previewData = ref(null)
const uploadResult = ref(null)
const isPreviewLoading = ref(false)
const isUploading = ref(false)

// Computed
const fileFormat = computed(() => {
  if (!selectedFile.value) return 'json'
  return selectedFile.value.name.toLowerCase().endsWith('.jsonl') ? 'jsonl' : 'json'
})

// Methods
const onFileSelected = (file) => {
  if (file) {
    previewData.value = null
    step.value = 1
  }
}

const previewFile = async () => {
  if (!selectedFile.value) return
  
  isPreviewLoading.value = true
  
  try {
    const formData = new FormData()
    formData.append('file', selectedFile.value)
    formData.append('format', fileFormat.value)
    
    const response = await api.post(
      `/api/v1/projects/${props.projectId}/examples/upload/preview`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      }
    )
    
    previewData.value = response.data
    step.value = 2
  } catch (error) {
    console.error('Preview error:', error)
    previewData.value = {
      total_records: 0,
      preview: [],
      errors: [error.response?.data?.error || 'Failed to preview file']
    }
    step.value = 2
  } finally {
    isPreviewLoading.value = false
  }
}

const uploadFile = async () => {
  if (!selectedFile.value) return
  
  isUploading.value = true
  
  try {
    const formData = new FormData()
    formData.append('file', selectedFile.value)
    formData.append('format', fileFormat.value)
    
    const response = await api.post(
      `/api/v1/projects/${props.projectId}/examples/upload`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      }
    )
    
    uploadResult.value = response.data
    step.value = 3
    emit('uploaded', response.data)
  } catch (error) {
    console.error('Upload error:', error)
    previewData.value = {
      ...previewData.value,
      errors: [error.response?.data?.error || 'Failed to upload file', ...(previewData.value?.errors || [])]
    }
  } finally {
    isUploading.value = false
  }
}

const closeDialog = () => {
  dialog.value = false
  // Reset state after dialog closes
  setTimeout(() => {
    step.value = 1
    selectedFile.value = null
    previewData.value = null
    uploadResult.value = null
  }, 300)
}
</script>

<style scoped>
.upload-dialog {
  border-radius: 16px;
  overflow: hidden;
}

.code-block {
  background: #1e1e1e;
  color: #d4d4d4;
  padding: 12px;
  border-radius: 8px;
  font-size: 0.75rem;
  overflow-x: auto;
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
}

.error-list {
  margin: 0;
  padding-left: 20px;
  font-size: 0.875rem;
}

.preview-table {
  border-radius: 8px;
  overflow: hidden;
}

.upload-btn {
  font-family: 'MonlamTBslim', sans-serif;
}
</style>

