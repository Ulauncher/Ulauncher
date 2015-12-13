(function(){
  'use strict';

  angular.module('ulauncher')
    .service('apiService', apiService);

  apiService.$inject = ['$rootScope'];

  // All jsonp calls should be stored in this service
  function apiService($rootScope) {
    window.onNotification = function (name, data) {
      if (name == 'hotkey-set') {
        if (data.name == 'hotkey-show-app' && data.value) {
          setHotkeyShowApp(data);
        }
      }
    };

    return {
      getAll: getAll,
      setAutostart: setAutostart,
      setShowIndicatorIcon: setShowIndicatorIcon,
      showHotkeyDialog: showHotkeyDialog
    };

    function getAll(autostartEl, hotkeyShowAppEl, showIndicatorIconEl) {
      jsonp('prefs://get/all').then(function(data){
        autostartEl.checked = data['autostart-enabled'];
        autostartEl.disabled = !data['autostart-allowed'];
        hotkeyShowAppEl.value = data['hotkey-show-app'];
        showIndicatorIconEl.checked = data['show-indicator-icon'];
      }, function(err){
          console.error('/get/all', err);
      });
    }

    function setAutostart(el) {
      jsonp('prefs://set/autostart-enabled', {value: el.checked}).then(function(){
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
  }
})();