import { createRouter, createWebHistory } from 'vue-router'
import DocumentsAll from '../components/DocumentsAll.vue'
import CollaboratorsAll from '../components/CollaboratorsAll.vue'
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
      path: '/docs/:docID',
      name: 'DocumentsItem',
      component: DocumentsItem,
    },
    {
      path: '/collaborators',
      name: 'CollaboratorsAll',
      component: CollaboratorsAll,
    },
    {
      path: '/ping',
      name: 'ping',
      component: Ping
    },
  ]
})

export default router
