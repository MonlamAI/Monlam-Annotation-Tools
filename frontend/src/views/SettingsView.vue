<template>
  <v-container fluid class="pa-6">
    <v-row class="mb-6">
      <v-col cols="12">
        <h1 class="text-h4 monlam-gold">Project Settings</h1>
      </v-col>
    </v-row>
    
    <v-row>
      <v-col cols="12" md="8">
        <v-card>
          <v-card-title>General Settings</v-card-title>
          <v-card-text>
            <v-form ref="form" @submit.prevent="saveSettings">
              <v-text-field
                v-model="settings.name"
                label="Project Name"
                :rules="[v => !!v || 'Name is required']"
              />
              
              <v-text-field
                v-model="settings.tibetan_name"
                label="Tibetan Name"
                placeholder="བོད་ཡིག་མིང།"
              />
              
              <v-textarea
                v-model="settings.description"
                label="Description"
                rows="3"
              />
              
              <v-textarea
                v-model="settings.guideline"
                label="Annotation Guideline"
                rows="5"
                placeholder="Instructions for annotators..."
              />
              
              <v-divider class="my-4" />
              
              <v-switch
                v-model="settings.random_order"
                label="Random order"
                hint="Present examples in random order"
                persistent-hint
              />
              
              <v-switch
                v-model="settings.collaborative_annotation"
                label="Collaborative annotation"
                hint="Multiple annotators can annotate the same example"
                persistent-hint
              />
            </v-form>
          </v-card-text>
          <v-card-actions>
            <v-spacer />
            <v-btn variant="text" @click="resetSettings">Reset</v-btn>
            <v-btn color="primary" :loading="saving" @click="saveSettings">
              Save Changes
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
      
      <v-col cols="12" md="4">
        <v-card class="mb-4">
          <v-card-title class="text-error">Danger Zone</v-card-title>
          <v-card-text>
            <p class="text-body-2 mb-4">
              Deleting this project will permanently remove all examples, 
              annotations, and settings. This cannot be undone.
            </p>
            <v-btn color="error" variant="outlined" @click="confirmDelete">
              Delete Project
            </v-btn>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
    
    <!-- Delete Confirmation -->
    <v-dialog v-model="showDeleteDialog" max-width="400">
      <v-card>
        <v-card-title class="text-error">Delete Project</v-card-title>
        <v-card-text>
          <p>Type the project name to confirm deletion:</p>
          <v-text-field
            v-model="deleteConfirmation"
            :placeholder="project?.name"
            class="mt-2"
          />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="showDeleteDialog = false">Cancel</v-btn>
          <v-btn 
            color="error" 
            :disabled="deleteConfirmation !== project?.name"
            :loading="deleting"
            @click="deleteProject"
          >
            Delete
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup>
import { ref, reactive, computed, onMounted, inject } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useProjectStore } from '@/stores/project'

const route = useRoute()
const router = useRouter()
const projectStore = useProjectStore()
const snackbar = inject('snackbar')

const projectId = computed(() => route.params.projectId)
const project = computed(() => projectStore.currentProject)

const form = ref(null)
const saving = ref(false)
const deleting = ref(false)
const showDeleteDialog = ref(false)
const deleteConfirmation = ref('')

const settings = reactive({
  name: '',
  tibetan_name: '',
  description: '',
  guideline: '',
  random_order: false,
  collaborative_annotation: false,
})

function loadSettings() {
  if (project.value) {
    Object.assign(settings, {
      name: project.value.name,
      tibetan_name: project.value.tibetan_name || '',
      description: project.value.description || '',
      guideline: project.value.guideline || '',
      random_order: project.value.random_order,
      collaborative_annotation: project.value.collaborative_annotation,
    })
  }
}

function resetSettings() {
  loadSettings()
}

async function saveSettings() {
  const { valid } = await form.value.validate()
  if (!valid) return

  saving.value = true
  const result = await projectStore.updateProject(projectId.value, settings)
  saving.value = false

  if (result.success) {
    snackbar.message = 'Settings saved!'
    snackbar.color = 'success'
    snackbar.show = true
  } else {
    snackbar.message = 'Failed to save settings'
    snackbar.color = 'error'
    snackbar.show = true
  }
}

function confirmDelete() {
  deleteConfirmation.value = ''
  showDeleteDialog.value = true
}

async function deleteProject() {
  deleting.value = true
  const result = await projectStore.deleteProject(projectId.value)
  deleting.value = false

  if (result.success) {
    snackbar.message = 'Project deleted'
    snackbar.color = 'success'
    snackbar.show = true
    router.push('/projects')
  } else {
    snackbar.message = 'Failed to delete project'
    snackbar.color = 'error'
    snackbar.show = true
  }
}

onMounted(async () => {
  await projectStore.fetchProject(projectId.value)
  loadSettings()
})
</script>

