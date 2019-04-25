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
        blacklisted_desktop_dirs: ['/var/tmp', '/tmp/var/log/bin/bash/root'].join(':'),
        available_themes: [{ text: 'Dark', value: 'dark' }, { text: 'Light', value: 'light' }],
        theme_name: 'light',
        is_wayland: true,
        env: {
          version: '1.2.3',
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
        window.onNotification(params.name, { value: `https://placeholdit.imgix.net/~text?txt=Icon&w=80&h=80` })
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
        resolve(Math.random() > 0.5 ? {
          last_commit: '64e106cawef23f2q332',
          last_commit_time: '2017-05-01T07:30:39Z'
        } : null)
      }, 1e3)
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
      reject(`Unknown URL "${url}"`)
    }
  })
}

function _getExtensions() {
  return [
    generateExtensionRecord('ext.custom', 'Very Very Very Very Long Extension Name', 2, null),
    generateExtensionRecord('ext.timer', 'Timer'),
    generateExtensionRecord('ext.dict', 'Dictionary', 0)
  ]
}

function generateExtensionRecord(extId, name, numOfPrefs = 4, url = 'https://github.com/ulauncher/ulauncher-demo-ext') {
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
      description: 'This is description',
      user_value: 'Hello Steve!',
      value: 'Hello Steve!'
    }
  ]
  prefs.length = numOfPrefs

  return {
    id: extId,
    url: url,
    name: name,
    updated_at: '2017-07-21T20:50:44.850738',
    icon: 'https://assets-cdn.github.com/favicon.ico',
    description: 'My extension description',
    developer_name: 'John Doe',
    version: '1.2.3',
    last_commit: 'abc234fd23425234a2',
    last_commit_time: '2017-07-21T20:50:44',
    preferences: prefs
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
      icon: 'https://assets-cdn.github.com/favicon.ico',
      name: 'Google Maps',
      keyword: 'maps',
      cmd: 'https://www.google.com.ua/maps/search/%s?hl=en&source=opensearch',
      is_default_search: true
    },
    {
      id: '4ad51010-04ee-44fc-81c4-ed6fb72cbf19',
      icon: 'https://assets-cdn.github.com/favicon.ico',
      name: 'Google Play',
      keyword: 'play',
      cmd: 'https://play.google.com/store/search?q=%s&utm_source=opensearch',
      is_default_search: true
    },
    {
      id: '5ad51010-04ee-44fc-81c4-ed6fb72cbf19',
      icon: 'https://assets-cdn.github.com/favicon.ico',
      name: 'Gihub',
      keyword: 'g',
      cmd: 'http://github.com/search?q=%s'
    },
    {
      id: '6ad51010-04ee-44fc-81c4-ed6fb72cbf19',
      icon: 'https://assets-cdn.github.com/favicon.ico',
      name: 'gismeteo.ua',
      keyword: 'gismeteo.ua',
      cmd: 'http://www.gismeteo.ua/city/?gis20141120102952990=%s&searchQueryData=%2758175%27'
    },
    {
      id: '7ad51010-04ee-44fc-81c4-ed6fb72cbf19',
      icon: 'https://assets-cdn.github.com/favicon.ico',
      name: 'Google Maps',
      keyword: 'maps',
      cmd: 'https://www.google.com.ua/maps/search/%s?hl=en&source=opensearch'
    },
    {
      id: '8ad51010-04ee-44fc-81c4-ed6fb72cbf19',
      icon: 'https://assets-cdn.github.com/favicon.ico',
      name: 'Google Play',
      keyword: 'play',
      cmd: 'https://play.google.com/store/search?q=%s&utm_source=opensearch'
    },
    {
      id: '9ad51010-04ee-44fc-81c4-ed6fb72cbf19',
      icon: 'https://assets-cdn.github.com/favicon.ico',
      name: 'Gihub',
      keyword: 'g',
      cmd: 'http://github.com/search?q=%s'
    },
    {
      id: '0ad51010-04ee-44fc-81c4-ed6fb72cbf19',
      icon: 'https://assets-cdn.github.com/favicon.ico',
      name: 'gismeteo.ua',
      keyword: 'gismeteo.ua',
      cmd: 'http://www.gismeteo.ua/city/?gis20141120102952990=%s&searchQueryData=%2758175%27'
    },
    {
      id: 'aad51010-04ee-44fc-81c4-ed6fb72cbf19',
      icon: 'https://assets-cdn.github.com/favicon.ico',
      name: 'Google Maps',
      keyword: 'maps',
      cmd: 'https://www.google.com.ua/maps/search/%s?hl=en&source=opensearch'
    },
    {
      id: 'bad51010-04ee-44fc-81c4-ed6fb72cbf19',
      icon: 'https://assets-cdn.github.com/favicon.ico',
      name: 'Google Play',
      keyword: 'play',
      cmd: 'https://play.google.com/store/search?q=%s&utm_source=opensearch'
    },
    {
      id: 'cad51010-04ee-44fc-81c4-ed6fb72cbf19',
      icon: 'https://assets-cdn.github.com/favicon.ico',
      name: 'Gihub',
      keyword: 'g',
      cmd: 'http://github.com/search?q=%s'
    },
    {
      id: 'dad51010-04ee-44fc-81c4-ed6fb72cbf19',
      icon: 'https://assets-cdn.github.com/favicon.ico',
      name: 'gismeteo.ua',
      keyword: 'gismeteo.ua',
      cmd: 'http://www.gismeteo.ua/city/?gis20141120102952990=%s&searchQueryData=%2758175%27'
    },
    {
      id: 'ead51010-04ee-44fc-81c4-ed6fb72cbf19',
      icon: 'https://assets-cdn.github.com/favicon.ico',
      name: 'Google Maps',
      keyword: 'maps',
      cmd: 'https://www.google.com.ua/maps/search/%s?hl=en&source=opensearch'
    },
    {
      id: 'fad51010-04ee-44fc-81c4-ed6fb72cbf19',
      icon: 'https://assets-cdn.github.com/favicon.ico',
      name: 'Google Play',
      keyword: 'play',
      cmd: 'https://play.google.com/store/search?q=%s&utm_source=opensearch'
    }
  ]
}
