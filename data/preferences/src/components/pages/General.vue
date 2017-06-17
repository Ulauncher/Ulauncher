<template>
<div class="page">

  <div class="form-container">

    <div class="form-group row">
      <label for="hotkey-show-app" class="col-4 col-form-label">Hotkey</label>
      <div class="col-4">
        <b-form-input id="hotkey-show-app" @focus="showHotkeyDialog" v-model="hotkey_show_app"></b-form-input>
      </div>
    </div>

    <div class="form-group row">
      <label for="autostart" class="col-4 col-form-label">Launch at Login</label>
      <div class="col-3 col-form-label">
        <b-form-checkbox
          :disabled="!autostart_allowed"
          id="autostart"
          @change="updateLaunchAtLogin"
          v-model="autostart_enabled"></b-form-checkbox>
      </div>
    </div>

    <div class="form-group row">
      <label for="show-indicator-icon" class="col-4 col-form-label">Show Indicator Icon</label>
      <div class="col-3 col-form-label">
        <b-form-checkbox
          id="show-indicator-icon"
          @change="updateShowIndicatorIcon"
          v-model="show_indicator_icon"></b-form-checkbox>
      </div>
    </div>

    <div class="form-group row">
      <label for="show-recent-apps" class="col-4 col-form-label">Show Frequent Apps</label>
      <div class="col-3 col-form-label">
        <b-form-checkbox
          id="show-recent-apps"
          @change="updateShowRecentApps"
          v-model="show_recent_apps"></b-form-checkbox>
      </div>
    </div>

    <div class="form-group row">
      <label for="theme-name" class="col-4 col-form-label">Theme</label>
      <div class="col-5 col-form-label">
        <b-form-radio
          id="theme-name"
          :options="['dark', 'light']"
          @change.native="updateTheme"
          v-model="theme_name"></b-form-radio>
      </div>
    </div>

  </div>

</div>

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
      previous_theme_name: null
    }
  },

  methods: {
    fetchData () {
      jsonp('/get/all').then((data) => {
        Object.keys(data).forEach((k) => {
          this[k] = data[k]
        })
      })
    },

    showHotkeyDialog () {
      jsonp('prefs://show/hotkey-dialog', {name: hotkeyEventName})
    },

    onHotkeySet (e) {
      const previous = this.hotkey_show_app
      this.hotkey_show_app = e.value
      jsonp('prefs://set/hotkey-show-app', {value: e.value}).then(null, (err) => {
        this.hotkey_show_app = previous
        console.error(err)
      })
    },

    updateLaunchAtLogin () {
      jsonp('prefs://set/autostart-enabled', {value: this.autostart_enabled}).then(null, (err) => {
        this.autostart_enabled = !this.autostart_enabled
        console.error(err)
      })
    },

    updateShowIndicatorIcon () {
      jsonp('prefs://set/show-indicator-icon', {value: this.show_indicator_icon}).then(null, (err) => {
        this.show_indicator_icon = !this.show_indicator_icon
        console.error(err)
      })
    },

    updateShowRecentApps () {
      jsonp('prefs://set/show-recent-apps', {value: this.show_recent_apps}).then(null, (err) => {
        this.show_recent_apps = !this.show_recent_apps
        console.error(err)
      })
    },

    updateTheme (e) {
      jsonp('prefs://set/theme-name', {value: this.theme_name}).then(null, (err) => {
        console.error(err)
      })
    }

  }
}
</script>

<style scoped>
.page {
  box-sizing: border-box;
  margin: 0 35px;
  margin: 40px;
}
.form-container {
  width: 600px;
}
label {
  cursor: pointer;
}
#hotkey-show-app {cursor: pointer;}
</style>
