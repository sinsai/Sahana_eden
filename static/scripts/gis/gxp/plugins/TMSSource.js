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
 *  class = TMSSource
 */

/** api: (extends)
 *  plugins/LayerSource.js
 */
Ext.namespace("gxp.plugins");

/** api: constructor
 *  .. class:: TMSSource(config)
 *
 *    Plugin for using OpenStreetMap layers with :class:`gxp.Viewer` instances.
 *
 *    Available layer names include "mapnik" and "osmarender"
 */
/** api: example
 *  The configuration in the ``sources`` property of the :class:`gxp.Viewer` is
 *  straightforward:
 *
 *  .. code-block:: javascript
 *
 *    osm: {
 *        ptype: "gx_tmssource"
 *    }
 *
 *  A typical configuration for a layer from this source (in the ``layers``
 *  array of the viewer's ``map`` config option would look like this:
 *
 *  .. code-block:: javascript
 *
 *    {
 *        source: "osm",
 *        name: "osmarender"
 *    }
 *
 */
gxp.plugins.TMSSource = Ext.extend(gxp.plugins.LayerSource, {
    
    /** api: ptype = gx_tmssource */
    ptype: "gx_tmssource",

    /** api: property[store]
     *  ``GeoExt.data.LayerStore``. Will contain records with "mapnik" and
     *  "osmarender" as name field values.
     */
    
    /** api: config[title]
     *  ``String``
     *  A descriptive title for this layer source (i18n).
     */
    title: "OpenStreetMap Layers",
    
    /** api: config[osmAttribution]
     *  ``String``
     *  Attribution string for mapnik generated layer (i18n).
     */
    osmAttribution: "Data CC-By-SA by <a href='http://openstreetmap.org/' target='_blank'>OpenStreetMap</a>",

    /** api: config[cyclemapAttribution]
     *  ``String``
     *  Attribution string for cyclemap generated layer (i18n).
     */
    cyclemapAttribution: "Data CC-By-SA by <a href='http://www.opencyclemap.org/' target='_blank'>OpenCycleMap</a>",

    /** api: config[mapQuestAttribution]
     *  ``String``
     *  Attribution string for mapnik generated layer (i18n).
     */
    mapQuestAttribution: "Tiles Courtesy of <a href='http://open.mapquest.co.uk/' target='_blank'>MapQuest</a> <img src='http://developer.mapquest.com/content/osm/mq_logo.png' border='0'>",

    /** api: config[labelsAttribution]
     *  ``String``
     *  Attribution string for labels generated layer (i18n).
     */
    labelsAttribution: "Labels overlay CC-by-SA by <a href='http://oobrien.com/oom/' target='_blank'>OpenOrienteeringMap</a>",

    /** api: config[reliefAttribution]
     *  ``String``
     *  Attribution string for relief generated layer (i18n).
     */
    reliefAttribution: "Relief by <a href='http://hikebikemap.de/' target='_blank'>Hike &amp; Bike Map</a>",

    /** api: method[createStore]
     *
     *  Creates a store of layer records.  Fires "ready" when store is loaded.
     */
    createStore: function() {

        var options = {
            projection: "EPSG:900913",
            maxExtent: new OpenLayers.Bounds(
                -128 * 156543.0339, -128 * 156543.0339,
                128 * 156543.0339, 128 * 156543.0339
            ),
            maxResolution: 156543.0339,
            numZoomLevels: 19,
            units: "m",
            buffer: 1,
            type: 'png',
            getURL: this.getTileURL,
            displayOutsideMaxExtent: true
        };

        var layers = [
            new OpenLayers.Layer.TMS(
                "OpenStreetMap (Mapnik)",
                [
                    "http://a.tile.openstreetmap.org/",
                    "http://b.tile.openstreetmap.org/",
                    "http://c.tile.openstreetmap.org/"
                ],
                OpenLayers.Util.applyDefaults({                
                    attribution: this.osmAttribution,
                    layerType: "mapnik"
                }, options)
            ),
            new OpenLayers.Layer.TMS(
                "OpenStreetMap (CycleMap)",
                [
                    "http://a.tile.opencyclemap.org/cycle/",
                    "http://b.tile.opencyclemap.org/cycle/",
                    "http://c.tile.opencyclemap.org/cycle/"
                ],
                OpenLayers.Util.applyDefaults({                
                    attribution: this.cyclemapAttribution,
                    layerType: "cyclemap"
                }, options)
            ),
            new OpenLayers.Layer.TMS(
                "MapQuest",
                [
                    "http://otile1.mqcdn.com/tiles/1.0.0/osm/",
                    "http://otile2.mqcdn.com/tiles/1.0.0/osm/",
                    "http://otile3.mqcdn.com/tiles/1.0.0/osm/",
                    "http://otile4.mqcdn.com/tiles/1.0.0/osm/"
                ],
                OpenLayers.Util.applyDefaults({                
                    attribution: this.mapQuestAttribution,
                    type: "mapquest"
                }, options)
            ),
            new OpenLayers.Layer.TMS(
                "OpenStreetMap (Osmarender)",
                [
                    "http://a.tah.openstreetmap.org/Tiles/tile/",
                    "http://b.tah.openstreetmap.org/Tiles/tile/",
                    "http://c.tah.openstreetmap.org/Tiles/tile/"
                ],
                OpenLayers.Util.applyDefaults({                
                    attribution: this.osmAttribution,
                    layerType: "osmarender"
                }, options)
            ),
            new OpenLayers.Layer.TMS(
                "OpenStreetMap (Sahana)",
                [
                    "http://geo.eden.sahanafoundation.org/tiles/"
                ],
                OpenLayers.Util.applyDefaults({                
                    attribution: this.osmAttribution,
                    layerType: "sahana"
                }, options)
            ),
            new OpenLayers.Layer.TMS(
                "OpenStreetMap (Taiwan)",
                [
                    "http://tile.openstreetmap.tw/tiles/"
                ],
                OpenLayers.Util.applyDefaults({                
                    attribution: this.osmAttribution,
                    layerType: "taiwan"
                }, options)
            ),
            new OpenLayers.Layer.TMS(
                "OpenStreetMap (Labels)",
                [
                    "http://tiler1.censusprofiler.org/labelsonly/"
                ],
                OpenLayers.Util.applyDefaults({                
                    attribution: this.labelsAttribution,
                    layerType: "labels",
                    isBaseLayer: false,
                    group: "overlays"
                }, options)
            ),
            new OpenLayers.Layer.TMS(
                "OpenStreetMap (Relief)",
                [
                    "http://toolserver.org/~cmarqu/hill/"
                ],
                OpenLayers.Util.applyDefaults({                
                    attribution: this.reliefAttribution,
                    layerType: "relief",
                    isBaseLayer: false,
                    group: "overlays"
                }, options)
            )
        ];

        this.store = new GeoExt.data.LayerStore({
            layers: layers,
            fields: [
                {name: "source", type: "string"},
                {name: "name", type: "string", mapping: "layerType"},
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
    
    /** api: method[getTileURL]
     *  :arg bounds:  The bounds of the request.
     *  :returns: url
     *
     *  Create a TMS request given the bounds.
     */
    getTileURL: function(bounds) {
        var res = this.map.getResolution();
        var x = Math.round((bounds.left - this.maxExtent.left) / (res * this.tileSize.w));
        var y = Math.round((this.maxExtent.top - bounds.top) / (res * this.tileSize.h));
        var z = this.map.getZoom();
        var limit = Math.pow(2, z);
        if (y < 0 || y >= limit) {
            return OpenLayers.Util.getImagesLocation() + '404.png';
        } else {
            x = ((x % limit) + limit) % limit;
            var path = z + "/" + x + "/" + y + "." + this.type;
            var url = this.url;
            if (url instanceof Array) {
                url = this.selectUrl(path, url);
            }
            return url + path;
        }
    }

});

Ext.preg(gxp.plugins.TMSSource.prototype.ptype, gxp.plugins.TMSSource);
