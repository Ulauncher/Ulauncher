angular.module('schemaForm').config(
['schemaFormProvider', 'schemaFormDecoratorsProvider', 'sfPathProvider',
  function (schemaFormProvider, schemaFormDecoratorsProvider, sfPathProvider) {
    var fileUpload = function (name, schema, options) {
      if (schema.type === 'string' && schema.format === 'file') {
        var f = schemaFormProvider.stdFormObj(name, schema, options);
        f.key = options.path;
        f.type = 'fileUpload';
        options.lookup[sfPathProvider.stringify(options.path)] = f;
        return f;
      }
    };

    schemaFormProvider.defaults.string.unshift(fileUpload);

    schemaFormDecoratorsProvider.addMapping(
      'bootstrapDecorator',
      'fileUpload',
      'angular-schema-form-file-upload/file-upload.html'
    );

    schemaFormDecoratorsProvider.createDirective(
      'fileUpload',
      'angular-schema-form-file-upload/file-upload.html'
    );
}]);

angular.module('schemaForm').directive('changeIcon', ['apiService', '$parse', function (apiService, $parse) {
  return {
    restrict: 'A',
    require: 'ngModel',
    link: function (scope, element, attrs, ngModelCtrl) {
      element.on('click', function(){
        apiService.showFileBrowser('image', 'icon1').then(function(path){
          ngModelCtrl.$setViewValue(path);
        });
      });
    }
  };
}]);