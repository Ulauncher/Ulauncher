(function(){
  'use strict';

  var App = angular.module('ulauncher', [
    'ngRoute'
  ]);

  App.config(['$routeProvider', function($routeProvider) {
    $routeProvider
      .when('/', {
          templateUrl : 'general-page/general.html'
      })
      .when('/general', {
          templateUrl : 'general-page/general.html'
      })
      .when('/help', {
          templateUrl : 'help-page/help.html'
      })
      .when('/about', {
          templateUrl : 'about-page/about.html'
      })
      .otherwise({redirectTo: '/general'});
  }]);
})();