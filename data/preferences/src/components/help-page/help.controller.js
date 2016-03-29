(function(){
  'use strict';

  angular.module('ulauncher')
    .controller('helpController', helpController);

  helpController.$inject = ['$scope'];

  function helpController($scope) {
    this.openUrlInBrowser = openUrlInBrowser;

    function openUrlInBrowser(urllink) {
      jsonp('prefs://open/web-url', {url: urllink}).then(function(){
        }, function(err){
          console.error(err);
        });
    }

    $scope.infoGroup = [
      {
        'icon': 'fa-github',
        'label': 'troubleshooting help',
        'text': 'Find or report your issue on Github',
        'url': 'https://github.com/Ulauncher/Ulauncher/issues'
      },
      {
        'icon': 'fa-envelope',
        'label': 'email us',
        'text': "Email us if you didn't find answer to your question/issue on Github",
        'url': 'mailto:ulauncher.app@gmail.com'
      },
      {
        'icon': 'fa-github-alt',
        'label': 'chat on gitter',
        'text': 'Chat with us on Gitter. (Keep in mind that our team leaves in Eastern European Time)',
        'url': 'https://gitter.im/Ulauncher'
      },
      {
        'icon': 'fa-twitter',
        'label': 'follow on twitter',
        'text': 'Follow us to get the latest updates and news about Ulauncher',
        'url': 'https://twitter.com/UlauncherApp'
      }
    ];
  }
})();