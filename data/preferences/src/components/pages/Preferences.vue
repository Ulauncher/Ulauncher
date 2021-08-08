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
          <div v-if="prefs.is_wayland" class="hotkey-warning">
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
          <label>Blacklisted App Dirs</label>
          <small>
            <p>Ulauncher won't search for .desktop files in these dirs</p>
            <p v-if="blacklistedDirsChanged">
              <i class="fa fa-warning"></i> Restart Ulauncher for this to take effect
            </p>
          </small>
        </td>
        <td class="pull-top">
          <editable-text-list
            width="450px"
            v-model="blacklisted_desktop_dirs"
            newItemPlaceholder="Type in an absolute path and press Enter"
          ></editable-text-list>
        </td>
      </tr>
    </table>
  </div>
</template>

<script>
import { mapState, mapMutations, mapGetters } from 'vuex'

import jsonp from '@/api'
import bus from '@/event-bus'
import EditableTextList from '@/components/widgets/EditableTextList'

const hotkeyEventName = 'hotkey-show-app'

export default {
  name: 'preferences',

  components: {
    'editable-text-list': EditableTextList
  },

  created() {
    bus.$on(hotkeyEventName, this.onHotkeySet)
  },

  beforeDestroy() {
    bus.$off(hotkeyEventName, this.onHotkeySet)
  },

  data() {
    return {
      previous_theme_name: null,
      blacklistedDirsChanged: false,
      renderOnScreenOptions: {
        'mouse-pointer-monitor': 'Monitor with a mouse pointer',
        'default-monitor': 'Default monitor'
      }
    }
  },

  computed: {
    ...mapState(['prefs']),

    ...mapGetters(['prefsLoaded']),

    autostart_enabled: {
      get() {
        return this.prefs.autostart_enabled
      },
      set(value) {
        return jsonp('prefs://set/autostart-enabled', { value: value }).then(
          () => this.setPrefs({ autostart_enabled: value }),
          err => bus.$emit('error', err)
        )
      }
    },

    show_indicator_icon: {
      get() {
        return this.prefs.show_indicator_icon
      },
      set(value) {
        return jsonp('prefs://set/show-indicator-icon', { value: value }).then(
          () => this.setPrefs({ show_indicator_icon: value }),
          err => bus.$emit('error', err)
        )
      }
    },

    show_recent_apps: {
      get() {
        if (this.prefs.show_recent_apps === true) {
          return '3'
        } else if (this.prefs.show_recent_apps === false) {
          return '0'
        }
        return this.prefs.show_recent_apps
      },
      set(value) {
        return jsonp('prefs://set/show-recent-apps', { value: value }).then(
          () => this.setPrefs({ show_recent_apps: value }),
          err => bus.$emit('error', err)
        )
      }
    },

    terminal_command: {
      get() {
        return this.prefs.terminal_command
      },
      set(value) {
        return jsonp('prefs://set/terminal-command', { value: value }).then(
          () => this.setPrefs({ terminal_command: value }),
          err => bus.$emit('error', err)
        )
      }
    },

    theme_name: {
      get() {
        return this.prefs.theme_name
      },
      set(value) {
        return jsonp('prefs://set/theme-name', { value: value }).then(
          () => this.setPrefs({ theme_name: value }),
          err => bus.$emit('error', err)
        )
      }
    },

    clear_previous_query: {
      get() {
        return this.prefs.clear_previous_query
      },
      set(value) {
        return jsonp('prefs://set/clear-previous-query', { value: value }).then(
          () => this.setPrefs({ clear_previous_query: value }),
          err => bus.$emit('error', err)
        )
      }
    },

    grab_mouse_pointer: {
      get() {
        return this.prefs.grab_mouse_pointer
      },
      set(value) {
        return jsonp('prefs://set/grab-mouse-pointer', { value: value }).then(
          () => this.setPrefs({ grab_mouse_pointer: value }),
          err => bus.$emit('error', err)
        )
      }
    },

    blacklisted_desktop_dirs: {
      get() {
        return this.prefs.blacklisted_desktop_dirs
      },
      set(value) {
        return jsonp('prefs://set/blacklisted-desktop-dirs', { value: value.join(':') }).then(
          () => {
            this.setPrefs({ blacklisted_desktop_dirs: value })
            this.blacklistedDirsChanged = true
          },
          err => bus.$emit('error', err)
        )
      }
    },

    render_on_screen: {
      get() {
        return this.prefs.render_on_screen
      },
      set(value) {
        return jsonp('prefs://set/render-on-screen', { value: value }).then(
          () => this.setPrefs({ render_on_screen: value }),
          err => bus.$emit('error', err)
        )
      }
    }
  },

  methods: {
    ...mapMutations(['setPrefs']),

    openUrlInBrowser(url) {
      jsonp('prefs://open/web-url', { url: url })
    },

    showHotkeyDialog(e) {
      jsonp('prefs://show/hotkey-dialog', { name: hotkeyEventName })
      e.target.blur()
    },

    onHotkeySet(e) {
      jsonp('prefs://set/hotkey-show-app', { value: e.value }).then(
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
