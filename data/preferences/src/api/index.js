import jsonpFixture from './fixture'
import jsonp from './jsonp'

var api = jsonp
if (window.location.href.indexOf('browser') !== -1 || window.location.href.indexOf('http') !== -1) {
  console.log('Import API fixtures')
  api = jsonpFixture
}

export default api
