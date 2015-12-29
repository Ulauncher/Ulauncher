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
          'theme-name': 'dark',
          'version': '1.2.3'
        });
      } else if (isMatch(url, '/set/show-indicator-icon')) {
        console.log('/set/show-indicator-icon', params);
        setTimeout(resolve, 0); // preventDefault doesn't work unless resolution is done in the next event loop
      } else if (isMatch(url, '/set/autostart-enabled')) {
        console.log('/set/autostart-enabled', params);
        setTimeout(resolve, 0);
      } else {
        reject("Unknown resource");
      }
    });
  };
}