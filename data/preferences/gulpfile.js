var gulp          = require('gulp');
var concat        = require('gulp-concat');
var sass          = require('gulp-sass');
var templateCache = require('gulp-angular-templatecache');
var browserSync   = require('browser-sync').create();
var inject        = require('gulp-inject');
var del           = require('del');
var childProc     = require('child_process');

var extCss = ['bower_components/pure/pure-min.css',
              'bower_components/bootstrap/dist/css/bootstrap.min.css',
              'bower_components/font-awesome/css/font-awesome.min.css',
              'bower_components/angular-ui-grid/ui-grid.min.css',
              'node_modules/angular-ui-bootstrap/dist/ui-bootstrap-csp.css'];

var extJs = ['bower_components/angular/angular.min.js',
             'bower_components/objectpath/lib/ObjectPath.js',
             'bower_components/tv4/tv4.js',
             'bower_components/angular-route/angular-route.min.js',
             'bower_components/angular-ui-grid/ui-grid.js',
             'node_modules/angular-ui-bootstrap/dist/ui-bootstrap.js',
             'node_modules/angular-ui-bootstrap/dist/ui-bootstrap-tpls.js',
             'bower_components/angular-schema-form/dist/schema-form.min.js',
             'bower_components/angular-schema-form-bootstrap/bootstrap-decorator.min.js'];

// Tasks for dev environment
// Static Server + watching scss/html/js files
gulp.task('serve', ['sass'], function() {

    browserSync.init({
        server: "./"
    });

    gulp.watch("src/**/*.scss", ['sass']);
    gulp.watch("src/**/*.html", ['compile-templates']);

    gulp.watch("index.html").on('change', browserSync.reload);

    gulp.watch("src/components/**/*.html").on('change', browserSync.reload);
    gulp.watch("src/components/**/*.scss").on('change', browserSync.reload);
    gulp.watch("src/components/**/*.js").on('change', browserSync.reload);
    gulp.watch("src/js/**/*.js").on('change', browserSync.reload);
});

gulp.task('copy-index-html', function() {
  childProc.execSync('cp index.tmpl.html index.html');
});

gulp.task('build-checksum', function() {
  childProc.execSync('hash git && git rev-parse HEAD > .build-checksum');
});

gulp.task('sass', function() {
  return gulp.src("src/components/main.scss")
    .pipe(sass())
    .pipe(gulp.dest(".tmp/css/"))
    .pipe(browserSync.stream());
});

gulp.task('compile-templates', function() {
  return  gulp.src('src/components/**/*.html')
    .pipe(templateCache({
        'module': 'ulauncher'
    }))
    .pipe(gulp.dest('.tmp/templates/'));
});

gulp.task('dev-copy-fonts', function() {
  return gulp.src(['bower_components/font-awesome/fonts/*',
                   'bower_components/angular-ui-grid/*.ttf',
                   'bower_components/angular-ui-grid/*.woff'])
    .pipe(gulp.dest('.tmp/css'));
});

gulp.task('inject-dev',
          ['copy-index-html', 'sass', 'dev-copy-fonts', 'compile-templates', 'build-checksum'],
          function() {
  var target = gulp.src('index.html');
  var devFiles = ['src/components/**/*.js', '.tmp/templates/*.js', '.tmp/css/**/*.css', 'src/js/libs/*.js',
    'src/js/fixture.js'];
  var sources = gulp.src(extCss.concat(extJs).concat(devFiles), {read: false});

   target.pipe(inject(sources, {addRootSlash: false}))
      .pipe(gulp.dest('./'));
});

// Tasks for a production build

gulp.task('clean-build', function () {
  del.sync(['build', '.tmp']);
});

gulp.task('build-concat-css', ['sass'], function() {
  return gulp.src(extCss.concat(['.tmp/css/**/*.css']))
    .pipe(concat('app.min.css'))
    .pipe(gulp.dest('build/css'));
});

gulp.task('build-concat-js', ['compile-templates'], function() {
  return gulp.src(extJs.concat(['src/**/*.js', '.tmp/templates/*.js']))
    .pipe(concat('app.min.js'))
    .pipe(gulp.dest('build/js'));
});

gulp.task('inject-build',['copy-index-html', 'build-concat-css', 'build-concat-js', 'build-checksum'], function() {
  var target = gulp.src('index.html'),
    sources = gulp.src(['build/**/*.js', 'build/css/**/*.css'], {read: false});

   target.pipe(inject(sources, {addRootSlash: false}))
      .pipe(gulp.dest('./'));
});

gulp.task('build-copy-fonts', function() {
  return gulp.src(['bower_components/font-awesome/fonts/*',
                   'bower_components/angular-ui-grid/*.ttf',
                   'bower_components/angular-ui-grid/*.woff'])
    .pipe(gulp.dest('build/fonts'));
});


gulp.task('default', ['serve', 'inject-dev']);
gulp.task('build', ['clean-build', 'inject-build', 'build-copy-fonts']);
