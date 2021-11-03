// see http://vuejs-templates.github.io/webpack for documentation.
var path = require('path')

module.exports = {
  build: {
    env: require('./prod.env'),
    index: path.resolve(__dirname, '../../data/preferences/index.html'),
    assetsRoot: path.resolve(__dirname, '../../data/preferences'),
    assetsSubDirectory: 'static',
    assetsPublicPath: './',
    optimization: {
      minimize: false
    },
    productionGzip: false,
  },
  dev: {
    env: require('./dev.env'),
    port: 8080,
    autoOpenBrowser: false,
    assetsSubDirectory: 'static',
    assetsPublicPath: '/',
    proxyTable: {},
    optimization: {
      minimize: false
    },
  }
}
