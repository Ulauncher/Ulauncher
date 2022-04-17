// see http://vuejs-templates.github.io/webpack for documentation.
var { resolve } = require('path')

module.exports = {
  entry: { app: './src/main.js' },
  resolve: {
    extensions: ['.js', '.vue', '.json'],
    alias: {
      'vue$': 'vue/dist/vue.esm.js',
      '@': resolve(__dirname, 'src')
    }
  },
  module: {
    rules: [
      {
        test: /\.css$/,
        use: ['vue-style-loader', { loader: 'css-loader' }]
      },
      {
        test: /\.vue$/,
        loader: 'vue-loader'
      },
      {
        test: /\.(png|jpe?g|gif|svg)(\?.*)?$/,
        loader: 'url-loader',
        options: {
          limit: 10000,
          name: 'static/img/[name].[hash:7].[ext]'
        }
      },
      {
        test: /\.(woff2?|eot|ttf|otf)(\?.*)?$/,
        loader: 'url-loader',
        options: {
          limit: 10000,
          name: 'static/fonts/[name].[hash:7].[ext]'
        }
      }
    ]
  }
}
