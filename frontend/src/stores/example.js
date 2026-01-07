import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/services/api'

export const useExampleStore = defineStore('example', () => {
  const examples = ref([])
  const currentExample = ref(null)
  const totalCount = ref(0)
  const loading = ref(false)
  const error = ref(null)
  const currentPage = ref(1)
  const pageSize = ref(20)

  async function fetchExamples(projectId, params = {}) {
    loading.value = true
    error.value = null
    try {
      const response = await api.get(`/projects/${projectId}/examples/`, {
        params: {
          page: currentPage.value,
          page_size: pageSize.value,
          ...params
        }
      })
      examples.value = response.data.results || response.data
      totalCount.value = response.data.count || examples.value.length
      return examples.value
    } catch (err) {
      error.value = 'Failed to load examples'
      console.error('Failed to fetch examples:', err)
      return []
    } finally {
      loading.value = false
    }
  }

  async function fetchExample(projectId, exampleId) {
    loading.value = true
    error.value = null
    try {
      const response = await api.get(`/projects/${projectId}/examples/${exampleId}/`)
      currentExample.value = response.data
      return response.data
    } catch (err) {
      error.value = 'Failed to load example'
      console.error('Failed to fetch example:', err)
      return null
    } finally {
      loading.value = false
    }
  }

  async function getNextExample(projectId, currentExampleId) {
    const currentIndex = examples.value.findIndex(e => e.id === currentExampleId)
    if (currentIndex < examples.value.length - 1) {
      return examples.value[currentIndex + 1]
    }
    // Load next page
    if ((currentPage.value * pageSize.value) < totalCount.value) {
      currentPage.value++
      await fetchExamples(projectId)
      return examples.value[0] || null
    }
    return null
  }

  async function getPreviousExample(projectId, currentExampleId) {
    const currentIndex = examples.value.findIndex(e => e.id === currentExampleId)
    if (currentIndex > 0) {
      return examples.value[currentIndex - 1]
    }
    // Load previous page
    if (currentPage.value > 1) {
      currentPage.value--
      await fetchExamples(projectId)
      return examples.value[examples.value.length - 1] || null
    }
    return null
  }

  async function getStatistics(projectId) {
    try {
      const response = await api.get(`/projects/${projectId}/examples/statistics/`)
      return response.data
    } catch (err) {
      console.error('Failed to fetch statistics:', err)
      return null
    }
  }

  function resetPagination() {
    currentPage.value = 1
    examples.value = []
    totalCount.value = 0
  }

  return {
    examples,
    currentExample,
    totalCount,
    loading,
    error,
    currentPage,
    pageSize,
    fetchExamples,
    fetchExample,
    getNextExample,
    getPreviousExample,
    getStatistics,
    resetPagination
  }
})

