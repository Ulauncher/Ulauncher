if (window.location.href.indexOf('browser') != -1) {
    // debugging in a browser with fixtures if URL has 'browser'

    window.jsonp = function (url, params) {
        function isMatch(url, resource) {
            return url.indexOf(resource) != -1;
        }

        return new Promise(function(resolve, reject){
            if (isMatch(url, '/get/all')) {
                resolve({
                    'show-indicator-icon': true,
                    'hotkey-show-app': 'Ctrl+Alt L',
                    'autostart-allowed': true,
                    'autostart-enabled': true
                });
            } else if (isMatch(url, '/set/show-indicator-icon')) {
                setTimeout(resolve, 0); // preventDefault doesn't work unless resolution is done in the next event loop
            } else if (isMatch(url, '/set/autostart-enabled')) {
                setTimeout(resolve, 0);
            } else {
                reject("Unknown resource");
            }
        });
    };
}

var autostart = document.querySelector('#autostart');
var hotkeyShowApp = document.querySelector('#hotkey-show-app');
var showIndicatorIcon = document.querySelector('#show-indicator-icon');

function onNotification(name, data) {
    if (name == 'hotkey-set') {
        if (data.name == 'hotkey-show-app' && data.value) {
            jsonp('prefs://set/hotkey-show-app', {value: data.value}).then(function(){
                hotkeyShowApp.value = data.displayValue;
            });
        }
    }
}

jsonp('prefs://get/all').then(function(data){
    autostart.checked = data['autostart-enabled'];
    autostart.disabled = !data['autostart-allowed'];
    hotkeyShowApp.value = data['hotkey-show-app'];
    showIndicatorIcon.checked = data['show-indicator-icon'];
}, function(e){
    console.error('/get/all', e);
});

autostart.addEventListener('click', function(e){
    e.preventDefault();
    jsonp('prefs://set/autostart-enabled', {value: autostart.checked}).then(function(){
        autostart.checked = !autostart.checked;
    }, function(e){
        // replace with a custom popup
        console.error(e);
    });
});

showIndicatorIcon.addEventListener('click', function(e){
    e.preventDefault();
    jsonp('prefs://set/show-indicator-icon', {value: showIndicatorIcon.checked}).then(function(){
        showIndicatorIcon.checked = !showIndicatorIcon.checked;
    }, function(e){
        // replace with a custom popup
        console.error(e);
    });
});

hotkeyShowApp.addEventListener('click', function(e){
    e.preventDefault();
    jsonp('prefs://show/hotkey-dialog', {name: 'hotkey-show-app'});
});
