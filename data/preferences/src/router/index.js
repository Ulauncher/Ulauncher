import Vue from 'vue'
import Router from 'vue-router'
import Preferences from '@/components/pages/Preferences'
import Shortcuts from '@/components/pages/Shortcuts'
import EditShortcut from '@/components/pages/EditShortcut'
import Extensions from '@/components/pages/Extensions'
import Help from '@/components/pages/Help'
import About from '@/components/pages/About'

Vue.use(Router)

export default new Router({
  routes: [
    {
      path: '/',
      redirect: { name: 'preferences' }
    },
    {
      path: '/preferences',
      name: 'preferences',
      component: Preferences
    },
    {
      path: '/shortcuts',
      name: 'shortcuts',
      component: Shortcuts
    },
    {
      path: '/edit-shortcut',
      name: 'edit-shortcut',
      props: route => route.query,
      component: EditShortcut
    },
    {
      path: '/extensions',
      name: 'extensions',
      component: Extensions
    },
    {
      path: '/help',
      name: 'help',
      component: Help
    },
    {
      path: '/about',
      name: 'about',
      component: About
    }
  ]
})
