/**
 * Copyright (c) 2011 The Sahana Eden Project
 *
 * @requires GeoExplorer/Composer.js
 */

/**
 * api: (define)
 * module = GeoExplorer
 * class = GeoExplorer.SahanaComposer(config)
 * extends = GeoExplorer.Composer
 */

/** api: constructor
 *  .. class:: GeoExplorer.SahanaComposer(config)
 *
 *      Create a GeoExplorer application intended for full-screen display.
 */
GeoExplorer.SahanaComposer = Ext.extend(GeoExplorer.Composer, {

    /**
     * api: method[createTools]
     * Create the toolbar configuration for the main view.
     */
    createTools: function() {
        var tools = GeoExplorer.SahanaComposer.superclass.createTools.apply(this, arguments);

        var geoLocateButton = new Ext.Button({
            iconCls: "geolocation",
            tooltip: "Zoom to Current Location",
            handler: function() {
                navigator.geolocation.getCurrentPosition(this.zoomCurrentPosition);
            },
            scope: this
        });

        if (navigator.geolocation) {
            // HTML5 geolocation is available :)
            tools.push("-");
            tools.push(geoLocateButton);
        } else {
            // geolocation is not available...IE sucks! ;)
        }
        return tools;
    },
    
    // HTML5 GeoLocation: http://dev.w3.org/geo/api/spec-source.html
    zoomCurrentPosition: function(position) {
        var proj4326 = new OpenLayers.Projection('EPSG:4326');
        // Level to zoom into
        var zoomLevel = 15;
        var lat = position.coords.latitude;
        var lon = position.coords.longitude;
        //var elevation = position.coords.altitude;
        //var ce = position.coords.accuracy;
        //var le = position.coords.altitudeAccuracy;
        //position.coords.heading;
        //position.coords.speed;
        // @ToDo: Avoid hardcoded appname (not sure how to get there from 'this' in this context)
        window.s3_gis_app.mapPanel.map.setCenter(new OpenLayers.LonLat(lon, lat).transform(proj4326, window.s3_gis_app.mapPanel.map.getProjectionObject()), zoomLevel);
    }

});
