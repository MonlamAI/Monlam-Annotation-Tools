<template>
  <v-container fluid class="pa-6">
    <v-row class="mb-4">
      <v-col cols="12">
        <div class="d-flex align-center">
          <h1 class="text-h4 monlam-gold">Projects</h1>
          <v-spacer />
          <v-btn color="primary" @click="showCreateDialog = true">
            <v-icon start>mdi-plus</v-icon>
            New Project
          </v-btn>
        </div>
      </v-col>
    </v-row>
    
    <!-- Search and Filter -->
    <v-row class="mb-4">
      <v-col cols="12" md="6">
        <v-text-field
          v-model="search"
          prepend-inner-icon="mdi-magnify"
          label="Search projects"
          hide-details
          clearable
        />
      </v-col>
      <v-col cols="12" md="3">
        <v-select
          v-model="typeFilter"
          :items="projectTypes"
          label="Project Type"
          hide-details
          clearable
        />
      </v-col>
    </v-row>
    
    <!-- Projects Grid -->
    <v-row v-if="loading">
      <v-col cols="12" class="text-center py-8">
        <v-progress-circular indeterminate color="primary" size="64" />
      </v-col>
    </v-row>
    
    <v-row v-else-if="filteredProjects.length === 0">
      <v-col cols="12" class="text-center py-8">
        <v-icon size="80" color="grey-lighten-1">mdi-folder-open-outline</v-icon>
        <p class="text-h5 mt-4 text-grey">No projects found</p>
        <p class="text-body-2 text-grey mb-4">
          {{ search ? 'Try a different search term' : 'Create your first project to get started' }}
        </p>
        <v-btn color="primary" @click="showCreateDialog = true">
          Create Project
        </v-btn>
      </v-col>
    </v-row>
    
    <v-row v-else>
      <v-col 
        v-for="project in filteredProjects" 
        :key="project.id"
        cols="12" 
        sm="6" 
        md="4" 
        lg="3"
      >
        <v-card class="hover-lift h-100">
          <v-card-title class="d-flex align-center">
            <router-link 
              :to="`/projects/${project.id}`"
              class="text-decoration-none monlam-gold"
            >
              {{ project.tibetan_name || project.name }}
            </router-link>
            <v-spacer />
            <v-menu>
              <template #activator="{ props }">
                <v-btn icon variant="text" size="small" v-bind="props">
                  <v-icon>mdi-dots-vertical</v-icon>
                </v-btn>
              </template>
              <v-list density="compact">
                <v-list-item :to="`/projects/${project.id}/settings`">
                  <v-list-item-title>Settings</v-list-item-title>
                </v-list-item>
                <v-list-item @click="confirmDelete(project)">
                  <v-list-item-title class="text-error">Delete</v-list-item-title>
                </v-list-item>
              </v-list>
            </v-menu>
          </v-card-title>
          
          <v-card-subtitle v-if="project.tibetan_name">
            {{ project.name }}
          </v-card-subtitle>
          
          <v-card-text>
            <p class="text-body-2 mb-3" style="min-height: 40px;">
              {{ project.description || 'No description' }}
            </p>
            
            <div class="d-flex flex-wrap gap-2">
              <v-chip size="small" color="primary" variant="outlined">
                {{ formatProjectType(project.project_type) }}
              </v-chip>
              <v-chip size="small">
                <v-icon start size="small">mdi-account-group</v-icon>
                {{ project.member_count }}
              </v-chip>
            </div>
          </v-card-text>
          
          <v-card-actions>
            <v-btn 
              variant="text" 
              color="primary"
              :to="`/projects/${project.id}/dataset`"
            >
              Dataset
            </v-btn>
            <v-btn 
              variant="text" 
              color="primary"
              :to="`/projects/${project.id}/annotation`"
            >
              Annotate
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>
    
    <!-- Create Project Dialog -->
    <v-dialog v-model="showCreateDialog" max-width="600">
      <v-card>
        <v-card-title>Create New Project</v-card-title>
        <v-card-text>
          <v-form ref="createForm">
            <v-text-field
              v-model="newProject.name"
              label="Project Name"
              :rules="[v => !!v || 'Name is required']"
            />
            <v-text-field
              v-model="newProject.tibetan_name"
              label="Tibetan Name (optional)"
              placeholder="བོད་ཡིག་མིང།"
            />
            <v-textarea
              v-model="newProject.description"
              label="Description"
              rows="2"
            />
            <v-select
              v-model="newProject.project_type"
              :items="projectTypes"
              label="Project Type"
              :rules="[v => !!v || 'Type is required']"
            />
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="showCreateDialog = false">Cancel</v-btn>
          <v-btn color="primary" :loading="creating" @click="createProject">
            Create
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
    
    <!-- Delete Confirmation Dialog -->
    <v-dialog v-model="showDeleteDialog" max-width="400">
      <v-card>
        <v-card-title class="text-error">Delete Project</v-card-title>
        <v-card-text>
          Are you sure you want to delete "{{ projectToDelete?.name }}"? 
          This action cannot be undone.
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="showDeleteDialog = false">Cancel</v-btn>
          <v-btn color="error" :loading="deleting" @click="deleteProject">
            Delete
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup>
import { ref, computed, reactive, onMounted, inject } from 'vue'
import { useProjectStore } from '@/stores/project'

const projectStore = useProjectStore()
const snackbar = inject('snackbar')

const search = ref('')
const typeFilter = ref(null)
const showCreateDialog = ref(false)
const showDeleteDialog = ref(false)
const creating = ref(false)
const deleting = ref(false)
const projectToDelete = ref(null)
const createForm = ref(null)

const newProject = reactive({
  name: '',
  tibetan_name: '',
  description: '',
  project_type: 'sequence_labeling'
})

const projectTypes = [
  { title: 'Sequence Labeling', value: 'sequence_labeling' },
  { title: 'Document Classification', value: 'document_classification' },
  { title: 'Speech to Text', value: 'speech_to_text' },
  { title: 'Sequence to Sequence', value: 'seq2seq' },
  { title: 'Image Classification', value: 'image_classification' },
]

const loading = computed(() => projectStore.loading)
const projects = computed(() => projectStore.projects)

const filteredProjects = computed(() => {
  let result = projects.value

  if (search.value) {
    const term = search.value.toLowerCase()
    result = result.filter(p => 
      p.name.toLowerCase().includes(term) ||
      p.tibetan_name?.toLowerCase().includes(term) ||
      p.description?.toLowerCase().includes(term)
    )
  }

  if (typeFilter.value) {
    result = result.filter(p => p.project_type === typeFilter.value)
  }

  return result
})

function formatProjectType(type) {
  const found = projectTypes.find(t => t.value === type)
  return found ? found.title : type
}

async function createProject() {
  const { valid } = await createForm.value.validate()
  if (!valid) return

  creating.value = true
  const result = await projectStore.createProject(newProject)
  creating.value = false

  if (result.success) {
    snackbar.message = 'Project created successfully!'
    snackbar.color = 'success'
    snackbar.show = true
    showCreateDialog.value = false
    // Reset form
    Object.assign(newProject, {
      name: '',
      tibetan_name: '',
      description: '',
      project_type: 'sequence_labeling'
    })
  } else {
    snackbar.message = 'Failed to create project'
    snackbar.color = 'error'
    snackbar.show = true
  }
}

function confirmDelete(project) {
  projectToDelete.value = project
  showDeleteDialog.value = true
}

async function deleteProject() {
  if (!projectToDelete.value) return

  deleting.value = true
  const result = await projectStore.deleteProject(projectToDelete.value.id)
  deleting.value = false

  if (result.success) {
    snackbar.message = 'Project deleted'
    snackbar.color = 'success'
    snackbar.show = true
    showDeleteDialog.value = false
    projectToDelete.value = null
  } else {
    snackbar.message = 'Failed to delete project'
    snackbar.color = 'error'
    snackbar.show = true
  }
}

onMounted(() => {
  projectStore.fetchProjects()
})
</script>

