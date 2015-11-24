(function(){
  angular.module('ulauncher')
    .directive('mainHeader', mainHeader);

  mainHeader.$inject = [];

  function mainHeader() {
    return {
      restrict: 'E',
      replace: true,
      templateUrl: 'main-header/main-header.html',
      link: link
    }

    function link(scope, elem, attrs) {
      scope.activePage = 'general';
    }
  }
})();