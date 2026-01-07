import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/services/api'

export const useProjectStore = defineStore('project', () => {
  const projects = ref([])
  const currentProject = ref(null)
  const loading = ref(false)
  const error = ref(null)

  const projectList = computed(() => projects.value)
  
  async function fetchProjects() {
    loading.value = true
    error.value = null
    try {
      const response = await api.get('/projects/')
      projects.value = response.data.results || response.data
    } catch (err) {
      error.value = 'Failed to load projects'
      console.error('Failed to fetch projects:', err)
    } finally {
      loading.value = false
    }
  }

  async function fetchProject(projectId) {
    loading.value = true
    error.value = null
    try {
      const response = await api.get(`/projects/${projectId}/`)
      currentProject.value = response.data
      return response.data
    } catch (err) {
      error.value = 'Failed to load project'
      console.error('Failed to fetch project:', err)
      return null
    } finally {
      loading.value = false
    }
  }

  async function createProject(projectData) {
    try {
      const response = await api.post('/projects/', projectData)
      projects.value.unshift(response.data)
      return { success: true, data: response.data }
    } catch (err) {
      return { success: false, error: err.response?.data || 'Failed to create project' }
    }
  }

  async function updateProject(projectId, projectData) {
    try {
      const response = await api.patch(`/projects/${projectId}/`, projectData)
      const index = projects.value.findIndex(p => p.id === projectId)
      if (index !== -1) {
        projects.value[index] = response.data
      }
      if (currentProject.value?.id === projectId) {
        currentProject.value = response.data
      }
      return { success: true, data: response.data }
    } catch (err) {
      return { success: false, error: err.response?.data || 'Failed to update project' }
    }
  }

  async function deleteProject(projectId) {
    try {
      await api.delete(`/projects/${projectId}/`)
      projects.value = projects.value.filter(p => p.id !== projectId)
      if (currentProject.value?.id === projectId) {
        currentProject.value = null
      }
      return { success: true }
    } catch (err) {
      return { success: false, error: err.response?.data || 'Failed to delete project' }
    }
  }

  return {
    projects,
    currentProject,
    loading,
    error,
    projectList,
    fetchProjects,
    fetchProject,
    createProject,
    updateProject,
    deleteProject
  }
})

