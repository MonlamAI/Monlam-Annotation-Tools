<template>
  <v-container class="fill-height" fluid>
    <v-row align="center" justify="center">
      <v-col cols="12" sm="8" md="4">
        <v-card class="elevation-12">
          <v-toolbar color="secondary" dark flat>
            <v-toolbar-title class="monlam-gold">
              མོན་ལམ། Monlam Annotation Tools
            </v-toolbar-title>
          </v-toolbar>
          
          <v-card-text class="pa-6">
            <v-form ref="form" @submit.prevent="login">
              <v-text-field
                v-model="credentials.username"
                label="Username"
                prepend-icon="mdi-account"
                :rules="[rules.required]"
                autofocus
              />
              
              <v-text-field
                v-model="credentials.password"
                label="Password"
                prepend-icon="mdi-lock"
                :type="showPassword ? 'text' : 'password'"
                :append-inner-icon="showPassword ? 'mdi-eye' : 'mdi-eye-off'"
                :rules="[rules.required]"
                @click:append-inner="showPassword = !showPassword"
              />
              
              <v-alert
                v-if="error"
                type="error"
                variant="tonal"
                class="mb-4"
              >
                {{ error }}
              </v-alert>
              
              <v-btn
                type="submit"
                color="primary"
                block
                size="large"
                :loading="loading"
              >
                Sign In
              </v-btn>
            </v-form>
          </v-card-text>
        </v-card>
        
        <div class="text-center mt-4">
          <p class="text-caption text-grey">
            Monlam Annotation Tools - བོད་ཡིག་མཆན་བཀོད་ལག་ཆ།
          </p>
        </div>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const form = ref(null)
const showPassword = ref(false)
const loading = ref(false)
const error = ref(null)

const credentials = reactive({
  username: '',
  password: ''
})

const rules = {
  required: v => !!v || 'This field is required'
}

async function login() {
  const { valid } = await form.value.validate()
  if (!valid) return

  loading.value = true
  error.value = null

  const result = await authStore.login(credentials)

  if (result.success) {
    const redirect = route.query.redirect || '/'
    router.push(redirect)
  } else {
    error.value = result.error
  }

  loading.value = false
}
</script>

