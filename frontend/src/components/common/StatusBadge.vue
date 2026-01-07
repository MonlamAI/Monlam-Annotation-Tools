<template>
  <span :class="['status-badge', status]">
    <v-icon v-if="showIcon" :size="iconSize" class="mr-1">{{ statusIcon }}</v-icon>
    {{ displayText }}
  </span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  status: {
    type: String,
    default: 'pending',
    validator: (value) => ['pending', 'in_progress', 'submitted', 'approved', 'rejected'].includes(value)
  },
  showIcon: {
    type: Boolean,
    default: true
  },
  iconSize: {
    type: String,
    default: 'x-small'
  }
})

const statusMap = {
  pending: { text: 'Pending', icon: 'mdi-clock-outline' },
  in_progress: { text: 'In Progress', icon: 'mdi-pencil' },
  submitted: { text: 'Submitted', icon: 'mdi-send' },
  approved: { text: 'Approved', icon: 'mdi-check' },
  rejected: { text: 'Rejected', icon: 'mdi-close' },
}

const displayText = computed(() => statusMap[props.status]?.text || 'Unknown')
const statusIcon = computed(() => statusMap[props.status]?.icon || 'mdi-help-circle')
</script>

