/**
 * THIS file has been heavily modified for Ulauncher's needs
 * We need this library due to working with very the very restricted Webkit register_uri_scheme()
 * Original author: alexbardas
 * https://github.com/alexbardas/jsonp-promise
 * MIT license
 */

// Callback index.
var count = 1

/**
 * JSONP handler
 *
 * @param {String} url
 * @param {Object} [params]  dictionary with query parameters
 * @return {Object} Returns a response promise and a cancel handler.
 */
export default function jsonp (url, params = {}) {
  var script

  // Generate a unique id for the request.
  var id = `__jp${count}`
  count += 1

  function cleanup () {
    // Remove the script tag.
    if (script && script.parentNode) {
      script.parentNode.removeChild(script)
    }

    window[id] = () => {}
  }


  return new Promise((resolve, reject) => {

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
    // This is a hacky, nonstandard way to send data that we resort to because of heavy
    // limitation in the GTKWebKit APIs
    url += `?${encodeURIComponent(JSON.stringify(params))}`

    // Create script.
    script = document.createElement('script')
    script.src = url
    let target = document.getElementsByTagName('script')[0] || document.head
    target.parentNode.insertBefore(script, target)
  })
}
