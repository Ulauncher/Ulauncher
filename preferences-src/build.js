var rm = require('rimraf')
var path = require('path')
var webpack = require('webpack')
var config = require('./webpack.build.conf')

console.log('building...')

rm(path.join(config.output.path, 'static'), err => {
  if (err) throw err
  webpack(config, (err, stats) => {
    if (err) throw err
    process.stdout.write(stats.toString({
      colors: true,
      modules: false,
      children: false,
      chunks: false,
      chunkModules: false
    }) + '\n\n')
  })
})
