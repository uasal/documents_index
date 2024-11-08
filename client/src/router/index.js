import { createRouter, createWebHistory } from 'vue-router'
import DocumentsAll from '../components/DocumentsAll.vue'
import CollaboratorsAll from '../components/CollaboratorsAll.vue'
import DocumentsItem from '../components/DocumentsItem.vue'
import Ping from '../components/Ping.vue'

import DemoDocumentsAll from '../componentsDemo/DocumentsAll.vue'
import DemoNumbersAll from '../componentsDemo/NumbersAll.vue'
import DemoCollaboratorsAll from '../componentsDemo/CollaboratorsAll.vue'
import DemoDocumentsItem from '../componentsDemo/DocumentsItem.vue'

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
    // demo
    {
      path: '/demo',
      name: 'DemoDocumentsAll',
      component: DemoDocumentsAll,
    },
    {
      path: '/demo/numbers',
      name: 'DemoNumbersAll',
      component: DemoNumbersAll,
    },
    {
      path: '/demo/docs/:docID',
      name: 'DemoDocumentsItem',
      component: DemoDocumentsItem,
    },
    {
      path: '/demo/collaborators',
      name: 'DemoCollaboratorsAll',
      component: DemoCollaboratorsAll,
    },
  ]
})

export default router
