(function(){
  'use strict';

  angular.module('ulauncher')
    .controller('helpController', helpController);

  helpController.$inject = ['$scope'];

  function helpController($scope) {
    var vm = this;

    vm.openUrlInBrowser = openUrlInBrowser

    function openUrlInBrowser(urllink) {
      jsonp('/open/web-url', {url: urllink}).then(function(){
        }, function(err){
          console.error(err);
        });
    }

    $scope.infoGroup = [
      {
        'icon': 'fa-comments',
        'label': 'troubleshooting help',
        'text': 'Lorem ipsum dolor sit amet, consectetur adipisicing elit. Fugiat a qui necessitatibus provident fuga nobis incidunt quisquam.',
        'url': 'mailto:ulauncher.app@gmail.com'
      },
      {
        'icon': 'fa-envelope',
        'label': 'email us',
        'text': 'Lorem ipsum dolor sit amet, consectetur adipisicing elit. Fugiat a qui necessitatibus provident fuga nobis incidunt quisquam.',
        'url': 'mailto:ulauncher.app@gmail.com'
      },
      {
        'icon': 'fa-github-alt',
        'label': 'chat on gitter',
        'text': 'Lorem ipsum dolor sit amet, consectetur adipisicing elit. Fugiat a qui necessitatibus provident fuga nobis incidunt quisquam.',
        'url': 'https://github.com/Ulauncher/Ulauncher/'
      },
      {
        'icon': 'fa-twitter',
        'label': 'follow on twitter',
        'text': 'Lorem ipsum dolor sit amet, consectetur adipisicing elit. Fugiat a qui necessitatibus provident fuga nobis incidunt quisquam.',
        'url': 'https://twitter.com/UlauncherApp'
      }
    ];
  }
})();