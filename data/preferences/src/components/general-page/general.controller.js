(function(){
  'use strict';

  angular.module('ulauncher')
    .controller('generalController', generalController);

  generalController.$inject = ['$scope','$element', 'apiService'];

  function generalController($scope, $element, apiService) {

    var autostartEl = document.querySelector('#autostart');
    var hotkeyShowAppEl = document.querySelector('#hotkey-show-app');
    var showIndicatorIconEl = document.querySelector('#show-indicator-icon');
    var showRecentApps = document.querySelector('#show-recent-apps');

    // get preferences and update checkboxes/inputs
    apiService.getPrefs().then(function (data){
      autostartEl.checked = data['autostart-enabled'];
      autostartEl.disabled = !data['autostart-allowed'];
      hotkeyShowAppEl.value = data['hotkey-show-app'];
      showIndicatorIconEl.checked = data['show-indicator-icon'];
      showRecentApps.checked = data['show-recent-apps'];
    });

    // evenets watchers
    $scope.$on('setHotkeyShowApp', function (event, data) {
      hotkeyShowAppEl.value = data.displayValue;
    });

    $scope.toggleAutostart = function(e) {
      e.preventDefault();
      apiService.setAutostart(autostartEl);
    };

    $scope.toggleIndicatorIcon = function(e) {
      e.preventDefault();
      apiService.setShowIndicatorIcon(showIndicatorIconEl);
    };

    $scope.hotkeyShowPopup = function(e) {
      e.preventDefault();
      apiService.showHotkeyDialog();
    };

    $scope.toggleRecentApps = function (e) {
      e.preventDefault();
      apiService.showHotkeyDialog();
    };

    $scope.toggleRecentApps = function(e) {
      e.preventDefault();
      apiService.setShowRecentApps(showRecentApps);
    }
  }
})();