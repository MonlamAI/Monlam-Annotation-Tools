import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/services/api'

export const useTrackingStore = defineStore('tracking', () => {
  const trackingStatus = ref(null)
  const summary = ref(null)
  const annotatorStats = ref([])
  const reviewerStats = ref([])
  const loading = ref(false)
  const error = ref(null)

  async function fetchTrackingStatus(projectId, exampleId) {
    try {
      const response = await api.get(`/projects/${projectId}/tracking/${exampleId}/status/`)
      trackingStatus.value = response.data
      return response.data
    } catch (err) {
      console.error('Failed to fetch tracking status:', err)
      // Return default pending status if no tracking exists
      return {
        example_id: exampleId,
        status: 'pending',
        status_display: 'Pending',
        annotated_by: null,
        reviewed_by: null,
        is_locked: false,
        locked_by: null
      }
    }
  }

  async function approve(projectId, exampleId, notes = '') {
    try {
      const response = await api.post(`/projects/${projectId}/tracking/${exampleId}/approve/`, {
        notes
      })
      trackingStatus.value = {
        ...trackingStatus.value,
        status: 'approved',
        status_display: 'Approved',
        reviewed_by: response.data.reviewed_by
      }
      return { success: true, data: response.data }
    } catch (err) {
      console.error('Failed to approve:', err)
      return { 
        success: false, 
        error: err.response?.data?.error || 'Failed to approve' 
      }
    }
  }

  async function reject(projectId, exampleId, notes) {
    if (!notes || !notes.trim()) {
      return { success: false, error: 'Rejection reason is required' }
    }

    try {
      const response = await api.post(`/projects/${projectId}/tracking/${exampleId}/reject/`, {
        notes
      })
      trackingStatus.value = {
        ...trackingStatus.value,
        status: 'rejected',
        status_display: 'Rejected',
        reviewed_by: response.data.reviewed_by
      }
      return { success: true, data: response.data }
    } catch (err) {
      console.error('Failed to reject:', err)
      return { 
        success: false, 
        error: err.response?.data?.error || 'Failed to reject' 
      }
    }
  }

  async function acquireLock(projectId, exampleId) {
    try {
      const response = await api.post(`/projects/${projectId}/tracking/${exampleId}/lock/`)
      return { success: true, data: response.data }
    } catch (err) {
      console.error('Failed to acquire lock:', err)
      return { 
        success: false, 
        error: err.response?.data?.error || 'Failed to acquire lock',
        locked_by: err.response?.data?.locked_by
      }
    }
  }

  async function releaseLock(projectId, exampleId) {
    try {
      await api.post(`/projects/${projectId}/tracking/${exampleId}/unlock/`)
      return { success: true }
    } catch (err) {
      console.error('Failed to release lock:', err)
      return { success: false, error: err.response?.data?.error || 'Failed to release lock' }
    }
  }

  async function markSubmitted(projectId, exampleId) {
    try {
      const response = await api.post(`/projects/${projectId}/tracking/${exampleId}/submit/`)
      trackingStatus.value = {
        ...trackingStatus.value,
        status: 'submitted',
        status_display: 'Submitted'
      }
      return { success: true, data: response.data }
    } catch (err) {
      console.error('Failed to mark submitted:', err)
      return { success: false, error: err.response?.data?.error || 'Failed to submit' }
    }
  }

  async function fetchSummary(projectId) {
    loading.value = true
    try {
      const response = await api.get(`/projects/${projectId}/tracking/summary/`)
      summary.value = response.data
      return response.data
    } catch (err) {
      console.error('Failed to fetch summary:', err)
      return null
    } finally {
      loading.value = false
    }
  }

  async function fetchAnnotatorStats(projectId) {
    try {
      const response = await api.get(`/projects/${projectId}/tracking/annotators/`)
      annotatorStats.value = response.data
      return response.data
    } catch (err) {
      console.error('Failed to fetch annotator stats:', err)
      return []
    }
  }

  async function fetchReviewerStats(projectId) {
    try {
      const response = await api.get(`/projects/${projectId}/tracking/approvers/`)
      reviewerStats.value = response.data
      return response.data
    } catch (err) {
      console.error('Failed to fetch reviewer stats:', err)
      return []
    }
  }

  return {
    trackingStatus,
    summary,
    annotatorStats,
    reviewerStats,
    loading,
    error,
    fetchTrackingStatus,
    approve,
    reject,
    acquireLock,
    releaseLock,
    markSubmitted,
    fetchSummary,
    fetchAnnotatorStats,
    fetchReviewerStats
  }
})

