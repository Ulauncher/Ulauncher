(function(){
  'use strict';

  angular.module('ulauncher')
    .controller('aboutController', aboutController);

  aboutController.$inject = ['$scope'];

  function aboutController($scope) {
    // NOTICE: This controller is empty, but I'm almost sure
    // it will be needed when api for opening links in native
    // browser will be ready (for Credits button)
  }
})();