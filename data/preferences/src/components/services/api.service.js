(function(){
  'use strict';

  angular.module('ulauncher')
    .service('apiService', apiService);

  apiService.$inject = ['$rootScope', '$q'];

  // All jsonp calls should be stored in this service
  function apiService($rootScope, $q) {
    window.onNotification = function (name, data) {
      console.info('onNotification', name, JSON.stringify(data));
      if (name == 'hotkey-set') {
        if (data.name == 'hotkey-show-app' && data.value) {
          setHotkeyShowApp(data);
        }
      } else if (name == 'file-select') {
        onFileSelect(data.name, data.path);
      }
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

    function setTheme(name) {
      return jsonp('prefs://set/theme-name', {value: name});
    }

    // file select API

    var pendingHandlers = {};

    function showFileBrowser(type, name) {
      var handler = $q.defer();
      pendingHandlers[name] = handler;
      return jsonp('prefs://show/file-browser', {name: name, type: type}).then(function(){
        return handler.promise;
      });
    }

    function onFileSelect(name, path) {
      if (pendingHandlers[name]) {
        var method = path ? 'resolve' : 'reject'; // resolve if path isn't empty
        pendingHandlers[name][method](path);
        delete pendingHandlers[name];
      }
    }

    // shortcut API

    function getAllShortcuts() {
      return jsonp('prefs://shortcut/get-all');
    }

    function updateShortcut(icon, name, keyword, cmd, is_default_search, id) {
      return jsonp('prefs://shortcut/update', {
        id: id,
        icon: icon,
        name: name,
        keyword: keyword,
        cmd: cmd,
        is_default_search: is_default_search
      });
    }

    function addShortcut(icon, name, keyword, cmd, is_default_search) {
      return jsonp('prefs://shortcut/add', {
        icon: icon,
        name: name,
        keyword: keyword,
        cmd: cmd,
        is_default_search: is_default_search
      });
    }

    function deleteShortcut(id) {
      return jsonp('prefs://shortcut/delete', {id: id});
    }

    return {
      getPrefs: getPrefs,
      setAutostart: setAutostart,
      setShowIndicatorIcon: setShowIndicatorIcon,
      setShowRecentApps: setShowRecentApps,
      showHotkeyDialog: showHotkeyDialog,
      showFileBrowser: showFileBrowser,
      setTheme: setTheme,
      close: close,

      shortcut: {
        getAll: getAllShortcuts,
        update: updateShortcut,
        add: addShortcut,
        delete: deleteShortcut
      }
    };

  }
})();