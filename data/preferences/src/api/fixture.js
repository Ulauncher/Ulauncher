const placeholderImage = 'https://dummyimage.com/40x40/540154/0011ff.png'

export default function(url, params) {
  function isMatch(url, resource) {
    return url.indexOf(resource) !== -1
  }

  return new Promise(function(resolve, reject) {
    if (isMatch(url, '/get/all')) {
      console.log('/get/all')
      resolve({
        show_indicator_icon: true,
        hotkey_show_app: 'Ctrl+Alt L',
        autostart_allowed: true,
        autostart_enabled: true,
        clear_previous_text: true,
        grab_mouse_pointer: true,
        blacklisted_desktop_dirs: ['/var/tmp', '/tmp/var/log/bin/bash/root'].join(':'),
        available_themes: [{ text: 'Dark', value: 'dark' }, { text: 'Light', value: 'light' }],
        theme_name: 'light',
        is_wayland: true,
        env: {
          version: '1.2.3',
          api_version: '2.1.0',
          user_home: '/home/username'
        }
      })
    } else if (isMatch(url, '/set/show-indicator-icon')) {
      console.log('/set/show-indicator-icon', params)
      setTimeout(resolve, 0) // preventDefault doesn't work unless resolution is done in the next event loop
    } else if (isMatch(url, '/set/autostart-enabled')) {
      console.log('/set/autostart-enabled', params)
      setTimeout(resolve, 0)
    } else if (isMatch(url, '/set/show-recent-apps')) {
      console.log('/set/show-recent-apps', params)
      setTimeout(resolve, 0)
    } else if (isMatch(url, '/set/theme-name')) {
      console.log('/set/theme-name', params)
      setTimeout(resolve, 0)
    } else if (isMatch(url, '/set/hotkey-show-app')) {
      console.log('/set/hotkey-show-app', params)
      setTimeout(resolve, 0)
    } else if (isMatch(url, '/set/clear-previous-query')) {
      console.log('/set/clear-previous-query', params)
      setTimeout(resolve, 0)
    } else if (isMatch(url, '/set/grab-mouse-pointer')) {
      console.log('/set/grab-mouse-pointer', params)
      setTimeout(resolve, 0)
    } else if (isMatch(url, '/set/blacklisted-desktop-dirs')) {
      console.log('/set/blacklisted-desktop-dirs', params)
      setTimeout(resolve, 0)
    } else if (isMatch(url, '/open/web-url')) {
      console.log('/open/web-url', params)
      setTimeout(resolve, 0)
    } else if (isMatch(url, '/show/hotkey-dialog')) {
      console.log('/show/hotkey-dialog', params)
      setTimeout(resolve, 0)
      setTimeout(function() {
        window.onNotification(params.name, { displayValue: 'Ctrl+Alt+Space', value: '<Ctrl>+<Alt>+<Space>' })
      }, 300)
    } else if (isMatch(url, '/show/file-browser')) {
      console.log('/show/file-browser', params)
      setTimeout(resolve, 0)
      setTimeout(function() {
        window.onNotification(params.name, { value: placeholderImage })
      }, 500)
    } else if (isMatch(url, '/shortcut/get-all')) {
      console.log('/shortcut/get-all', params)
      setTimeout(function() {
        resolve(_getShortcuts())
      }, 0)
    } else if (isMatch(url, '/shortcut/update')) {
      console.log('/shortcut/update', params)
      setTimeout(resolve, 0)
    } else if (isMatch(url, '/shortcut/remove')) {
      console.log('/shortcut/remove', params)
      setTimeout(resolve, 0)
    } else if (isMatch(url, '/shortcut/add')) {
      console.log('/shortcut/add', params)
      setTimeout(function() {
        resolve({ ...params, id: 'new-id-832923742' })
      }, 0)
    } else if (isMatch(url, '/extension/get-all')) {
      console.log('/extension/get-all', params)
      setTimeout(function() {
        // reject({
        //   message: 'Something went wrong',
        //   type: 'Exception',
        //   errorName: 'UnhandledError',
        //   stacktrace:
        //     'Traceback (most recent call last):\n  File "PreferencesUlauncherDialog.py", line 192, in on_scheme_callback\n    resp = rt.dispatch...'
        // })
        resolve(_getExtensions())
      }, 0)
    } else if (isMatch(url, '/extension/update-prefs')) {
      console.log('/extension/update-prefs', params)
      setTimeout(resolve, 0)
    } else if (isMatch(url, '/extension/update-ext')) {
      console.log('/extension/update-ext', params)
      setTimeout(resolve, 1e3)
    } else if (isMatch(url, '/extension/check-updates')) {
      console.log('/extension/check-updates', params)
      setTimeout(() => {
        if (Math.random() > 0.75) {
          reject({
            message: 'Could not find versions.json file using URL "https://raw.githubusercontent.com/Ulauncher/ulauncher-kill/master/versions.json"',
            type: 'GithubExtensionError',
            errorName: 'VersionsJsonNotFound',
            stacktrace: 'Traceback (most recent call last):\n  File "ulauncher/ulauncher/api/server/GithubExtension.py", line 101, in _read_json\n    return json.loads(urlopen(url).read().decode(\'utf-8\'))\n  File "request.py", line 223, in urlopen\n    return opener.open(url, data, timeout)'
          })
        } else {
          resolve(Math.random() > 0.5 ? {
            last_commit: '64e106cawef23f2q332',
            last_commit_time: '2017-05-01T07:30:39Z'
          } : null)
        }
      }, 300)
    } else if (isMatch(url, '/extension/add')) {
      console.log('/extension/add', params)
      setTimeout(() => {
        if (params.url.includes('reject')) {
          reject({
            message: 'Could not load extension',
            errorName: 'UnexpectedError',
            stacktrace: 'stacktrace\nabc\nxyz',
            type: 'ClassName'
          })
          return
        }
        resolve([..._getExtensions(), generateExtensionRecord('ext.newext', 'NewExt', 2, params.url)])
      }, 300)
    } else if (isMatch(url, '/extension/remove')) {
      console.log('/extension/remove', params)
      setTimeout(resolve, 0)
    } else if (isMatch(url, '/close')) {
      console.log('/close')
    } else {
      reject({ message: `Unknown URL "${url}"` })
    }
  })
}

function _getExtensions() {
  return [
    generateExtensionRecord({
      extId: 'ext.custom',
      name: 'Extension without URL and with a very long name',
      numOfPrefs: 2,
      url: null
    }),
    generateExtensionRecord({
      extId: 'ext.timer',
      name: 'Just a regular one'
    }),
    generateExtensionRecord({
      extId: 'ext.dict',
      name: 'Without preferences',
      numOfPrefs: 0
    }),
    generateExtensionRecord({
      extId: 'ext.stopped',
      name: 'Stopped because of --no-extensions flag',
      isRunning: false,
      runtimeError: {
        name: 'NoExtensionsFlag',
        message: 'bash exec /file --no-things abc | script > null /python/path/env/var EXEC_ONLY=true /bin/bash ulauncher'
      }
    }),
    generateExtensionRecord({
      extId: 'ext.crashed',
      name: 'Crashed on start',
      isRunning: false,
      runtimeError: {
        name: 'ExitedInstantly',
        message: 'Extension "ext.crashed" exited instantly with code 123'
      }
    }),
    generateExtensionRecord({
      extId: 'ext.witherror',
      name: 'Manifest validation error',
      numOfPrefs: 0,
      error: {
        message: "'required_api_version' is not provided",
        errorName: 'InvalidManifestJson'
      }
    })
  ]
}

function generateExtensionRecord(config) {
  let prefs = [
    {
      id: 'keyword',
      type: 'keyword',
      name: 'My Timer',
      default_value: 'ti',
      user_value: 't',
      value: 't'
    },
    {
      id: 'max',
      type: 'input',
      name: 'Max Number of Posts',
      default_value: '5',
      description: 'This is description',
      user_value: null,
      value: '5'
    },
    {
      id: 'size',
      type: 'select',
      name: 'Size',
      default_value: 'M',
      description: 'This is description',
      user_value: null,
      options: ['S', 'M', 'L', 'XL'],
      value: 'M'
    },
    {
      id: 'default_msg',
      type: 'text',
      name: 'Default Message',
      default_value: '',
      description: 'Should open link in browser <a href="https://example.com">here</a>',
      user_value: 'Hello Steve!',
      value: 'Hello Steve!'
    }
  ]
  prefs.length = config.numOfPrefs !== undefined ? config.numOfPrefs : 4

  return {
    id: config.extId,
    url: config.url || 'https://github.com/ulauncher/ulauncher-demo-ext',
    name: config.name,
    updated_at: '2017-07-21T20:50:44.850738',
    icon: placeholderImage,
    description: 'My extension description',
    developer_name: 'John Doe',
    version: '1.2.3',
    last_commit: 'abc234fd23425234a2',
    last_commit_time: '2017-07-21T20:50:44',
    preferences: prefs,
    error: config.error,
    is_running: config.isRunning !== undefined ? config.isRunning : true,
    runtime_error: config.runtimeError
  }
}

function _getShortcuts() {
  return [
    {
      id: '1ad51010-04ee-44fc-81c4-ed6fb72cbf19',
      icon: null,
      name: 'Looooooong naaaaaaaaaaaaaaame',
      keyword: 'g',
      cmd: 'http://github.com/search?q=%s',
      is_default_search: true
    },
    {
      id: '2ad51010-04ee-44fc-81c4-ed6fb72cbf19',
      icon: '~/Downloads/favicon.ico',
      name: 'gismeteo.ua',
      keyword: 'gismeteo.ua',
      cmd: 'http://www.gismeteo.ua/city/?gis20141120102952990=%s&sedddddddddddddddddddarchQueryData=%2758175%27'
    },
    {
      id: '3ad51010-04ee-44fc-81c4-ed6fb72cbf19',
      icon: placeholderImage,
      name: 'Google Maps',
      keyword: 'maps',
      cmd: 'https://www.google.com.ua/maps/search/%s?hl=en&source=opensearch',
      is_default_search: true
    },
    {
      id: '4ad51010-04ee-44fc-81c4-ed6fb72cbf19',
      icon: placeholderImage,
      name: 'Google Play',
      keyword: 'play',
      cmd: 'https://play.google.com/store/search?q=%s&utm_source=opensearch',
      is_default_search: true
    },
    {
      id: '5ad51010-04ee-44fc-81c4-ed6fb72cbf19',
      icon: placeholderImage,
      name: 'Gihub',
      keyword: 'g',
      cmd: 'http://github.com/search?q=%s'
    },
    {
      id: '6ad51010-04ee-44fc-81c4-ed6fb72cbf19',
      icon: placeholderImage,
      name: 'gismeteo.ua',
      keyword: 'gismeteo.ua',
      cmd: 'http://www.gismeteo.ua/city/?gis20141120102952990=%s&searchQueryData=%2758175%27'
    },
    {
      id: '7ad51010-04ee-44fc-81c4-ed6fb72cbf19',
      icon: placeholderImage,
      name: 'Google Maps',
      keyword: 'maps',
      cmd: 'https://www.google.com.ua/maps/search/%s?hl=en&source=opensearch'
    },
    {
      id: '8ad51010-04ee-44fc-81c4-ed6fb72cbf19',
      icon: placeholderImage,
      name: 'Google Play',
      keyword: 'play',
      cmd: 'https://play.google.com/store/search?q=%s&utm_source=opensearch'
    },
    {
      id: '9ad51010-04ee-44fc-81c4-ed6fb72cbf19',
      icon: placeholderImage,
      name: 'Gihub',
      keyword: 'g',
      cmd: 'http://github.com/search?q=%s'
    },
    {
      id: '0ad51010-04ee-44fc-81c4-ed6fb72cbf19',
      icon: placeholderImage,
      name: 'gismeteo.ua',
      keyword: 'gismeteo.ua',
      cmd: 'http://www.gismeteo.ua/city/?gis20141120102952990=%s&searchQueryData=%2758175%27'
    },
    {
      id: 'aad51010-04ee-44fc-81c4-ed6fb72cbf19',
      icon: placeholderImage,
      name: 'Google Maps',
      keyword: 'maps',
      cmd: 'https://www.google.com.ua/maps/search/%s?hl=en&source=opensearch'
    },
    {
      id: 'bad51010-04ee-44fc-81c4-ed6fb72cbf19',
      icon: placeholderImage,
      name: 'Google Play',
      keyword: 'play',
      cmd: 'https://play.google.com/store/search?q=%s&utm_source=opensearch'
    },
    {
      id: 'cad51010-04ee-44fc-81c4-ed6fb72cbf19',
      icon: placeholderImage,
      name: 'Gihub',
      keyword: 'g',
      cmd: 'http://github.com/search?q=%s'
    },
    {
      id: 'dad51010-04ee-44fc-81c4-ed6fb72cbf19',
      icon: placeholderImage,
      name: 'gismeteo.ua',
      keyword: 'gismeteo.ua',
      cmd: 'http://www.gismeteo.ua/city/?gis20141120102952990=%s&searchQueryData=%2758175%27'
    },
    {
      id: 'ead51010-04ee-44fc-81c4-ed6fb72cbf19',
      icon: placeholderImage,
      name: 'Google Maps',
      keyword: 'maps',
      cmd: 'https://www.google.com.ua/maps/search/%s?hl=en&source=opensearch'
    },
    {
      id: 'fad51010-04ee-44fc-81c4-ed6fb72cbf19',
      icon: placeholderImage,
      name: 'Google Play',
      keyword: 'play',
      cmd: 'https://play.google.com/store/search?q=%s&utm_source=opensearch'
    }
  ]
}
