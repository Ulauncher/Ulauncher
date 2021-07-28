/**
 * Author: alexbardas
 * https://github.com/alexbardas/jsonp-promise
 * MIT license
 */

// Callback index.
var count = 0

/**
 * JSONP handler
 *
 * Options:
 * - prefix {String} callback prefix (defaults to `__jp`)
 * - param {String} qs parameter (defaults to `callback`)
 * - timeout {Number} how long after the request until a timeout error
 *   is emitted (defaults to `15000`)
 *
 * @param {String} url
 * @param {Object} [params]  dictionary with query parameters
 * @param {Object} [options]
 * @return {Object} Returns a response promise and a cancel handler.
 */
export default function jsonp (url, params, options) {
  params = params || {}
  options = options || {}

  var script
  var timer
  var cancel

  // Generate a unique id for the request.
  var prefix = options.prefix || '__jp'
  var id = prefix + (count++)

  function cleanup () {
    // Remove the script tag.
    if (script && script.parentNode) {
      script.parentNode.removeChild(script)
    }

    window[id] = () => {}

    if (timer) {
      clearTimeout(timer)
    }
  }

  function b64EncodeUnicode (str) {
    // first we use encodeURIComponent to get percent-encoded UTF-8,
    // then we convert the percent encodings into raw bytes which
    // can be fed into btoa.
    return btoa(encodeURIComponent(str).replace(
      /%([0-9A-F]{2})/g,
      (match, p1) => {
        return String.fromCharCode('0x' + p1)
      }
    ))
  }

  let promise = new Promise(function (resolve, reject) {
    let timeout = options.timeout || 15000
    timer = setTimeout(function () {
      cleanup()
      reject('Request timeout')
    }, timeout)

    window[id] = function (data, error) {
      cleanup()
      if (error) {
        reject(error)
      } else {
        resolve(data)
      }
    }

    // Add querystring component
    let param = options.param || 'callback'
    params[param] = id
    let urlParams = []
    for (let i in params) {
      if (params[i] instanceof Object) {
        let key = `${i}_b64json`
        let val = b64EncodeUnicode(JSON.stringify(params[i]))
        urlParams.push(`${key}=${val}`)
      } else {
        urlParams.push(i + '=' + encodeURIComponent(params[i]))
      }
    }
    url += (~url.indexOf('?') ? '&' : '?') + urlParams.join('&')
    url = url.replace('?&', '?')

    // Create script.
    script = document.createElement('script')
    script.src = url
    let target = document.getElementsByTagName('script')[0] || document.head
    target.parentNode.insertBefore(script, target)

    cancel = function () {
      if (window[id]) {
        cleanup()
        reject('Request canceled')
      }
    }
  })

  promise.cancel = cancel

  return promise
}
