import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    // Catch-all — App.vue is the static shell rendered by main.ts.
    // Router is reserved for future query-param-driven navigation.
    {
      path: '/:pathMatch(.*)*',
      name: 'catch-all',
      component: { template: '<div></div>' },
    },
  ],
})

export default router
