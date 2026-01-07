<template>
  <v-navigation-drawer
    v-model="drawer"
    :rail="rail"
    permanent
    @click="rail = false"
  >
    <v-list density="compact" nav>
      <!-- Project Home -->
      <v-list-item
        :to="`/projects/${projectId}`"
        prepend-icon="mdi-home"
        title="Project Home"
        :subtitle="tibetanLabels.home"
      />
      
      <v-divider class="my-2" />
      
      <!-- Dataset / གཞི་གྲངས། -->
      <v-list-item
        :to="`/projects/${projectId}/dataset`"
        prepend-icon="mdi-database"
        title="Dataset"
        :subtitle="tibetanLabels.dataset"
      />
      
      <!-- Annotation -->
      <v-list-item
        :to="`/projects/${projectId}/annotation`"
        prepend-icon="mdi-pencil"
        title="Annotate"
        :subtitle="tibetanLabels.annotate"
      />
      
      <v-divider class="my-2" />
      
      <!-- Metrics / Completion Dashboard -->
      <v-list-item
        :to="`/monlam/${projectId}/completion`"
        prepend-icon="mdi-chart-bar"
        title="Completion"
        :subtitle="tibetanLabels.completion"
      />
      
      <!-- Labels -->
      <v-list-item
        :to="`/projects/${projectId}/labels`"
        prepend-icon="mdi-label"
        title="Labels"
        :subtitle="tibetanLabels.labels"
      />
      
      <!-- Members -->
      <v-list-item
        :to="`/projects/${projectId}/members`"
        prepend-icon="mdi-account-group"
        title="Members"
        :subtitle="tibetanLabels.members"
      />
      
      <v-divider class="my-2" />
      
      <!-- Settings -->
      <v-list-item
        v-if="canManage"
        :to="`/projects/${projectId}/settings`"
        prepend-icon="mdi-cog"
        title="Settings"
        :subtitle="tibetanLabels.settings"
      />
      
      <!-- Import/Export -->
      <v-list-item
        v-if="canManage"
        :to="`/projects/${projectId}/import`"
        prepend-icon="mdi-upload"
        title="Import"
        :subtitle="tibetanLabels.import"
      />
      
      <v-list-item
        v-if="canManage"
        :to="`/projects/${projectId}/export`"
        prepend-icon="mdi-download"
        title="Export"
        :subtitle="tibetanLabels.export"
      />
    </v-list>
    
    <template #append>
      <v-btn
        icon
        variant="text"
        @click.stop="rail = !rail"
        class="ma-2"
      >
        <v-icon>{{ rail ? 'mdi-chevron-right' : 'mdi-chevron-left' }}</v-icon>
      </v-btn>
    </template>
  </v-navigation-drawer>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useProjectStore } from '@/stores/project'

const route = useRoute()
const projectStore = useProjectStore()

const drawer = ref(true)
const rail = ref(false)

const projectId = computed(() => route.params.projectId)
const currentProject = computed(() => projectStore.currentProject)

const canManage = computed(() => {
  const role = currentProject.value?.current_user_role
  return role === 'project_manager' || role === 'project_admin'
})

// Tibetan labels for menu items
const tibetanLabels = {
  home: 'ཁྱིམ།',
  dataset: 'གཞི་གྲངས།',
  annotate: 'མཆན་བཀོད།',
  completion: 'འགྲུབ་ཚད།',
  labels: 'མཆན་རྟགས།',
  members: 'ཚོགས་མི།',
  settings: 'སྒྲིག་འགོད།',
  import: 'ནང་འདྲེན།',
  export: 'ཕྱི་འདྲེན།'
}
</script>

