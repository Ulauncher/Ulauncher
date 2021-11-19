var webpack = require('webpack')
var baseWebpackConfig = require('./webpack.base.conf')
var HtmlWebpackPlugin = require('html-webpack-plugin')
var FriendlyErrorsPlugin = require('@nuxtjs/friendly-errors-webpack-plugin')
var { VueLoaderPlugin } = require('vue-loader')

// add hot-reload related code to entry chunks
Object.keys(baseWebpackConfig.entry).forEach(function (name) {
  baseWebpackConfig.entry[name] = ['./dev-client'].concat(baseWebpackConfig.entry[name])
})

module.exports = Object.assign({}, baseWebpackConfig, {
  mode: 'development',
  output: {
    filename: '[name].js',
    publicPath: '/',
  },
  // cheap-module-eval-source-map is faster for development
  devtool: 'eval-cheap-module-source-map',
  plugins: [
    new VueLoaderPlugin(),
    // https://github.com/glenjamin/webpack-hot-middleware#installation--usage
    new webpack.HotModuleReplacementPlugin(),
    // https://github.com/ampedandwired/html-webpack-plugin
    new HtmlWebpackPlugin({
      filename: 'index.html',
      template: 'index.html',
      inject: true
    }),
    new FriendlyErrorsPlugin()
  ]
})
