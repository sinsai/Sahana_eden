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

    // Begin i18n.
    geoLocateButtonText: "Zoom to Current Location",
    potlatchButtonText: "Edit the OpenStreetMap data for this area",
    // End i18n.
    
    /**
     * api: config[potlatch_url]
     * URL of the potlatch editor
     *
     */
    potlatchUrl: '/eden/gis/potlatch2/potlatch2.html',
    
    /** private: method[createOverviewMap]
     * Adds the :class:`OpenLayers.Control.OverviewMap` to the map.
     * http://trac.osgeo.org/openlayers/wiki/Control/OverviewMap
     */
    createOverviewMap: function() {
        var proj4326 = new OpenLayers.Projection('EPSG:4326');
        var options = {
            //displayProjection: proj4326,
            projection: this.mapPanel.map.projection,
            // Use Manual stylesheet download (means can be done in HEAD to not delay pageload)
            theme: null,
            units: this.mapPanel.map.units,
            maxResolution: this.mapPanel.map.maxResolution,
            maxExtent: this.mapPanel.map.maxExtent,
            numZoomLevels: this.mapPanel.map.numZoomLevels
        };
        var overviewMap = new OpenLayers.Control.OverviewMap({
            mapOptions: options
        });

        this.mapPanel.map.addControl(overviewMap);
    },
    
    /**
     * api: method[createTools]
     * Create the toolbar configuration for the main view.
     */
    createTools: function() {
        var tools = GeoExplorer.SahanaComposer.superclass.createTools.apply(this, arguments);

        var proj4326 = new OpenLayers.Projection('EPSG:4326');

        // Edit in OpenStreetMap
        var potlatchButton =  new Ext.Button({
            iconCls: 'potlatch',
            tooltip: this.potlatchButtonText,
            handler: function() {
                // @ToDo: Avoid hardcoded appname (not sure how to get there from 'this' in this context)
                var map = s3_gis_app.mapPanel.map;
                // Read current settings from map
                var lonlat = this.mapPanel.map.getCenter();
                var zoom_current = this.mapPanel.map.getZoom();
                if ( zoom_current < 14 ) {
                    zoom_current = 14;
                }
                // Convert back to LonLat for saving
                lonlat.transform(this.mapPanel.map.getProjectionObject(), proj4326);
                var url = this.potlatchUrl + '?lat=' + lonlat.lat + '&lon=' + lonlat.lon + '&zoom=' + zoom_current;
                window.open(url);
            },
            scope: this
        })
        tools.push(potlatchButton);
        
        var geoLocateButton = new Ext.Button({
            iconCls: "geolocation",
            tooltip: this.geoLocateButtonText,
            handler: function() {
                navigator.geolocation.getCurrentPosition(this.zoomToCurrentPosition);
            },
            scope: this
        });

        if (navigator.geolocation) {
            // HTML5 geolocation is available :)
            //tools.push("-");
            tools.push(geoLocateButton);
        } else {
            // geolocation is not available...IE sucks! ;)
        }
        return tools;
    },
    
    // HTML5 GeoLocation: http://dev.w3.org/geo/api/spec-source.html
    zoomToCurrentPosition: function(position) {
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
        // http://www.sencha.com/learn/Manual:Utilities:Function
        //this.mapPanel.map.setCenter(new OpenLayers.LonLat(lon, lat).transform(proj4326, window.s3_gis_app.mapPanel.map.getProjectionObject()), zoomLevel);
        window.s3_gis_app.mapPanel.map.setCenter(new OpenLayers.LonLat(lon, lat).transform(proj4326, window.s3_gis_app.mapPanel.map.getProjectionObject()), zoomLevel);
    }

});