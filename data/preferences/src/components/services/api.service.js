(function(){
  'use strict';

  angular.module('ulauncher')
    .service('apiService', apiService);

  apiService.$inject = ['$rootScope', '$q'];

  // All jsonp calls should be stored in this service
  function apiService($rootScope, $q) {
    window.onNotification = function (name, data) {
      if (name == 'hotkey-set') {
        if (data.name == 'hotkey-show-app' && data.value) {
          setHotkeyShowApp(data);
        }
      }
    };

    return {
      getPrefs: getPrefs,
      setAutostart: setAutostart,
      setShowIndicatorIcon: setShowIndicatorIcon,
      setShowRecentApps: setShowRecentApps,
      showHotkeyDialog: showHotkeyDialog,
      close: close
    };

    function getSetting(name) {
      return settings[name];
    }

    var prefsDefer;
    function getPrefs() {
      if (prefsDefer) {
        return prefsDefer.promise;
      }

      prefsDefer = $q.defer();
      jsonp('prefs://get/all').then(function(data){
        prefsDefer.resolve(data);
      }, function(err){
        console.error('/get/all', err);
        prefsDefer.reject();
      });
      return prefsDefer.promise;
    }

    function setAutostart(el) {
      jsonp('prefs://set/autostart-enabled', {value: !el.checked}).then(function(){
          el.checked = !el.checked;
      }, function(err){
          console.error(err);
      });
    }

    function setShowIndicatorIcon(el) {
      jsonp('prefs://set/show-indicator-icon', {value: !el.checked}).then(function(){
        el.checked = !el.checked;
      }, function(err){
        console.error(err);
      });
    }

    function setShowRecentApps(el) {
      jsonp('prefs://set/show-recent-apps', {value: !el.checked}).then(function(){
        el.checked = !el.checked;
      }, function(err){
        console.error(err);
      });
    }

    function showHotkeyDialog() {
      jsonp('prefs://show/hotkey-dialog', {name: 'hotkey-show-app'});
    }

    function setHotkeyShowApp(data) {
      jsonp('prefs://set/hotkey-show-app', {value: data.value}).then(function(){
        $rootScope.$broadcast('setHotkeyShowApp', {
          displayValue: data.displayValue
        });
      });
    }

    function close() {
      jsonp('prefs://close');
    }

  }
})();