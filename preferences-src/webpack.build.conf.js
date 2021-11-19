var { resolve } = require('path')
var { BundleAnalyzerPlugin } = require('webpack-bundle-analyzer')
var { DefinePlugin } = require('webpack')
var baseConfig = require('./webpack.base.conf')
var CopyPlugin = require('copy-webpack-plugin')
var HtmlPlugin = require('html-webpack-plugin')
var { VueLoaderPlugin } = require('vue-loader')

var webpackConfig = Object.assign({}, baseConfig, {
  // http://vuejs.github.io/vue-loader/en/workflow/production.html
  mode: 'none',
  devtool: false,
  output: {
    path: resolve(__dirname, '../data/preferences'),
    filename: '[name].js',
    publicPath: './'
  },
  plugins: [
    new DefinePlugin({
      'process.env.NODE_ENV': JSON.stringify(process.env.NODE_ENV),
    }),
    new VueLoaderPlugin(),
    // Generate dist index.html with correct asset hash for caching.
    // you can customize output by editing /index.html
    // see https://github.com/ampedandwired/html-webpack-plugin
    new HtmlPlugin({
      filename: resolve(__dirname, '../data/preferences/index.html'),
      template: 'index.html',
    }),
    // Copy custom static assets
    new CopyPlugin({
      patterns: [
        { from: 'static', to: 'static' }
      ]
    })
  ]
})

// Run `yarn run analyze` to generate the bundle analyzer report
if (process.env.npm_lifecycle_event === 'analyze') {
  webpackConfig.plugins.push(new BundleAnalyzerPlugin())
}

module.exports = webpackConfig
