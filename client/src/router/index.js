import { createRouter, createWebHistory } from 'vue-router'
import DocumentsAll from '../components/DocumentsAll.vue'
import DocumentsItem from '../components/DocumentsItem.vue'
import Ping from '../components/Ping.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'DocumentsAll',
      component: DocumentsAll,
    },
    {
      path: '/documents/:docID',
      name: 'DocumentsItem',
      component: DocumentsItem,
    },
    {
      path: '/ping',
      name: 'ping',
      component: Ping
    },
  ]
})

export default router
