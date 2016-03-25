(function(){
  'use strict';

  angular.module('ulauncher')
    .controller('generalController', generalController);

  generalController.$inject = ['$scope','$element', 'apiService'];

  function generalController($scope, $element, apiService) {
    $scope.toggleAutostart = toggleAutostart;
    $scope.toggleIndicatorIcon = toggleIndicatorIcon;
    $scope.hotkeyShowPopup = hotkeyShowPopup;

    var autostartEl = document.querySelector('#autostart'),
      hotkeyShowAppEl = document.querySelector('#hotkey-show-app'),
      showIndicatorIconEl = document.querySelector('#show-indicator-icon');

    // get preferences and update checkboxes/inputs
    apiService.getPrefs().then(function (data){
      autostartEl.checked = data['autostart-enabled'];
      autostartEl.disabled = !data['autostart-allowed'];
      hotkeyShowAppEl.value = data['hotkey-show-app'];
      showIndicatorIconEl.checked = data['show-indicator-icon'];
    });

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