(function(){
  'use strict';

  angular.module('ulauncher')
    .controller('aboutController', aboutController);

  aboutController.$inject = ['$scope', 'apiService'];

  function aboutController($scope, apiService) {
    apiService.getPrefs().then(function(data){
        $scope.version = data.version;
    });
  }
})();