// Pre-JS file for McRogueFace Emscripten build
// This runs BEFORE Emscripten's code, allowing us to patch browser quirks

// Fix for browser zoom causing undefined values in resize events
// When browser zoom changes, some event/window properties can become undefined
// which causes Emscripten's HEAP32 writes to fail with assertion errors

(function() {
    'use strict';

    // Store original addEventListener
    var originalAddEventListener = EventTarget.prototype.addEventListener;

    // Properties that Emscripten's uiEventHandlerFunc reads
    // These need to be integers, not undefined
    var windowIntegerProps = [
        'innerWidth', 'innerHeight',
        'outerWidth', 'outerHeight',
        'pageXOffset', 'pageYOffset'
    ];

    // Ensure window properties return integers even during zoom transitions
    windowIntegerProps.forEach(function(prop) {
        var descriptor = Object.getOwnPropertyDescriptor(window, prop);
        if (descriptor && descriptor.get) {
            var originalGetter = descriptor.get;
            Object.defineProperty(window, prop, {
                get: function() {
                    var val = originalGetter.call(this);
                    // Return 0 if undefined/null, otherwise floor to integer
                    return (val === undefined || val === null) ? 0 : Math.floor(val);
                },
                configurable: true
            });
        }
    });

    // Wrap addEventListener to intercept resize/scroll events
    EventTarget.prototype.addEventListener = function(type, listener, options) {
        if (type === 'resize' || type === 'scroll') {
            var wrappedListener = function(e) {
                // Ensure e.detail is an integer
                if (e.detail === undefined || e.detail === null) {
                    // Create a new event with detail = 0
                    try {
                        Object.defineProperty(e, 'detail', {
                            value: 0,
                            writable: false
                        });
                    } catch (ex) {
                        // If we can't modify, create a proxy event
                        e = new Proxy(e, {
                            get: function(target, prop) {
                                if (prop === 'detail') return 0;
                                var val = target[prop];
                                return typeof val === 'function' ? val.bind(target) : val;
                            }
                        });
                    }
                }
                return listener.call(this, e);
            };
            return originalAddEventListener.call(this, type, wrappedListener, options);
        }
        return originalAddEventListener.call(this, type, listener, options);
    };

    console.log('McRogueFace: Emscripten pre-JS patches applied');
})();
