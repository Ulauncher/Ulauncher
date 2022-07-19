import Vuex from 'vuex'
import fetchData from '@/fetchData'
import bus from '@/event-bus'

export default function createStore() {
  return new Vuex.Store({
    state: {
      prefs: {}
    },

    getters: {
      prefsLoaded: state => {
        return state.prefs && !!Object.keys(state.prefs).length
      }
    },

    mutations: {
      setPrefs: (state, prefs) => {
        state.prefs = { ...state.prefs, ...prefs }
      }
    },

    actions: {
      getAllPrefs: ({ commit }) => {
        fetchData('prefs:///get/all').then(
          data => commit('setPrefs', data),
          err => bus.$emit('error', err)
        )
      }
    }
  })
}
