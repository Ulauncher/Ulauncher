import 'bootstrap/dist/css/bootstrap.css'
import 'bootstrap-vue/dist/bootstrap-vue.css'

// The Vue build version to load with the `import` command
// (runtime-only or standalone) has been set in webpack.base.conf with an alias.
import Vue from 'vue'
import Vuex from 'vuex'
import App from './App'
import router from './router'
import BootstrapVue from 'bootstrap-vue'
import bus from './event-bus'
import createStore from './store'

Vue.config.productionTip = false
Vue.use(BootstrapVue)
Vue.use(Vuex)

/* eslint-disable no-new */
new Vue({
  el: '#app',
  router,
  store: createStore(),
  template: '<App/>',
  components: { App }
})

window.onNotification = function(eventName, data) {
  console.info('onNotification', eventName, JSON.stringify(data))
  bus.$emit(eventName, data)
}
