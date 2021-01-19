using Toybox.Application;
using Toybox.Position;



(:glance)
class SMHIApp extends Application.AppBase {

    var mainView, glanceView;

    function initialize() {
        AppBase.initialize();
        System.println("SMHIApp initialize");
        
    }

    // onStart() is called on application start up
    function onStart(state) {
        System.println("SMHIApp onStart");
        
        
    }

    // onStop() is called when your application is exiting
    function onStop(state) {
        System.println("SMHIApp onStop");
        
    }

    /*function onPosition(info) {
        System.println("App onPosition");
        if (mainView) {
            mainView.onPosition(info);
        }
    }*/

    // Return the initial view of your application here
    function getInitialView() {
        mainView = new SMHIView();
        return [ mainView ];
    }

    function getGlanceView() {
        glanceView = new SMHIGlanceView();
        return [glanceView];
    }
}
