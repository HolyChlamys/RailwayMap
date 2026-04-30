import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'map',
      component: () => import('../views/MapView.vue')
    },
    {
      path: '/transfer',
      name: 'transfer',
      component: () => import('../views/TransferView.vue')
    }
  ]
})

export default router
