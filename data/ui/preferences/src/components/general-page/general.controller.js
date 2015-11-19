(function(){
  'use strict';

  angular.module('uLauncher')
    .controller('generalController', generalController);

  generalController.$inject = ['$scope','$element', 'apiService'];

  function generalController($scope, $element, apiService) {
    $scope.toggleAutostart = toggleAutostart;
    $scope.toggleIndicatorIcon = toggleIndicatorIcon;
    $scope.hotkeyShowPopup = hotkeyShowPopup;

    var autostartEl = document.querySelector('#autostart'),
      hotkeyShowAppEl = document.querySelector('#hotkey-show-app'),
      showIndicatorIconEl = document.querySelector('#show-indicator-icon');

    // initialization
    apiService.getAll(autostartEl, hotkeyShowAppEl, showIndicatorIconEl);

    // evenets watchers
    $scope.$on('setHotkeyShowApp', function (event, data) {
      hotkeyShowAppEl.value = data.displayValue;
    });

    function toggleAutostart(e) {
      e.preventDefault();
      apiService.setAutostart(autostartEl);
    }

    function toggleIndicatorIcon(e) {
      e.preventDefault();
      apiService.setShowIndicatorIcon(showIndicatorIconEl)
    }

    function hotkeyShowPopup(e) {
      e.preventDefault();
      apiService.showHotkeyDialog();
    }
  }
})();