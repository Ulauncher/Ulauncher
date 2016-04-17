if (window.location.href.indexOf('browser') != -1) {
  // debugging in a browser with fixtures if URL has 'browser'

  window.jsonp = function (url, params) {
    function isMatch(url, resource) {
      return url.indexOf(resource) != -1;
    }

    return new Promise(function(resolve, reject){
      if (isMatch(url, '/get/all')) {
        resolve({
          'show-indicator-icon': true,
          'hotkey-show-app': 'Ctrl+Alt L',
          'autostart-allowed': true,
          'autostart-enabled': true,
          'theme-name': 'light',
          'version': '1.2.3'
        });
      } else if (isMatch(url, '/set/show-indicator-icon')) {
        console.log('/set/show-indicator-icon', params);
        setTimeout(resolve, 0); // preventDefault doesn't work unless resolution is done in the next event loop
      } else if (isMatch(url, '/set/autostart-enabled')) {
        console.log('/set/autostart-enabled', params);
        setTimeout(resolve, 0);
      } else if (isMatch(url, '/set/theme-name')) {
        console.log('/set/theme-name', params);
        setTimeout(resolve, 0);
      } else if (isMatch(url, '/show/file-browser')) {
        console.log('/show/file-browser', params);
        setTimeout(resolve, 0);
        setTimeout(function(){
          window.onNotification('file-select',
            {name: params.name, path: 'http://getbootstrap.com/favicon.ico'});
        }, 500);
      } else if (isMatch(url, '/shortcut/get-all')) {
        console.log('/shortcut/get-all', params);
        setTimeout(function(){
          resolve(_getShortcuts());
        }, 0);
      } else if (isMatch(url, '/shortcut/update')) {
        console.log('/shortcut/update', params);
        setTimeout(resolve, 0);
      } else if (isMatch(url, '/shortcut/delete')) {
        console.log('/shortcut/delete', params);
        setTimeout(resolve, 0);
      } else if (isMatch(url, '/shortcut/add')) {
        console.log('/shortcut/add', params);
        setTimeout(function(){
          resolve({id: 'new-id-832923742'});
        }, 0);
      } else {
        reject("Unknown resource");
      }
    });
  };
}

function _getShortcuts() {
  return [
    {
      id: 'dad51010-04ee-44fc-81c4-ed6fb72cbf19',
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
      id: 'dad51010-04ee-44fc-81c4-ed6fb72cbf19',
      icon: 'https://assets-cdn.github.com/favicon.ico',
      name: 'Google Maps',
      keyword: 'maps',
      cmd: 'https://www.google.com.ua/maps/search/%s?hl=en&source=opensearch'
    },
    {
      id: 'dad51010-04ee-44fc-81c4-ed6fb72cbf19',
      icon: 'https://assets-cdn.github.com/favicon.ico',
      name: 'Google Play',
      keyword: 'play',
      cmd: 'https://play.google.com/store/search?q=%s&utm_source=opensearch'
    },
    {
      id: 'dad51010-04ee-44fc-81c4-ed6fb72cbf19',
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
      id: 'dad51010-04ee-44fc-81c4-ed6fb72cbf19',
      icon: 'https://assets-cdn.github.com/favicon.ico',
      name: 'Google Maps',
      keyword: 'maps',
      cmd: 'https://www.google.com.ua/maps/search/%s?hl=en&source=opensearch'
    },
    {
      id: 'dad51010-04ee-44fc-81c4-ed6fb72cbf19',
      icon: 'https://assets-cdn.github.com/favicon.ico',
      name: 'Google Play',
      keyword: 'play',
      cmd: 'https://play.google.com/store/search?q=%s&utm_source=opensearch'
    },
    {
      id: 'dad51010-04ee-44fc-81c4-ed6fb72cbf19',
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
      id: 'dad51010-04ee-44fc-81c4-ed6fb72cbf19',
      icon: 'https://assets-cdn.github.com/favicon.ico',
      name: 'Google Maps',
      keyword: 'maps',
      cmd: 'https://www.google.com.ua/maps/search/%s?hl=en&source=opensearch'
    },
    {
      id: 'dad51010-04ee-44fc-81c4-ed6fb72cbf19',
      icon: 'https://assets-cdn.github.com/favicon.ico',
      name: 'Google Play',
      keyword: 'play',
      cmd: 'https://play.google.com/store/search?q=%s&utm_source=opensearch'
    },
    {
      id: 'dad51010-04ee-44fc-81c4-ed6fb72cbf19',
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
      id: 'dad51010-04ee-44fc-81c4-ed6fb72cbf19',
      icon: 'https://assets-cdn.github.com/favicon.ico',
      name: 'Google Maps',
      keyword: 'maps',
      cmd: 'https://www.google.com.ua/maps/search/%s?hl=en&source=opensearch'
    },
    {
      id: 'dad51010-04ee-44fc-81c4-ed6fb72cbf19',
      icon: 'https://assets-cdn.github.com/favicon.ico',
      name: 'Google Play',
      keyword: 'play',
      cmd: 'https://play.google.com/store/search?q=%s&utm_source=opensearch'
    },
  ];
}