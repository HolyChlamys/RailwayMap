import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import App from './App.vue'

import './assets/styles/tokens.css'
import './assets/styles/base.css'
import 'maplibre-gl/dist/maplibre-gl.css'

// ---- Auto dark mode detection ----
const darkQuery = window.matchMedia('(prefers-color-scheme: dark)')
if (darkQuery.matches) {
  document.documentElement.classList.add('dark')
}
darkQuery.addEventListener('change', (e) => {
  document.documentElement.classList.toggle('dark', e.matches)
})

const app = createApp(App)

app.use(createPinia())
app.use(router)

app.mount('#app')
