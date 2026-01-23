<template>
  <v-tooltip bottom v-if="isAnnotator">
    <template #activator="{ on }">
      <v-btn 
        icon 
        v-on="on" 
        @click="markAsDefect"
        :disabled="isLoading"
        :loading="isLoading"
      >
        <v-icon :color="iconColor">
          {{ mdiAlertCircle }}
        </v-icon>
      </v-btn>
    </template>
    <span>Mark as Defect</span>
  </v-tooltip>
</template>

<script>
import { mdiAlertCircle } from '@mdi/js'

export default {
  props: {
    projectId: {
      type: Number,
      required: true
    },
    exampleId: {
      type: Number,
      required: true
    }
  },

  data() {
    return {
      mdiAlertCircle,
      isLoading: false,
      iconColor: 'error',
      isAnnotator: false,
      roleChecked: false
    }
  },

  async mounted() {
    await this.checkUserRole()
  },

  methods: {
    async checkUserRole() {
      // Check if user is an annotator (not approver/admin/manager)
      try {
        const response = await fetch(`/v1/projects/${this.projectId}/my-role`)
        if (response.ok) {
          const roleData = await response.json()
          const roleName = (roleData.rolename || roleData.role || '').toLowerCase()
          
          // User is annotator if role includes 'annotator' but not admin/manager/approver
          this.isAnnotator = roleName.includes('annotator') && 
                            !roleName.includes('admin') && 
                            !roleName.includes('manager') && 
                            !roleName.includes('approver')
        }
      } catch (error) {
        console.error('[Defect Button] Error checking role:', error)
        // Default to showing button, backend will validate
        this.isAnnotator = true
      } finally {
        this.roleChecked = true
      }
    },

    async markAsDefect() {
      if (this.isLoading) return

      // Confirm action
      const confirmed = confirm(
        'Mark this example as a defect?\n\n' +
        'This will permanently hide this example from your view. ' +
        'You will not see it again.\n\n' +
        'Click OK to mark as defect, or Cancel to abort.'
      )

      if (!confirmed) return

      this.isLoading = true
      this.iconColor = 'warning'

      try {
        // Get CSRF token
        const csrfToken = this.getCsrfToken()

        // Call skip API with defect reason
        const response = await fetch(
          `/v1/projects/${this.projectId}/tracking/${this.exampleId}/skip/`,
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({
              reason: 'Defect - Example has issues that prevent annotation'
            })
          }
        )

        if (response.ok) {
          const data = await response.json()
          
          // Show success notification
          this.showNotification('✅ Example marked as defect. You will not see it anymore.', 'success')
          
          // Change icon to success temporarily
          this.iconColor = 'success'
          
          // Navigate to next example after a short delay
          setTimeout(() => {
            this.navigateToNext()
          }, 1500)
        } else {
          const errorData = await response.json().catch(() => ({ error: 'Unknown error' }))
          throw new Error(errorData.error || 'Failed to mark as defect')
        }
      } catch (error) {
        console.error('[Defect Button] Error:', error)
        this.showNotification('❌ Error: ' + error.message, 'error')
        this.iconColor = 'error'
      } finally {
        this.isLoading = false
      }
    },

    getCsrfToken() {
      const cookieMatch = document.cookie.match(/csrftoken=([^;]+)/)
      return cookieMatch ? cookieMatch[1] : ''
    },

    showNotification(message, type = 'success') {
      // Create a simple notification element
      const notification = document.createElement('div')
      const bgColor = type === 'success' ? '#4caf50' : '#f44336'
      notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${bgColor};
        color: white;
        padding: 12px 20px;
        border-radius: 4px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
        z-index: 10000;
        font-size: 14px;
        max-width: 400px;
      `
      notification.textContent = message
      document.body.appendChild(notification)
      setTimeout(() => {
        notification.style.transition = 'opacity 0.3s'
        notification.style.opacity = '0'
        setTimeout(() => notification.remove(), 300)
      }, 3000)
    },

    navigateToNext() {
      // Try to find and click next button using pagination component
      const paginationButtons = document.querySelectorAll('.v-btn')
      for (const btn of paginationButtons) {
        const ariaLabel = btn.getAttribute('aria-label')
        const text = btn.textContent || ''
        if (ariaLabel && ariaLabel.toLowerCase().includes('next')) {
          btn.click()
          return
        }
        if (text.includes('Next') || text.includes('chevron_right')) {
          btn.click()
          return
        }
      }
      
      // Fallback: navigate using router
      const currentPage = parseInt(this.$route.query.page || '1', 10)
      this.$router.push({
        query: {
          ...this.$route.query,
          page: (currentPage + 1).toString()
        }
      })
    }
  }
}
</script>

