// WebKit.URISchemeRequest is very primitive as a server:
// * It can only read the URL (not the body of a post request)
// * It can either send data with status 200 or an error with no data.
// So we have to invent our own ways to handle errors and passing data:
// 1. Data is sent to the server as URL encoded JSON in the URL query string.
// (because actual URL params is an old, terrible and lossy standard).
// 2. The response is sent as an array "[data, error]".
export default async function fetchData (url, ...args) {
  if (args.length) {
    url = `${url}?${encodeURIComponent(JSON.stringify(args))}`
  }
  const response = await fetch(url);
  const [payload, error] = await response.json();
  if (error) {
    throw error; // Sorry, but this is more helpful than an actual error
  }
  return payload;
}
