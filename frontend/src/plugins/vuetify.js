import 'vuetify/styles'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import '@mdi/font/css/materialdesignicons.css'

// Monlam color theme
const monlamTheme = {
  dark: false,
  colors: {
    primary: '#B8963E',      // Monlam Gold
    'primary-darken-1': '#9A7B32',
    secondary: '#1a1a2e',    // Monlam Navy
    accent: '#B8963E',
    error: '#f44336',
    info: '#2196f3',
    success: '#4caf50',
    warning: '#ff9800',
    background: '#f5f5f5',
    surface: '#ffffff',
  },
}

export default createVuetify({
  components,
  directives,
  theme: {
    defaultTheme: 'monlamTheme',
    themes: {
      monlamTheme,
    },
  },
  defaults: {
    VBtn: {
      color: 'primary',
      variant: 'elevated',
    },
    VCard: {
      elevation: 2,
    },
  },
})

