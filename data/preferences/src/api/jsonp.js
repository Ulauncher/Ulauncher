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
 * @param {String} url
 * @param {Object} [params]  dictionary with query parameters
 * @return {Promise} Resolves with the response, rejects with the error object the backend sent.
 */
export default function jsonp (url, params) {
  params = params || {}

  var script

  // Generate a unique id for the request.
  var id = '__jp' + (count++)

  function cleanup () {
    // Remove the script tag.
    if (script && script.parentNode) {
      script.parentNode.removeChild(script)
    }

    window[id] = () => {}
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

  return new Promise(function (resolve, reject) {
    window[id] = function (data, error) {
      cleanup()
      if (error) {
        reject(error)
      } else {
        resolve(data)
      }
    }

    // Add querystring component
    params['callback'] = id
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
  })
}
