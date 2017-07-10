<template>
  <table>
    <tr>
      <td>
        <label for="hotkey-show-app">Hotkey</label>
      </td>
      <td>
        <b-form-input
          id="hotkey-show-app"
          @focus.native="showHotkeyDialog($event)"
          v-model="hotkey_show_app"></b-form-input>
      </td>
    </tr>

    <tr>
      <td>
        <label for="autostart">Launch at Login</label>
      </td>
      <td>
        <b-form-checkbox
          :disabled="!autostart_allowed"
          id="autostart"
          @change="updateLaunchAtLogin"
          v-model="autostart_enabled"></b-form-checkbox>
      </td>
    </tr>

    <tr>
      <td>
        <label for="show-indicator-icon">Show Indicator Icon</label>
      </td>
      <td>
        <b-form-checkbox
          id="show-indicator-icon"
          @change="updateShowIndicatorIcon"
          v-model="show_indicator_icon"></b-form-checkbox>
      </td>
    </tr>

    <tr>
      <td>
        <label for="show-recent-apps">Show Frequent Apps</label>
      </td>
      <td>
        <b-form-checkbox
          id="show-recent-apps"
          @change="updateShowRecentApps"
          v-model="show_recent_apps"></b-form-checkbox>
      </td>
    </tr>

    <tr>
      <td>
        <label for="theme-name">Theme</label>
      </td>
      <td>
        <b-form-radio
          id="theme-name"
          :options="theme_options"
          @change.native="updateTheme"
          v-model="theme_name"></b-form-radio>
      </td>
    </tr>
  </table>
</template>

<script>
import jsonp from '@/api'
import bus from '@/event-bus'

const hotkeyEventName = 'hotkey-show-app'

export default {
  name: 'general',

  created () {
    this.fetchData()
    bus.$on(hotkeyEventName, this.onHotkeySet)
  },

  beforeDestroy () {
    bus.$off(hotkeyEventName, this.onHotkeySet)
  },

  data () {
    return {
      hotkey_show_app: '',
      autostart_allowed: false,
      autostart_enabled: false,
      show_recent_apps: false,
      show_indicator_icon: false,
      theme_name: null,
      previous_theme_name: null,
      theme_options: [
        {text: 'Dark', value: 'dark'},
        {text: 'Light', value: 'light'}
      ]
    }
  },

  methods: {
    fetchData () {
      jsonp('prefs:///get/all').then((data) => {
        this.hotkey_show_app = data.hotkey_show_app
        this.autostart_allowed = data.autostart_allowed
        this.autostart_enabled = data.autostart_enabled
        this.show_recent_apps = data.show_recent_apps
        this.show_indicator_icon = data.show_indicator_icon
        this.theme_name = data.theme_name
      }, (err) => bus.$emit('error', err))
    },

    showHotkeyDialog (e) {
      jsonp('prefs://show/hotkey-dialog', {name: hotkeyEventName})
      e.target.blur()
    },

    onHotkeySet (e) {
      const previous = this.hotkey_show_app
      this.hotkey_show_app = e.displayValue
      jsonp('prefs://set/hotkey-show-app', {value: e.value}).then(null, (err) => {
        this.hotkey_show_app = previous
        bus.$emit('error', err)
      })
    },

    updateLaunchAtLogin () {
      jsonp('prefs://set/autostart-enabled', {value: this.autostart_enabled}).then(null, (err) => {
        this.autostart_enabled = !this.autostart_enabled
        bus.$emit('error', err)
      })
    },

    updateShowIndicatorIcon () {
      jsonp('prefs://set/show-indicator-icon', {value: this.show_indicator_icon}).then(null, (err) => {
        this.show_indicator_icon = !this.show_indicator_icon
        bus.$emit('error', err)
      })
    },

    updateShowRecentApps () {
      jsonp('prefs://set/show-recent-apps', {value: this.show_recent_apps}).then(null, (err) => {
        this.show_recent_apps = !this.show_recent_apps
        bus.$emit('error', err)
      })
    },

    updateTheme (e) {
      jsonp('prefs://set/theme-name', {value: this.theme_name}).then(null, (err) => {
        bus.$emit('error', err)
      })
    }

  }
}
</script>

<style scoped>
/* use tables to support WebKit on Ubuntu 14.04 */
table {
  width: 100%;
  margin: 25px 15px 15px 25px;
}
td:first-child {width: 220px;}
td {padding-bottom: 30px;}
tr:last-child td {padding-bottom: 0;}
label {cursor: pointer;}
#hotkey-show-app {
  cursor: pointer;
  width: 200px;
}
</style>
