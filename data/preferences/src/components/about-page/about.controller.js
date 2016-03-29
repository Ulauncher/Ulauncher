(function(){
  'use strict';

  angular.module('ulauncher')
    .controller('aboutController', aboutController);

  aboutController.$inject = ['$scope', 'apiService'];

  function aboutController($scope, apiService) {
    $scope.isCreditsShown = false;

    apiService.getPrefs().then(function(data){
        $scope.version = data.version;
    });

    $scope.toggleCredits = function() {
        $scope.isCreditsShown = !$scope.isCreditsShown;
    };
  }
})();