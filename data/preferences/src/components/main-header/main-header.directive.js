(function(){
  angular.module('ulauncher')
    .directive('mainHeader', mainHeader);

  mainHeader.$inject = ['$location', 'apiService'];

  function mainHeader($location, apiService) {
    return {
      restrict: 'E',
      replace: true,
      templateUrl: 'main-header/main-header.html',
      link: link
    }

    function link(scope, elem, attrs) {
      // methods
      scope.isActivePage = isActivePage;

      scope.headerLinks = [
        {
          name: 'general',
          iconClass: 'fa-cog',
          text: 'general'
        },{
          name: 'help',
          iconClass: 'fa-support',
          text: 'help'
        },{
          name: 'about',
          iconClass: 'fa-info-circle',
          text: 'about'
        }
      ];

      scope.closePrefs = function closePrefs () {
        apiService.close();
      };

      function isActivePage(route) {
        return route === $location.path();
      }
    }
  }
})();