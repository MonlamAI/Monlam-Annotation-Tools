<template>
  <v-container fluid class="pa-6">
    <!-- Welcome Header -->
    <v-card class="mb-6" elevation="2">
      <v-card-title class="text-h4 primary--text">
        <v-icon left large color="primary">mdi-hand-wave</v-icon>
        བཀྲ་ཤིས་བདེ་ལེགས། Welcome!
      </v-card-title>
      <v-card-subtitle class="text-h6">
        {{ project.name }}
      </v-card-subtitle>
    </v-card>

    <!-- Quick Actions -->
    <v-card class="mb-6" elevation="2">
      <v-card-title>
        <v-icon left>mdi-lightning-bolt</v-icon>
        མྱུར་སྤྱོད་བྱེད་སྒོ། / Quick Actions
      </v-card-title>
      <v-card-text>
        <v-row>
          <v-col cols="12" sm="4">
            <v-btn 
              block 
              x-large 
              color="primary" 
              @click="startAnnotation"
              class="text-none"
            >
              <v-icon left>mdi-play-circle</v-icon>
              མཆན་འགྲེལ་འགོ་འཛུགས། / Start Annotation
            </v-btn>
          </v-col>
          <v-col cols="12" sm="4">
            <v-btn 
              block 
              x-large 
              outlined 
              color="primary" 
              @click="viewDataset"
              class="text-none"
            >
              <v-icon left>mdi-database</v-icon>
              གཞི་གྲངས། / Dataset
            </v-btn>
          </v-col>
          <v-col v-if="isProjectAdmin" cols="12" sm="4">
            <v-btn 
              block 
              x-large 
              outlined 
              color="secondary" 
              @click="viewStatistics"
              class="text-none"
            >
              <v-icon left>mdi-chart-bar</v-icon>
              གྲུབ་ཐོ། / Statistics
            </v-btn>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <!-- Instructions Section -->
    <v-row>
      <!-- Annotator Instructions -->
      <v-col cols="12" md="6">
        <v-card elevation="2" height="100%">
          <v-card-title class="blue--text text--darken-2">
            <v-icon left color="blue darken-2">mdi-pencil</v-icon>
            ལས་མིའི་ལམ་སྟོན། / Annotator Instructions
          </v-card-title>
          <v-card-subtitle class="text-h6 mt-2">
            མཆན་འགྲེལ་ཇི་ལྟར་རྒྱག་དགོས་མིན། / How to Annotate
          </v-card-subtitle>
          <v-card-text>
            <v-timeline dense>
              <v-timeline-item small color="blue">
                <strong>གོམ་པ་དང་པོ། / Step 1:</strong><br>
                'མཆན་འགྲེལ་འགོ་འཛུགས་'ཞེས་པར་གནོན་ནས་འགོ་འཛུགས་བྱེད་དགོས།<br>
                <span class="grey--text">Click 'Start Annotation' to begin</span>
              </v-timeline-item>
              <v-timeline-item small color="blue">
                <strong>གོམ་པ་གཉིས་པ། / Step 2:</strong><br>
                སྒྲ་ལ་ཉན་ནས་ཡིག་ཐོག་གི་འབྲི་རྩོམ་ལ་ཞིབ་བཤེར་བྱེད་དགོས།<br>
                <span class="grey--text">Listen to the audio and check the transcription</span>
              </v-timeline-item>
              <v-timeline-item small color="blue">
                <strong>གོམ་པ་གསུམ་པ། / Step 3:</strong><br>
                དགོས་ངེས་ཡིན་ན་ཡིག་རྩོམ་ལ་བཟོ་བཅོས་རྒྱག་པ།<br>
                <span class="grey--text">Edit the text if needed</span>
              </v-timeline-item>
              <v-timeline-item small color="green">
                <strong>གོམ་པ་བཞི་པ། / Step 4:</strong><br>
                ར་སྤྲོད་བྱེད་པའི་ཆེད་དུ་རྟགས་ (✓) ལ་གནོན་ནས་མདུན་དུ་འགྲོ་དགོས།<br>
                <span class="grey--text">Click the checkmark (✓) to confirm and move to next</span>
              </v-timeline-item>
            </v-timeline>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- Reviewer Instructions -->
      <v-col cols="12" md="6">
        <v-card elevation="2" height="100%">
          <v-card-title class="orange--text text--darken-2">
            <v-icon left color="orange darken-2">mdi-check-decagram</v-icon>
            ཚན་པའི་འགན་འཛིན་གྱི་ལམ་སྟོན། / Reviewer Instructions
          </v-card-title>
          <v-card-subtitle class="text-h6 mt-2">
            ཞིབ་བཤེར་ཇི་ལྟར་བྱེད་དགོས་མིན། / How to Review
          </v-card-subtitle>
          <v-card-text>
            <v-timeline dense>
              <v-timeline-item small color="orange">
                <strong>གོམ་པ་དང་པོ། / Step 1:</strong><br>
                གཞི་གྲངས་ཚོགས་ལ་འགྲོ་ནས་ 'གྲུབ་ཟིན་པ་'ཞེས་པར་ལ་གཟིགས་དགོས།<br>
                <span class="grey--text">Go to Dataset and filter by 'Done'</span>
              </v-timeline-item>
              <v-timeline-item small color="orange">
                <strong>གོམ་པ་གཉིས་པ། / Step 2:</strong><br>
                མཆན་འགྲེལ་རེ་རེ་བཞིན་དག་ཚད་ལ་ཞིབ་བཤེར་བྱེད་པ།<br>
                <span class="grey--text">Check each annotation for accuracy</span>
              </v-timeline-item>
              <v-timeline-item small color="green">
                <strong>གོམ་པ་གསུམ་པ། / Step 3:</strong><br>
                'འགྲིག' ཡང་ན་ 'མ་འགྲིག' ཞེས་པར་འོས་འཚམ་ལྟར་གནོན་དགོས།<br>
                <span class="grey--text">Click 'Approve' or 'Reject' as appropriate</span>
              </v-timeline-item>
            </v-timeline>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Footer Note -->
    <v-card class="mt-6 text-center" color="grey lighten-4" flat>
      <v-card-text>
        <v-icon left small>mdi-help-circle</v-icon>
        རོགས་རམ་དགོས་སམ། ཁྱེད་ཀྱི་ཚན་པའི་འགན་འཛིན་ཡང་ན་དམིགས་འབེན་འགན་འཛིན་ལ་འབྲེལ་བ་གནང་རོགས།<br>
        <span class="grey--text text--darken-1">Need help? Contact your project administrator.</span>
      </v-card-text>
    </v-card>
  </v-container>
</template>

<script>
import { getLinkToAnnotationPage } from '~/presenter/linkToAnnotationPage'

export default {
  layout: 'project',

  middleware: ['check-auth', 'auth', 'setCurrentProject'],

  validate({ params }) {
    return /^\d+$/.test(params.id)
  },

  data() {
    return {
      project: {},
      isProjectAdmin: false
    }
  },

  async created() {
    await this.fetchProject()
    await this.checkRole()
  },

  methods: {
    async fetchProject() {
      try {
        const response = await this.$axios.$get(`/v1/projects/${this.$route.params.id}`)
        this.project = response
      } catch (e) {
        console.error('Failed to fetch project:', e)
      }
    },

    async checkRole() {
      try {
        const response = await this.$axios.$get(`/v1/projects/${this.$route.params.id}/my-role`)
        this.isProjectAdmin = response.is_project_admin || response.rolename === 'project_admin'
      } catch (e) {
        console.error('Failed to check role:', e)
      }
    },

    startAnnotation() {
      const query = this.$services.option.findOption(this.$route.params.id)
      const link = getLinkToAnnotationPage(this.$route.params.id, this.project.projectType || this.project.project_type)
      this.$router.push({
        path: this.localePath(link),
        query
      })
    },

    viewDataset() {
      this.$router.push(this.localePath(`/projects/${this.$route.params.id}/dataset`))
    },

    viewStatistics() {
      window.location.href = `/monlam/${this.$route.params.id}/completion/`
    }
  }
}
</script>

<style scoped>
.v-timeline-item {
  padding-bottom: 16px;
}
</style>

