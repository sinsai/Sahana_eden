/**
 * Copyright (c) 2008-2010 The Open Planning Project
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
 *  class = YahooSource
 */

/** api: (extends)
 *  plugins/LayerSource.js
 */
Ext.namespace("gxp.plugins");

/** api: constructor
 *  .. class:: YahooSource(config)
 *
 *    Plugin for using Yahoo layers with :class:`gxp.Viewer` instances. The
 *    plugin uses the YMaps v3.8 API and also takes care of loading the
 *    required Yahoo resources.
 *
 *    Available layer names for this source are "YAHOO_MAP_REG", "YAHOO_MAP_SAT" and
 *    "YAHOO_MAP_HYB"
 */   
/** api: example
 *  The configuration in the ``sources`` property of the :class:`gxp.Viewer` is
 *  straightforward:
 *
 *  .. code-block:: javascript
 *
 *    "yahoo": {
 *        ptype: "gx_yahoosource"
 *    }
 *
 *  A typical configuration for a layer from this source (in the ``layers``
 *  array of the viewer's ``map`` config option would look like this:
 *
 *  .. code-block:: javascript
 *
 *    {
 *        source: "yahoo",
 *        name: "YAHOO_MAP_HYB"
 *    }
 *
 */
gxp.plugins.YahooSource = Ext.extend(gxp.plugins.LayerSource, {
    
    /** api: ptype = gx_yahoosource */
    ptype: "gxp_yahoosource",
    
    /** config: config[timeout]
     *  ``Number``
     *  The time (in milliseconds) to wait before giving up on the Yahoo Maps
     *  script loading.  This layer source will not be available if the script
     *  does not load within the given timeout.  Default is 7000 (seven seconds).
     */
    timeout: 7000,

    /** api: property[store]
     *  ``GeoExt.data.LayerStore`` containing records with "YAHOO_MAP_REG",
     *  "YAHOO_MAP_SAT" and "HYAHOO_MAP_HYB" name fields.
     */
    
    /** api: config[title]
     *  ``String``
     *  A descriptive title for this layer source (i18n).
     */
    title: "Yahoo Layers",

    /** api: config[roadmapAbstract]
     *  ``String``
     *  Description of the YAHOO_MAP_REG layer (i18n).
     */
    roadmapAbstract: "Show street map",

    /** api: config[satelliteAbstract]
     *  ``String``
     *  Description of the YAHOO_MAP_SAT layer (i18n).
     */
    satelliteAbstract: "Show satellite imagery",

    /** api: config[hybridAbstract]
     *  ``String``
     *  Description of the YAHOO_MAP_HYB layer (i18n).
     */
    hybridAbstract: "Show imagery with street names",

    constructor: function(config) {
        this.config = config;
        gxp.plugins.YahooSource.superclass.constructor.apply(this, arguments);
    },
    
    /** api: config[apiKey]
     *  ``String``
     *  API key generated from http://developer.yahoo.com/maps/ for your domain.
     */
    apiKey: "euzuro-openlayers",
    
    /** api: method[createStore]
     *
     *  Creates a store of layer records.  Fires "ready" when store is loaded.
     */
    createStore: function() {        
        //if (gxp.plugins.YahooSource.monitor.ready) {
            this.syncCreateStore();
        //} else {
        //    gxp.plugins.YahooSource.monitor.on({
        //        ready: function() {
        //            this.syncCreateStore();
        //        },
        //        scope: this
        //    });
        //    if (!gxp.plugins.YahooSource.monitor.loading) {
        //        this.loadScript();
        //    }
        //}
    },
    
    /** private: method[syncCreateStore]
     *
     *  Creates a store of layers.  This requires that the API script has already
     *  loaded.  Fires the "ready" event when the store is loaded.
     */
    syncCreateStore: function() {
        var mapTypes = {
            "YAHOO_MAP_REG": {"abstract": this.roadmapAbstract, "name": "Roads"},
            "YAHOO_MAP_SAT": {"abstract": this.satelliteAbstract, "name": "Satellite"},
            "YAHOO_MAP_HYB": {"abstract": this.hybridAbstract, "name": "Hybrid"}
        };
        
        var layers = [];
        //var name;
        //for(var name in mapTypes) {
        //    layers.push(new OpenLayers.Layer.Yahoo(
        //        "Yahoo " + mapTypes[name]["name"], {
        //            type: name,
        //            'sphericalMercator': true
        //        }
        //    ))
        //}
        layers.push(new OpenLayers.Layer.Yahoo( 'Yahoo Satellite' , {type: YAHOO_MAP_SAT, 'sphericalMercator': true } ));
        this.store = new GeoExt.data.LayerStore({
            layers: layers,
            fields: [
                {name: "source", type: "string"},
                {name: "name", type: "string", mapping: "type"},
                {name: "abstract", type: "string"},
                {name: "group", type: "string", defaultValue: "background"},
                {name: "fixed", type: "boolean", defaultValue: true},
                {name: "selected", type: "boolean"}
            ]
        });
        this.store.each(function(l) {
            //l.set("abstract", mapTypes[l.get("name")]["abstract"]);
            l.set("group", "background");
            l.set("abstract", this.satelliteAbstract);
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
        var cmp = function(l) {
            return l.get("name") === config.name;
        };
        // only return layer if app does not have it already
        if (this.target.mapPanel.layers.findBy(cmp) == -1) {
            // records can be in only one store
            record = this.store.getAt(this.store.findBy(cmp)).clone();
            var layer = record.getLayer();
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
            record.commit();
        };
        return record;
    },
    
    loadScript: function() {

        //var script = document.createElement("script");
        //script.src = "http://api.maps.yahoo.com/ajaxymap?v=3.8&appid=" + this.apiKey;
        
        //http://www.bukisa.com/articles/183250_loading-the-on-demand-javascript-and-css-the-yui-way
        
        var options = {
            onSuccess: function(){
                //alert("YUI Get loaded the script resource successfully");
                gxp.plugins.GoogleSource.monitor.onScriptLoad();
            },
            onFailure: function(){
                //alert("YUI Get could not load the resource successfully");
            }
        };

        // @ToDo: Fix (fails to bootstrap - YAHOO not defined (even if yahoo-min.js has loaded)
        var script = YAHOO.util.Get.script("http://api.maps.yahoo.com/ajaxymap?v=3.8&appid=" + this.apiKey, options);

        // cancel loading if environment is not ready within timeout
        // Alternate option without callback: http://code.davidjanes.com/blog/2008/11/08/how-to-dynamically-load-map-apis/
        window.setTimeout(
            (function() {
                if (!gxp.plugins.YahooSource.monitor.ready) {
                    this.abortScriptLoad(script);
                }
            }).createDelegate(this), 
            this.timeout
        );
        
        //document.getElementsByTagName("head")[0].appendChild(script);

    },
    
    /** private: method[abortScriptLoad]
     *  :arg script: ``HTMLScriptElement``
     *
     *  Aborts the Yahoo Maps script loading by removing the script from the 
     *  document.  Fires the "failure" event.  Called if the script does not 
     *  load within the timeout.
     */
    abortScriptLoad: function(script) {
        document.getElementsByTagName("head")[0].removeChild(script);
        delete this.store;
        this.fireEvent(
            "failure", 
            this,
            "The Yahoo Maps script failed to load within the provided timeout (" + (this.timeout / 1000) + " s)."
        );
    }

});

/**
 * Create a monitor singleton that all plugin instances can use.
 */
gxp.plugins.YahooSource.monitor = new (Ext.extend(Ext.util.Observable, {

    /** private: property[ready]
     *  ``Boolean``
     *  This plugin type is ready to use.
     */
    ready: !!(window.YMapConfig),

    /** private: property[loading]
     *  ``Boolean``
     *  The resources for this plugin type are loading.
     */
    loading: false,
    
    constructor: function() {
        this.addEvents(
            /** private: event[ready]
             *  Fires when this plugin type is ready.
             */
             "ready"
        );
    },
    
    /** private: method[onScriptLoad]
     *  Called when all resources required by this plugin type have loaded.
     */
    onScriptLoad: function() {
        // the yahoo loader calls this in the window scope
        var monitor = gxp.plugins.YahooSource.monitor;
        if (!monitor.ready) {
            monitor.ready = true;
            monitor.loading = false;
            monitor.fireEvent("ready");
        }
    }

}))();

Ext.preg(gxp.plugins.YahooSource.prototype.ptype, gxp.plugins.YahooSource);
