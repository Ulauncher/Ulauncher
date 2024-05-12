<template>
  <div v-if="prefsLoaded">
    <h1>General</h1>

    <table>
      <tr>
        <td>
          <label for="autostart">Launch at login</label>
          <small v-if="daemonless">
            <p>Enabling this will disable the "Daemonless mode" option.</p>
          </small>
        </td>
        <td>
          <b-form-checkbox
            :disabled="!prefs.env.autostart_allowed"
            id="autostart"
            v-model="autostart_enabled"
          ></b-form-checkbox>
        </td>
      </tr>

      <tr>
        <td>
          <label for="hotkey-show-app">Hotkey</label>
        </td>
        <td>
          <b-button variant="secondary" @click="showHotkeyDialog" v-if="prefs.env.hotkey_supported">Set hotkey</b-button>
          <div v-if="!prefs.env.hotkey_supported" class="compat-warning">
            <b-alert show variant="warning small">
              Ulauncher doesn't support setting global shortcuts for your desktop environment.<br/>
              If you haven't already done so, we strongly advice that you manually add a global shortcut 
              in your desktop environment settings, or using a third party service.<br/>
              Bind it to this command:
              <code>gapplication launch io.ulauncher.Ulauncher</code>
              <b-button size="sm" v-clipboard:copy="'gapplication launch io.ulauncher.Ulauncher'" title="Copy">
                <i class="fa fa-copy"></i>
              </b-button>
            </b-alert>
          </div>
        </td>
      </tr>

      <tr>
        <td>
          <label for="theme-name">Color theme</label>
        </td>
        <td>
          <b-form-select style="min-width:380px"
            id="theme-name"
            class="theme-select"
            :options="prefs.available_themes"
            v-model="theme_name"
          ></b-form-select>
        </td>
      </tr>

      <tr>
        <td>
          <label for="render-on-screen">Screen to show on</label>
        </td>
        <td>
          <b-form-select style="min-width:380px"
            id="render-on-screen"
            class="render-on-screen-select"
            :options="renderOnScreenOptions"
            v-model="render_on_screen"
          ></b-form-select>
        </td>
      </tr>

      <tr>
        <td>
          <label for="clear_previous_query">Start each session with a blank query</label>
        </td>
        <td>
          <b-form-checkbox id="clear_previous_query" v-model="clear_previous_query"></b-form-checkbox>
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

    <h1>Applications</h1>
    <table>
      <tr>
        <td>
          <label for="enable_application_mode">Include applications in search</label>
          <small>
            <p>Disable if you only want to use Ulauncher for shortcuts and extensions</p>
          </small>
        </td>
        <td>
          <b-form-checkbox id="enable_application_mode" v-model="enable_application_mode"></b-form-checkbox>
        </td>
      </tr>

      <tr>
        <td>
          <label for="raise-if-started">Switch to application if it's already running</label>
        </td>
        <td>
          <b-form-checkbox id="raise-if-started" v-model="raise_if_started"></b-form-checkbox>
          <div v-if="!prefs.env.is_x11" class="compat-warning">
            <b-alert show variant="warning">
              <small>
                This feature can only be supported with the X11 Display Server, but you are using Wayland.
              </small>
            </b-alert>
          </div>
        </td>
      </tr>

      <tr>
        <td>
          <label for="base-width">Window width</label>
          <small>
            <p>Window width (in pixels). Min: 540, Max: 2000</p>
          </small>
        </td>
        <td>
          <b-form-input style="width:380px" id="base-width" v-model.number="base_width" type="number" min="540" max="2000"></b-form-input>
        </td>
      </tr>

      <tr>
        <td>
          <label for="show-recent-apps">Number of frequent apps to show</label>
        </td>
        <td>
          <b-form-input style="width:380px" id="show-recent-apps" v-model.number="max_recent_apps" type="number" min="0"></b-form-input>
        </td>
      </tr>
    </table>

    <h1>Advanced</h1>

    <table>
      <tr>
        <td>
          <label for="show-tray-icon">Show tray icon</label>
          <small>
            <p>Requires optional dependency XApp (recommended), AppIndicator3 or AyatanaAppindicator3</p>
          </small>
        </td>
        <td>
          <b-form-checkbox id="show-tray-icon" v-model="show_tray_icon"></b-form-checkbox>
        </td>
      </tr>

      <tr>
        <td>
          <label for="disable-desktop-filters">Show all apps</label>
          <small>
            <p>
              Display all applications, even if they are configured to not show in the current desktop environment.
            </p>
          </small>
        </td>
        <td>
          <b-form-checkbox id="disable-desktop-filters" v-model="disable_desktop_filters"></b-form-checkbox>
        </td>
      </tr>

      <tr>
        <td>
          <label for="daemonless">Daemonless mode</label>
          <small>
            <p>Prevents keeping Ulauncher running in the background. Beware that this mode comes with some caveats and is not recommended. <a href="#" @click="openUrlInBrowser('https://github.com/Ulauncher/Ulauncher/discussions/1388')">Read more here</a>.</p>
            <p v-if="autostart_enabled">Enabling this will disable "Launch at login".</p>
          </small>
        </td>
        <td>
          <b-form-checkbox id="daemonless" v-model="daemonless"></b-form-checkbox>
        </td>
      </tr>

      <tr>
        <td>
          <label for="jump-keys">Jump keys</label>
          <small>
            <p>Set the keys to use for quickly jumping to results</p>
          </small>
        </td>
        <td>
          <b-form-input style="width:500px" id="jump-keys" v-model="jump_keys"></b-form-input>
        </td>
      </tr>

      <tr>
        <td>
          <label for="terminal-exec">Terminal command</label>
          <small>
            <p>
              Overrides terminal for apps that are configured to be run from a terminal.
              Set to an empty value for default terminal
            </p>
          </small>
        </td>
        <td>
          <b-form-input style="width:500px" id="terminal-exec" v-model="terminal_command"></b-form-input>
        </td>
      </tr>
    </table>
  </div>
</template>

<script>
import { mapState, mapMutations, mapGetters } from 'vuex'

import fetchData from '@/fetchData'
import bus from '@/event-bus'

export default {
  name: 'preferences',

  data() {
    return {
      changed : {},
      renderOnScreenOptions: [
        { value: 'mouse-pointer-monitor', text: 'The screen with the mouse pointer' },
        { value: 'default-monitor', text: 'The default screen' },
      ]
    }
  },

  computed: {
    ...mapState(['prefs']),
    ...mapGetters(['prefsLoaded']),
    // Generate getters/setters for all preferences that are just storing to the config file
    // Unfortunately there seems to be no way to generate these from the backend data,
    // as we haven't recievened it yet at this point in the runtime
    // A more reasonable approach would probably be to use a wrapper rather than directly accessing these
    // As in v-model="prefs.max_recent_apps" instead of v-model="max_recent_apps"?
    ...Object.fromEntries([
      'autostart_enabled',
      'clear_previous_query',
      'disable_desktop_filters',
      'grab_mouse_pointer',
      'jump_keys',
      'base_width',
      'enable_application_mode',
      'raise_if_started',
      'render_on_screen',
      'show_tray_icon',
      'max_recent_apps',
      'daemonless',
      'terminal_command',
      'theme_name',
    ].map(name => ([name, {
      get() {
        return this.prefs[name]
      },
      set(value) {
        if (value && name === "daemonless") {
          this.autostart_enabled = false;
        } else if (value && name === "autostart_enabled") {
          this.daemonless = false;
        } else if (name === "max_recent_apps") {
          value = parseInt(value, 10) || 0 // WebkitGtk doesn't support input[type=number] for some strange reason
        } else if (name === 'base_width' && (value < 540 || value > 2000)) {
          return
        }
        return fetchData('prefs:///set', name, value).then(
          () => {
            this.setPrefs({[name]: value})
            this.changed[name] = true
          },
          err => bus.$emit('error', err)
        )
      }
    }]))),
  },

  methods: {
    ...mapMutations(['setPrefs']),

    openUrlInBrowser(url) {
      fetchData('prefs:///open/web-url', url)
    },

    showHotkeyDialog() {
      fetchData('prefs:///show/hotkey-dialog')
    },
  }
}
</script>

<style lang="css" scoped>
/* use tables to support WebKit on Ubuntu 14.04 */
table {
  width: 100%;
  margin: 25px 15px 15px 40px;
}
h1 {
  margin: 30px 0 0 25px;
  font-size: 110%;
  color: #aaa;
  text-shadow: 1px 1px 1px #fff;
}
td:first-child {
  box-sizing: border-box;
  width: 260px;
  padding-right: 30px;
}
td {
  vertical-align: top;
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
.compat-warning {
  width: 550px;
}
.compat-warning .alert {
  margin: 10px 0 0 0;
  padding: 0.4em 0.7em;
}
.compat-warning .alert button {
  font-size: 0.75rem;
  padding: 0 4px;
}
.theme-select,
.render-on-screen-select {
  width: auto;
}
</style>
