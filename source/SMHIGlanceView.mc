using Toybox.WatchUi as Ui;

(:glance)
class SMHIGlanceView extends Ui.GlanceView {

	function initialize() {
        GlanceView.initialize();
        System.println("SMHIGlanceView initialize");
    }
    
    // Update the view
    function onUpdate(dc) {
    	System.println("SMHIGlanceView onUpdate");
        GlanceView.onUpdate(dc);
        dc.setColor(Graphics.COLOR_WHITE, Graphics.COLOR_BLACK);
        dc.clear();
        dc.drawText(0, dc.getHeight() / 4, Graphics.FONT_SMALL, "SMHI Radar", Graphics.TEXT_JUSTIFY_LEFT);
    }

    // Called when this View is removed from the screen. Save the
    // state of this View here. This includes freeing resources from
    // memory.
    function onHide() {
        System.println("SMHIGlanceView onHide");
    }
}
