import { createApp, reactive } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import vuetify from './plugins/vuetify'
import i18n from './i18n/config'
import './assets/styles/main.scss'

const app = createApp(App)

// Global snackbar for notifications
const snackbar = reactive({
  show: false,
  message: '',
  color: 'success',
  timeout: 3000
})

app.provide('snackbar', snackbar)

app.use(createPinia())
app.use(router)
app.use(vuetify)
app.use(i18n)

app.mount('#app')

