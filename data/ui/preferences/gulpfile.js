var gulp          = require('gulp');
var concat        = require('gulp-concat');
var uglify        = require('gulp-uglify');
var minifyCss     = require('gulp-minify-css');
var sass          = require('gulp-sass');
var templateCache = require('gulp-angular-templatecache');
var browserSync   = require('browser-sync').create();
var inject        = require('gulp-inject');

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
});

gulp.task('sass', function() {
  return gulp.src("./src/components/**/*.scss")
    .pipe(sass())
    .pipe(gulp.dest("./.tmp/css/"))
    .pipe(browserSync.stream());
});

gulp.task('compile-templates', function() {
  return  gulp.src('src/components/**/*.html')
    .pipe(templateCache({
        'module': 'uLauncher'
    }))
    .pipe(gulp.dest('.tmp/templates/'));
});

gulp.task('inject-dev',['sass', 'compile-templates'], function() {
  var target = gulp.src('./index.html'),
    sources = gulp.src(['./src/js/libs/jsonp.js', './src/**/*.js',
                        './.tmp/templates/*.js', './.tmp/css/**/*.css'], {read: false});

   target.pipe(inject(sources, {addRootSlash: false}))
      .pipe(gulp.dest('./'));
});

// Tasks for producion environment
gulp.task('concat-css', ['sass'], function() {
  return gulp.src('./.tmp/css/**/*.css')
    .pipe(minifyCss())
    .pipe(concat('main.min.css'))
    .pipe(gulp.dest('prod/css'));
});

gulp.task('concat-js', ['compile-templates'], function() {
  return gulp.src(['./src/components/**/*.js', './.tmp/templates/*.js'])
    .pipe(concat('app.min.js'))
    .pipe(uglify())
    .pipe(gulp.dest('prod/js'));
});

gulp.task('inject-prod',['concat-css', 'concat-js'], function() {
  var target = gulp.src('./index.html'),
    sources = gulp.src(['./src/js/libs/jsonp.js', './prod/**/*.js',
                        './prod/css/**/*.css'], {read: false});

   target.pipe(inject(sources, {addRootSlash: false}))
      .pipe(gulp.dest('./prod'));
});


gulp.task('default', ['serve', 'compile-templates', 'inject-dev']);
gulp.task('build', ['inject-prod']);