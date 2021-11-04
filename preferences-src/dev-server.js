var express = require('express')
var webpack = require('webpack')
var config = require('./webpack.debug.conf')

var port = process.env.PORT || 8080
var app = express()
var compiler = webpack(config)

// enable hot-reload and state-preserving
var devMiddleware = require('webpack-dev-middleware')(compiler, { publicPath: config.output.publicPath })
devMiddleware.waitUntilValid(() => {
  console.log(`> Listening at http://localhost:${port}\n`)
})

app.use(devMiddleware)
app.use(require('webpack-hot-middleware')(compiler))

// handle fallback for HTML5 history API
app.use(require('connect-history-api-fallback')())

// serve pure static assets
app.use('/static', express.static('./static'))

console.log('> Starting dev server...')

app.listen(port)
