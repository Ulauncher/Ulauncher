(function(){
  'use strict';

  angular.module('ulauncher')
    .constant('ShortcutSchema', {
      type: 'object',
      properties: {
        icon: { type: 'string', title: 'Icon', format: 'file' },
        name: { type: 'string', title: 'Name' },
        keyword: { type: 'string', title: 'Keyword' },
        cmd: { type: 'string', title: 'Query or CMD' }
      }
    })
    .controller('shortcutsController', shortcutsController);

  shortcutsController.$inject = ['$scope','$element', '$window', '$uibModal', 'apiService'];

  function shortcutsController($scope, $element, $window, $uibModal, apiService) {
    $scope.gridOptions = {
      enableColumnMenus: false,
      cellTemplate: null,
      showGridFooter: true,
      gridFooterHeight: 50,
      gridFooterTemplate: 'shortcuts-page/add.button.html',
      columnDefs: [{displayName: '', field: 'icon', width: 50, cellClass: 'shortcuts-grid__icon-cell',
                    cellTemplate: '<img class="shortcuts-grid__icon" ng-src="{{row.entity.icon}}" />'},
                   {displayName: 'Name', field: 'name'},
                   {displayName: 'Keyword', field: 'keyword'},
                   {displayName: 'Query or CMD', field: 'cmd', width: '50%',
                    cellTemplate: 'shortcuts-page/row.controls.html'}],
      onRegisterApi: function (gridApi) {
        $scope.gridApi = gridApi;
      }
    };

    // populate the grid
    apiService.shortcut.getAll().then(function (data) {
      $scope.gridOptions.data = data || [];
    });

    function showEditForm(row, grid) {
      $uibModal.open({
        animation: false,
        templateUrl: 'shortcuts-page/edit.modal.html',
        controller: ['$uibModalInstance', 'ShortcutSchema', 'apiService', 'grid', 'row', RowEditCtrl],
        controllerAs: 'vm',
        resolve: {
          grid: function () { return grid; },
          row: function () { return row; }
        }
      });
    }

    $scope.showContent = function (fileContent) {
      $scope.model.icon = fileContent;
      console.log($scope.model);
    };

    // control bindings
    $scope.edit = showEditForm;
    $scope.add = showEditForm;
    $scope.delete = function(row, grid) {
      apiService.shortcut.delete(row.entity.id).then(function(){
        $scope.$apply(function(){
          var index = grid.appScope.gridOptions.data.indexOf(row.entity);
          grid.appScope.gridOptions.data.splice(index, 1);
        });
      });
    };

    // resizing logic
    $scope.gridHeight = 0;
    angular.element($window).bind('resize', function () {
      resizeContainer();
    });

    resizeContainer();

    function resizeContainer() {
      var mainHeader = document.querySelector('.main-header');
      $scope.gridHeight = window.innerHeight - mainHeader.offsetHeight - 30;
    }

  }

  function RowEditCtrl($uibModalInstance, ShortcutSchema, apiService, grid, row) {
    var vm = this;

    vm.schema = ShortcutSchema;
    if (row) {
      vm.entity = angular.copy(row.entity);
    } else {
      vm.entity = {icon: '', name: '', keyword: '', cmd: ''};
    }
    vm.form = [
      {
        key: "icon",
        type: "fileUpload",
        options: {
          onReadFn: "showContent"
        }
      },
      'name',
      'keyword',
      {
        type: 'textarea',
        key: 'cmd',
        placeholder: 'Use %s as a placeholder for a user query.'
      }];

    vm.grid = grid;
    vm.row = row;
    vm.save = save;

    function save() {
      var entity = vm.entity;
      var method = entity && entity.id ? 'update' : 'add';
      apiService.shortcut[method](entity.icon, entity.name, entity.keyword, entity.cmd, entity.id).then(function(resp){
        if (method == 'update') {
          // Copy row values over
          row.entity = angular.extend(row.entity, entity);
        } else {
          entity.id = resp.id;
          vm.grid.appScope.gridOptions.data.push(entity);
        }
        $uibModalInstance.close(true);
      }, function(e) {
        console.error(e);
      });
    }
  }

})();
