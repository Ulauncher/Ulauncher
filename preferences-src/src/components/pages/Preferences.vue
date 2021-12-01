<template>
  <div v-if="prefsLoaded">
    <h1>General</h1>

    <table>
      <tr>
        <td>
          <label for="hotkey-show-app">Hotkey</label>
        </td>
        <td>
          <b-form-input
            id="hotkey-show-app"
            @focus.native="showHotkeyDialog($event)"
            :value="prefs.hotkey_show_app"
          ></b-form-input>
          <div v-if="prefs.env.is_wayland" class="hotkey-warning">
            <b-alert show variant="warning">
              <small>
                It appears that your are in Wayland session.
                This hotkey may not work all the time.
                <br />Check
                <a
                  href
                  @click.prevent="openUrlInBrowser('https://github.com/Ulauncher/Ulauncher/wiki/Hotkey-In-Wayland')"
                >this</a>
                to get better user experience
              </small>
            </b-alert>
          </div>
        </td>
      </tr>

      <tr>
        <td>
          <label for="theme-name">Color Theme</label>
        </td>
        <td>
          <b-form-select
            id="theme-name"
            class="theme-select"
            :options="prefs.available_themes"
            v-model="theme_name"
          ></b-form-select>
        </td>
      </tr>

      <tr>
        <td>
          <label for="autostart">Launch at Login</label>
        </td>
        <td>
          <b-form-checkbox
            :disabled="!prefs.autostart_allowed"
            id="autostart"
            v-model="autostart_enabled"
          ></b-form-checkbox>
        </td>
      </tr>

      <tr>
        <td>
          <label for="show-recent-apps">Number of frequent apps to show</label>
        </td>
        <td>
          <b-form-input style="width:250px" id="show-recent-apps" v-model="show_recent_apps"></b-form-input>
        </td>
      </tr>

      <tr>
        <td>
          <label for="clear_previous_query">Clear Input on Hide</label>
        </td>
        <td>
          <b-form-checkbox id="clear_previous_query" v-model="clear_previous_query"></b-form-checkbox>
        </td>
      </tr>

      <tr>
        <td>
          <label for="render-on-screen">Render On</label>
        </td>
        <td>
          <b-form-select
            id="render-on-screen"
            class="render-on-screen-select"
            :options="renderOnScreenOptions"
            v-model="render_on_screen"
          ></b-form-select>
        </td>
      </tr>

      <tr>
        <td>
          <label for="grab_mouse_pointer">Don't hide after losing mouse focus</label>
        </td>
        <td>
          <b-form-checkbox id="grab_mouse_pointer" v-model="grab_mouse_pointer"></b-form-checkbox>
        </td>
      </tr>
    </table>

    <h1>Advanced</h1>

    <table>
      <tr>
        <td>
          <label for="show-indicator-icon">Show Indicator Icon</label>
          <small>
            <p>It's supported only if gir1.2-ayatanaappindicator3-0.1 or an equivalent is installed</p>
          </small>
        </td>
        <td>
          <b-form-checkbox id="show-indicator-icon" v-model="show_indicator_icon"></b-form-checkbox>
        </td>
      </tr>

      <tr>
        <td>
          <label for="terminal-exec">Terminal Command</label>
          <small>
            <p>
              Overrides terminal for apps that are configured to be run from a terminal.
              Set to an empty value for default terminal
            </p>
          </small>
        </td>
        <td>
          <b-form-input style="width:250px" id="terminal-exec" v-model="terminal_command"></b-form-input>
        </td>
      </tr>
      <tr>
        <td class="pull-top">
          <label for="disable-desktop-filters">Show All Apps</label>
          <small>
            <p>
              Display all applications, even if they are configured to not show in the current desktop environment.
            </p>
          </small>
        </td>
        <td class="pull-top">
          <b-form-checkbox id="disable-desktop-filters" v-model="disable_desktop_filters"></b-form-checkbox>
        </td>
      </tr>
    </table>
  </div>
</template>

<script>
import { mapState, mapMutations, mapGetters } from 'vuex'

import jsonp from '@/api'
import bus from '@/event-bus'

const hotkeyEventName = 'hotkey-show-app'

export default {
  name: 'preferences',

  created() {
    bus.$on(hotkeyEventName, this.onHotkeySet)
  },

  beforeDestroy() {
    bus.$off(hotkeyEventName, this.onHotkeySet)
  },

  data() {
    return {
      renderOnScreenOptions: {
        'mouse-pointer-monitor': 'Monitor with a mouse pointer',
        'default-monitor': 'Default monitor'
      }
    }
  },

  computed: {
    ...mapState(['prefs']),
    ...mapGetters(['prefsLoaded']),
    // Generate getters/setters for all preferences that are just storing to the config file
    // Unfortunately there seems to be no way to generate these from the backend data,
    // as we haven't recievened it yet at this point in the runtime
    // A more reasonable approach would probably be to use a wrapper rather than directly accessing these
    // As in v-model="prefs.show_recent_apps" instead of v-model="show_recent_apps"?
    ...Object.fromEntries([
      'autostart_enabled',
      'clear_previous_query',
      'disable_desktop_filters',
      'grab_mouse_pointer',
      'render_on_screen',
      'show_indicator_icon',
      'show_recent_apps',
      'terminal_command',
      'theme_name',
    ].map(name => ([name, {
      get() {
        return this.prefs[name]
      },
      set(value) {
        return jsonp('prefs:///set', {property: name.replace('_', '-'), value}).then(
          () => this.setPrefs({[name]: value}),
          err => bus.$emit('error', err)
        )
      }
    }]))),
  },

  methods: {
    ...mapMutations(['setPrefs']),

    openUrlInBrowser(url) {
      jsonp('prefs:///open/web-url', { url: url })
    },

    showHotkeyDialog(e) {
      jsonp('prefs:///show/hotkey-dialog', { name: hotkeyEventName })
      e.target.blur()
    },

    onHotkeySet(e) {
      jsonp('prefs:///set/hotkey-show-app', { value: e.value }).then(
        () => this.setPrefs({ hotkey_show_app: e.displayValue }),
        err => bus.$emit('error', err)
      )
    }
  }
}
</script>

<style lang="css" scoped>
/* use tables to support WebKit on Ubuntu 14.04 */
table {
  width: 100%;
  margin: 25px 15px 15px 40px;
}
.pull-top {
  vertical-align: top;
}
h1 {
  margin: 30px 0 0 25px;
  font-size: 110%;
  color: #aaa;
  text-shadow: 1px 1px 1px #fff;
}
td:first-child {
  box-sizing: border-box;
  width: 220px;
  padding-right: 20px;
}
td {
  padding-bottom: 20px;
}
tr:last-child td {
  padding-bottom: 0;
}
label {
  cursor: pointer;
}
label + small {
    position: relative;
    top: -5px;
    line-height: 1.3em;
    display: block;
    color: #888;
}
#hotkey-show-app {
  cursor: pointer;
  width: 200px;
}
.hotkey-warning {
  width: 550px;
}
.hotkey-warning .alert {
  margin: 10px 0 0 0;
  padding: 0.4em 0.7em;
  line-height: 95%;
}
.theme-select,
.render-on-screen-select {
  width: auto;
}
</style>
