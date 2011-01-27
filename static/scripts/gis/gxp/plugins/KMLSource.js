/**
 * Copyright (c) 2011 The Sahana Eden Project
 * 
 * Published under the BSD license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

/**
 * @requires plugins/LayerSource.js
 */

/** api: (define)
 *  module = gxp.plugins
 *  class = KMLSource
 */

/** api: (extends)
 *  plugins/LayerSource.js
 */
Ext.namespace("gxp.plugins");

/** api: constructor
 *  .. class:: KMLSource(config)
 *
 *    Plugin for using KML layers with :class:`gxp.Viewer` instances.
 */   
/** api: example
 *  Configuration in the  :class:`gxp.Viewer`:
 *
 *  .. code-block:: javascript
 *
 *    sources: {
 *        kml: {
 *            url: "http://example.com/example.kml",
 *            marker_url: "/img/example.png",
 *            type: "gx_kmlsource"
 *        }
 *    }
 *
 *  A typical configuration for a layer from this source (in the ``layers``
 *  array of the viewer's ``map`` config option would look like this:
 *
 *  .. code-block:: javascript
 *
 *    {
 *        source: "kml",
 *        name: "example"
 *    }
 *
 */
gxp.plugins.KMLSource = Ext.extend(gxp.plugins.LayerSource, {
    
    /** api: ptype = gx_kmlsource */
    ptype: "gxp_kmlsource",
    
    /** api: property[store]
     *  ``GeoExt.data.LayerStore``.
     *  Will contain records with name field values.
     */
    
    /** api: config[title]
     *  ``String``
     *  A descriptive title for this layer source (i18n).
     */
    title: "KML Layers",
    
    /** api: config[url]
     *  ``String`` URL for this KML source
     */
    
    /** api: config[max_w]
     *  ``Integer`` max width for the Icons
     */
    max_w: 30,
    
    /** api: config[max_h]
     *  ``Integer`` max height for the Icons
     */
    max_h: 35,
    
    /** api: method[createStore]
     *
     *  Creates a store of layer records.  Fires "ready" when store is loaded.
     */
    createStore: function() {

        var format_kml = new OpenLayers.Format.KML({
            extractStyles: true,
            extractAttributes: true,
            maxDepth: 2
        })

        // @ToDo: How to find a path for a default Icon? Across SingleFile & Debug)
        iconURL = config.marker_url || 'marker-blue.png';
        // Pre-cache this image
        // Need unique names
        var i = new Image();
        i.onload = this.scaleImage;
        i.src = iconURL;
        // Needs to be uniquely instantiated
        var style_marker = OpenLayers.Util.extend({}, OpenLayers.Feature.Vector.style['default']);
        style_marker.graphicOpacity = 1;
        style_marker.graphicWidth = i.width;
        style_marker.graphicHeight = i.height;
        style_marker.graphicXOffset = -(i.width / 2);
        style_marker.graphicYOffset = -i.height;
        style_marker.externalGraphic = iconURL;

        var options = {
            // KML coordinates are always in longlat WGS84
            projection: "EPSG:4326",
            maxExtent: new OpenLayers.Bounds(
                -180, -90, 180, 90
            ),
            maxResolution: 1.40625,
            //numZoomLevels: 19,
            units: "degrees"
        };

        var layer = {
            name: "Test KML Name",
            url: "http://127.0.0.1/eden/hms/hospital.kml",
            attribution: "Test KML Attribution"
        }

        var layers = [
            new OpenLayers.Layer.Vector(
                config.title || layer.name, 
                //OpenLayers.Util.applyDefaults({                
                //    attribution: layer.attribution,
                //    name: layer.name
                //},
                {
                    projection: layerProjection,
                    strategies: [
                        new OpenLayers.Strategy.Fixed(),
                        // @ToDo: Make these configurable
                        new OpenLayers.Strategy.Cluster({distance: 5, threshold: 2})
                    ],
                    style: style_marker,
                    protocol: new OpenLayers.Protocol.HTTP({
                        url: layer.url,
                        format: format_kml
                    })
                }
            )
        ];

        this.store = new GeoExt.data.LayerStore({
            layers: layers,
            fields: [
                {name: "source", type: "string"},
                {name: "name", type: "string"},
                {name: "abstract", type: "string", mapping: "attribution"},
                {name: "group", type: "string", defaultValue: "background"},
                {name: "fixed", type: "boolean", defaultValue: true},
                {name: "selected", type: "boolean"}
            ]
        });
        this.store.each(function(l) {
            if ( l.get("group") != "overlays" ) {
                l.set("group", "background");
            } else {
                l.set("group", "");
            }
        });
        this.fireEvent("ready", this);

    },
    
    /** api: method[createLayerRecord]
     *  :arg config:  ``Object``  The application config for this layer.
     *  :returns: ``GeoExt.data.LayerRecord``
     *
     *  Create a layer record given the config.
     */
    createLayerRecord: function(config) {
        var record;
        var index = this.store.findExact("name", config.name);
        if (index > -1) {

            record = this.store.getAt(index).copy(Ext.data.Record.id({}));
            var layer = record.getLayer().clone();
 
            // set layer title from config
            if (config.title) {
                /**
                 * Because the layer title data is duplicated, we have
                 * to set it in both places.  After records have been
                 * added to the store, the store handles this
                 * synchronization.
                 */
                layer.setName(config.title);
                record.set("title", config.title);
            }

            // set visibility from config
            if ("visibility" in config) {
                layer.visibility = config.visibility
            }
            
            record.set("selected", config.selected || false);
            record.set("source", config.source);
            record.set("name", config.name);
            if ("group" in config) {
                record.set("group", config.group);
            }

            record.data.layer = layer;
            record.commit();
        };
        return record;
    },      

    /** private: method[scaleImage]
     *
     *  Scales an Image.
     */
    scaleImage: function() {
        var scaleRatio = i.height/i.width;
        var w = Math.min(i.width, this.max_w);
        var h = w * scaleRatio;
        if (h > this.max_h) {
                h = this.max_h;
                scaleRatio = w/h;
                w = w * scaleRatio;
            }
        i.height = h;
        i.width = w;
    }

    /* @ToDo:
    
    // @ToDo: Handle KMZs
    // Provide a Server service to unzip them?
    // Have the server unzip them before they arrive here?
    
    // @ToDo: Caching
    // Again, suggests that the server processes them before they arrive here
    // Perhaps we only process KMLs from server here & use Layer Catalog to add new ones which are unzipped/cached
    
    // @ToDo: onFeatureSelect
    // check how this is being done for WFS currently
    function onKmlFeatureSelect(event) {
        // unselect any previous selections
        tooltipUnselect(event);
        var feature = event.feature;
        centerPoint = feature.geometry.getBounds().getCenterLonLat();
        var selectedFeature = feature;
        var title = feature.layer.title;
        var _attributes = feature.attributes;
        var type = typeof _attributes[title];
        if ('object' == type) {
            _title = _attributes[title].value;
        } else {
            _title = _attributes[title];
        }
        var body = feature.layer.body.split(' ');
        var content = '';
        for (var i = 0; i < body.length; i++) {
            type = typeof _attributes[body[i]];
            if ('object' == type) {
                // Geocommons style
                var displayName = _attributes[body[i]].displayName;
                if (displayName == '') {
                    displayName = body[i];
                }
                var value = _attributes[body[i]].value;
                var row = '<b>' + displayName + '</b>: ' + value + '<br />';
            } else {
                var row = _attributes[body[i]] + '<br />';
            }
            content += row;
        }
        // Protect the content against JavaScript attacks
        if (content.search('<script') != -1) {
            content = 'Content contained Javascript! Escaped content below.<br />' + content.replace(/</g, '<');
        }
        var contents = '<h2>' + _title + '</h2>' + content;

        var popup = new OpenLayers.Popup.FramedCloud('kmlpopup',
            centerPoint,
            new OpenLayers.Size(200, 200),
            contents,
            null, true, onPopupClose
        );
        feature.popup = popup;
        popup.feature = feature;
        map.addPopup(popup);
    }
    kmlLayer.events.on({ "featureselected": onKmlFeatureSelect, "featureunselected": onFeatureUnselect });
    
    */
    
});

Ext.preg(gxp.plugins.KMLSource.prototype.ptype, gxp.plugins.KMLSource);
