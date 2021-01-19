using Toybox.WatchUi;
using Toybox.Communications;
using Toybox.Position;
using Toybox.Graphics;
using Toybox.System;
using Toybox.Application.Storage as Storage;

class SMHIView extends WatchUi.View {

    hidden var radarImage = null;
    var posInfo = null;

    function initialize() {
        View.initialize();
    }

    // Load your resources here
    function onLayout(dc) {
        setLayout(Rez.Layouts.MainLayout(dc));
        System.println("SMHIView onLayout");
    }

    function onReceive(responseCode, data) {
        if (responseCode == 200) {
            System.println("Request Successful");
            System.println("Response: " + responseCode + " Data: " + data);  
            radarImage = data;
        }
        else {
            System.println("Response: " + responseCode + " Data: " + data);
            onPosition(Position.getInfo());
        }
        WatchUi.requestUpdate();
    }

    function updateRadar(myLocation) {
        System.println("Latitude: " + myLocation[0]);
        System.println("Longitude: " + myLocation[1]);
        Communications.makeImageRequest("https://djazz.se/connectiq/smhi/radar", {
            "lat" => myLocation[0],
            "lon" => myLocation[1],
            "scale" => 4,
            "screenWidth" => System.getDeviceSettings().screenWidth,
            "screenHeight" => System.getDeviceSettings().screenHeight
        }, {
            :dithering => Communications.IMAGE_DITHERING_NONE
        }, method(:onReceive));
        WatchUi.requestUpdate();
    }

    function onPosition(info) {
        System.println("SMHIView onPosition");
        posInfo = info;

        System.println(info.accuracy);
        
        if (info.accuracy > 0) {
            var myLocation = info.position.toDegrees();
            Storage.setValue("storedPosition", myLocation);
            updateRadar(myLocation);
        }
    }

    // Called when this View is brought to the foreground. Restore
    // the state of this View and prepare it to be shown. This includes
    // loading resources into memory.
    function onShow() {
        System.println("SMHIView onShow");
        onPosition(Position.getInfo());

        var storedPosition = Storage.getValue("storedPosition");
        if (storedPosition != null) {
            updateRadar(storedPosition);
        }

        Position.enableLocationEvents({
            :acquisitionType => Position.LOCATION_ONE_SHOT,
            :constellations => [ Position.CONSTELLATION_GPS, Position.CONSTELLATION_GALILEO ]
        }, method(:onPosition));
    }

    // Update the view
    function onUpdate(dc) {
        // Call the parent onUpdate function to redraw the layout
        System.println("SMHIView onUpdate");
        View.onUpdate(dc);
        if (posInfo == null || Position.getInfo().accuracy == 0) {
            dc.setColor(Graphics.COLOR_WHITE, Graphics.COLOR_BLACK);
            dc.clear();
            dc.drawText(dc.getWidth() / 2, dc.getHeight() / 4, Graphics.FONT_SMALL, "Getting position...", Graphics.TEXT_JUSTIFY_CENTER);
            dc.drawText(dc.getWidth() / 2, dc.getHeight() / 2, Graphics.FONT_SMALL, Position.getInfo().when.value() + " " + Position.getInfo().accuracy, Graphics.TEXT_JUSTIFY_CENTER);
            System.println("Waiting for GPS...");
        } else if (radarImage == null) {
            dc.setColor(Graphics.COLOR_WHITE, Graphics.COLOR_BLACK);
            dc.clear();
            dc.drawText(dc.getWidth() / 2, dc.getHeight() / 4, Graphics.FONT_SMALL, "Loading radar image...", Graphics.TEXT_JUSTIFY_CENTER);
            dc.drawText(dc.getWidth() / 2, dc.getHeight() / 2, Graphics.FONT_SMALL, Position.getInfo().position.toDegrees()[0] + " " + Position.getInfo().accuracy, Graphics.TEXT_JUSTIFY_CENTER);
            System.println("Waiting for radar image...");
        } else {
            dc.drawBitmap(0, 0, radarImage);
            System.println("Showing radar image");
        }
    }

    // Called when this View is removed from the screen. Save the
    // state of this View here. This includes freeing resources from
    // memory.
    function onHide() {
        System.println("SMHIView onHide");
        radarImage = null;
        Position.enableLocationEvents(Position.LOCATION_DISABLE, method(:onPosition));
    }
}
