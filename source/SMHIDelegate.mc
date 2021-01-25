using Toybox.WatchUi;
using Toybox.Application;

class SMHIDelegate extends WatchUi.InputDelegate {
    function initialize() {
        InputDelegate.initialize();
    }

    // Handle key  events
    function onKey(evt) {
        var app = Application.getApp();
        var key = evt.getKey();
        if (WatchUi.KEY_DOWN == key) {
            return app.mainView.zoom(1);
        } else if (WatchUi.KEY_UP == key) {
            return app.mainView.zoom(-1);
        } else if (WatchUi.KEY_ENTER == key) {
            //app.mainView.action();
            return false;
        } else if (WatchUi.KEY_START == key) {
            //app.mainView.action();
            return false;
        } else {
            return false;
        }
        WatchUi.requestUpdate();
        return true;
    }
}