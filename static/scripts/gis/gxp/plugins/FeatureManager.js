/**
 * Copyright (c) 2008-2011 The Open Planning Project
 * 
 * Published under the BSD license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

/**
 * @requires plugins/Tool.js
 */

/** api: (define)
 *  module = gxp.plugins
 *  class = FeatureManager
 */

/** api: (extends)
 *  plugins/Tool.js
 */
Ext.namespace("gxp.plugins");

/** api: constructor
 *  .. class:: FeatureManager(config)
 *
 *    Plugin for a shared feature manager that other tools can reference. Works
 *    on layers added by the :class:`gxp.plugins.WMSSource` plugin, if there is
 *    a WFS resource advertized in the layer's DescribeLayer document.
 *
 *    The FeatureManager handles WFS feature loading, filtering, paging and
 *    transactions.
 */   
gxp.plugins.FeatureManager = Ext.extend(gxp.plugins.Tool, {
    
    /** api: ptype = gx_featuremanager */
    ptype: "gx_featuremanager",
    
    /** api: config[maxFeatures]
     *  ``Number`` Default is 100
     */
    maxFeatures: 100,
    
    /** api: config[paging]
     *  ``Boolean`` Should quad-tree paging be enabled? Default is true.
     */
    paging: true,
    
    /** api: config[autoZoomPage]
     *  ``Boolean`` Set to true to always zoom the map to the currently
     *  selected page. Default is false.
     */
    autoZoomPage: false,

    /** api: config[autoSetLayer]
     *  ``Boolean`` When no ``layer`` is configured, listen to the viewer's
     *  layerselectionchange event to automatically set the layer. Default is
     *  true unless ``layer`` is configured.
     */
    autoSetLayer: true,
    
    /** api: config[layer]
     *  ``Object`` with source and name properties. The layer referenced here
     *  will be set as soon as it is added to the target's map. When this
     *  option is configured, ``autoSetLayer`` will be set to false.
     */

    /** api: config[autoLoadFeatures]
     *  ``Boolean`` Automatically load features after a new layer has been set?
     *  Default is false.
     */
    autoLoadFeatures: false,
    
    /** api: config[symbolizer]
     *  ``Object`` An object with "Point", "Line" and "Polygon" properties,
     *  each with a valid symbolizer object for OpenLayers. Will be used to
     *  render features.
     */
    
    /** api: config[format]
     *  ``String`` Optional response format to use for WFS GetFeature requests.
     *  Valid values are "GML2", "GML3" and "JSON". By default this is not set,
     *  which means that GML3 will be used.
     */
    
    /** api: property[layerRecord]
     *  ``GeoExt.data.LayerRecord`` The currently selected layer for this
     *  FeatureManager
     */
    layerRecord: null,
    
    /** api: property[featureStore]
     *  :class:`gxp.data.WFSFeatureStore` The FeatureStore that this tool
     *  manages.
     */
    featureStore: null,
    
    /** private: property[hitCountProtocol]
     *  ``OpenLayers.Protocol.WFS``
     */
    hitCountProtocol: null,
    
    /** api: property[featureLayer]
     *  ``OpenLayers.Layer.Vector`` The layer associated with this tool's
     *  featureStore.
     */
    featureLayer: null,
    
    /** api: property[schema]
     *  ``GeoExt.data.AttributeStore`` or false if the ``featureLayer`` has no
     *   associated WFS FeatureType, or null if no layer is currently selected.
     */
    schema: null,
    
    /** api: property[geometryType]
     *  ``String`` The geometry type of the featureLayer
     */
    geometryType: null,
    
    /** private: property[toolsShowingLayer]
     *  ``Object`` keyed by tool id - tools that currently need to show the
     *  layer. Each entry holds a String, which is either "default" or
     *  "invisible". Selected features will always be shown, and tools setting
     *  the style to "default" take precedence over tools that set it to
     *  "invisible".
     */
    toolsShowingLayer: null,
    
    /** private: property[style]
     *  ``Object`` with an "all" and a "selected" property, each holding an
     *  ``OpenLayers.Style``
     */
    style: null,
    
    /** private: property[pages]
     *  ``Array`` of page objects for paging mode
     */
    pages: null,
    
    /** private: property[page]
     *  ``Object`` The page currently loaded (for paging mode). Has extent
     *  and numFeatures properties
     */
    page: null,
    
    /** private: method[constructor]
     */
    constructor: function(config) {
        this.addEvents(
            /** api: event[beforequery]
             *  Fired before a WFS GetFeature request is issued. This event
             *  can be used to abort the loadFeatures method before any action
             *  is performed, by having a listener return false.
             *
             *  Listener arguments:
             *
             *  * tool   - :class:`gxp.plugins.FeatureManager` this tool
             *  * filter - ``OpenLayers.Filter`` the filter argument passed to
             *    the loadFeatures method
             *  * callback - ``Function`` the callback argument passed to the
             *    loadFeatures method
             *  * scope - ``Object`` the scope argument passed to the
             *    loadFeatures method
             */
            "beforequery",
            
            /** api: event[query]
             *  Fired after a WFS GetFeature query, when the results are
             *  available.
             *
             *  Listener arguments:
             *
             *  * tool  - :class:`gxp.plugins.FeatureManager` this tool
             *  * store - :class:`gxp.data.WFSFeatureStore`
             */
            "query",
            
            /** api: event[beforelayerchange]
             *  Fired before a layer change results in destruction of the
             *  current featureStore, and creation of a new one. This event
             *  can be used to abort the setLayer method before any action is
             *  performed, by having a listener return false.
             *
             *  Listener arguments:
             *
             *  * tool  - :class:`gxp.plugins.FeatureManager` this tool
             *  * layer - ``GeoExt.data.LayerRecord`` the layerRecord argument
             *    passed to the setLayer method
             */
            "beforelayerchange",
            
            /** api: event[layerchange]
             *  Fired after a layer change, as soon as the layer's schema is
             *  available and a ``featureStore`` has been created.
             *
             *  Listener arguments:
             *
             *  * tool   - :class:`gxp.plugins.FeatureManager` this tool
             *  * layer  - ``GeoExt.data.LayerRecord`` the new layer
             *  * schema - ``GeoExt.data.AttributeStore`` or false if the
             *    layer has no associated WFS FeatureType, or null if no layer
             *    is currently selected.
             */
            "layerchange",
            
            /** api: event[beforsetpage]
             *  Fired if paging is on, before a different page is requested. This
             *  event can be used to abort the setPage method before any action
             *  is performed, by having a listener return false.
             *
             *  Listener arguments:
             *
             *  * tool      - :class:`gxp.plugins.FeatureManager` this tool
             *  * condition - ``Object`` the condition passed to the setPage
             *    method
             *  * callback  - ``Function`` the callback argument passed to the
             *    setPage method
             *  * scope     - ``Object`` the scope argument passed to the
             *    setPage method
             */
            "beforesetpage",

            /** api: event[setpage]
             *  Fired if paging is on, when a different page is set, but before
             *  its features are loaded.
             *
             *  Listener arguments:
             *
             *  * tool      - :class:`gxp.plugins.FeatureManager` this tool
             *  * condition - ``Object`` the condition passed to the setPage
             *    method
             *  * callback  - ``Function`` the callback argument passed to the
             *    setPage method
             *  * scope     - ``Object`` the scope argument passed to the
             *    setPage method
             */
            "setpage"
        );
        
        // change autoSetLayer default if passed a layer config
        if (config && config.layer) {
            this.autoSetLayer = false;
        }
        
        gxp.plugins.FeatureManager.superclass.constructor.apply(this, arguments);        
    },
    
    /** private: method[init]
     */
    init: function(target) {
        gxp.plugins.FeatureManager.superclass.init.apply(this, arguments);
        this.toolsShowingLayer = {};
        
        this.style = {
            "all": new OpenLayers.Style(null, {
                rules: [new OpenLayers.Rule({
                    symbolizer: this.initialConfig.symbolizer || {
                        "Point": {
                            pointRadius: 4,
                            graphicName: "square",
                            fillColor: "white",
                            fillOpacity: 1,
                            strokeWidth: 1,
                            strokeOpacity: 1,
                            strokeColor: "#333333"
                        },
                        "Line": {
                            strokeWidth: 4,
                            strokeOpacity: 1,
                            strokeColor: "#ff9933"
                        },
                        "Polygon": {
                            strokeWidth: 2,
                            strokeOpacity: 1,
                            strokeColor: "#ff6633",
                            fillColor: "white",
                            fillOpacity: 0.3
                        }
                    }
                })]
            }),
            "selected": new OpenLayers.Style(null, {
                rules: [new OpenLayers.Rule({symbolizer: {display: "none"}})]
            })
        };
        
        this.featureLayer = new OpenLayers.Layer.Vector(this.id, {
            displayInLayerSwitcher: false,
            visibility: false,
            styleMap: new OpenLayers.StyleMap({
                "select": OpenLayers.Util.extend({display: ""},
                    OpenLayers.Feature.Vector.style["select"]),
                "vertex": this.style["all"]
            }, {extendDefault: false})    
        });
        
        this.target.on({
            ready: function() {
                this.target.mapPanel.map.addLayer(this.featureLayer);
            },
            scope: this
        });
        this.on({
            //TODO add a beforedestroy event to the tool
            beforedestroy: function() {
                this.target.mapPanel.map.removeLayer(this.featureLayer);
            },
            scope: this
        });
    },
    
    /** api: method[activate]
     *  :returns: ``Boolean`` true when this tool was activated
     *
     *  Activates this tool. When active, this tool loads the features for the
     *  configured layer, or listens to layer changes on the application and
     *  loads features for the selected layer.
     */
    activate: function() {
        if (gxp.plugins.FeatureManager.superclass.activate.apply(this, arguments)) {
            if (this.autoSetLayer) {
                this.target.on("beforelayerselectionchange", this.setLayer, this);
            }
            if (this.layer) {
                this.target.getLayerRecord(this.layer, this.setLayer, this);
            }
            this.on("layerchange", this.setSchema, this);
            return true;
        }
    },
    
    /** api: method[deactivate]
     *  :returns: ``Boolean`` true when this tool was deactivated
     *
     *  Dectivates this tool. When deactivated, this tool won't listen to layer
     *  changes on the application and load features for the selected layer.
     *  The current featureLayer will be cleared.
     */
    deactivate: function() {
        if (gxp.plugins.FeatureManager.superclass.deactivate.apply(this, arguments)) {
            if (this.autoSetLayer) {
                this.target.un("beforelayerselectionchange", this.setLayer, this);
            }
            this.un("layerchange", this.setSchema, this);
            this.setLayer();
            return true;
        }
    },
    
    /** api: method[setLayer]
     *  :arg layerRecord: ``GeoExt.data.LayerRecord``
     *  :returns: ``Boolean`` The layer was changed.
     *
     *  Sets the layer for this tool
     */
    setLayer: function(layerRecord) {
        var change = this.fireEvent("beforelayerchange", this, layerRecord);
        if (change !== false) {
            if (layerRecord !== this.layerRecord) {
                this.clearFeatureStore();
                this.layerRecord = layerRecord;
                if (layerRecord) {
                    this.autoLoadFeatures === true ?
                        this.loadFeatures() :
                        this.setFeatureStore();
                } else {
                    this.fireEvent("layerchange", this, null);
                }
            }
        }
        return change;
    },
    
    /** private: method[setSchema]
     *  :arg mgr: :class:`gxp.plugins.FeatureManager`
     *  :arg layer: ``GeoExt.data.LayerRecord``
     *  :arg schema: ``GeoExt.data.AttributeStore``
     */
    setSchema: function(mgr, layer, schema) {
        this.schema = schema;
    },
    
    /** api: method[showLayer]
     *  :arg id: ``String`` id of a tool that needs to show this tool's
     *      featureLayer.
     *  :arg display: ``String`` "all" or "selected". Optional, default is
     *      "all"
     */
    showLayer: function(id, display) {
        this.toolsShowingLayer[id] = display || "all";
        this.setLayerDisplay();
    },
    
    /** api: method[hideLayer]
     *  :arg id: ``String`` id of a tool that no longer needs to show this
     *      tool's featureLayer. The layer will be hidden if no more tools need
     *      to show it.
     */
    hideLayer: function(id) {
        delete this.toolsShowingLayer[id];
        this.setLayerDisplay();
    },
    
    /** private: mathod[setLayerDisplay]
     *  If ``toolsShowingLayer`` has entries, the layer will be added to the
     *  map, otherwise it will be removed. Tools can choose whether they want
     *  to display all features (display == "all") or only selected features
     *  (display == "selected"). If there are both tools that want to show all
     *  features and selected features, all features will be shown.
     */
    setLayerDisplay: function() {
        var show = false;
        for (var i in this.toolsShowingLayer) {
            if (show != "all") {
                show = this.toolsShowingLayer[i];
            }
        }
        var map = this.target.mapPanel.map;
        if (show) {
            var style = this.style[show];
            if (style !== this.featureLayer.styleMap.styles["default"]) {
                this.featureLayer.styleMap.styles["default"] = style;
                this.featureLayer.redraw();
            }
            this.featureLayer.setVisibility(true);
            map.events.on({
                addlayer: this.raiseLayer,
                scope: this
            });
        } else if (this.featureLayer.map) {
            this.featureLayer.setVisibility(false);
            map.events.un({
                addlayer: this.raiseLayer,
                scope: this
            });
        }
    },
    
    /** private: method[raiseLayer]
     *  Called whenever a layer is added to the map to keep this layer on top.
     */
    raiseLayer: function() {
        var map = this.featureLayer && this.featureLayer.map;
        if (map) {
            map.setLayerIndex(this.featureLayer, map.layers.length);
        }
    },
    
    /** api: method[loadFeatures]
     *  :arg filter: ``OpenLayers.Filter`` Optional filter for the GetFeature
     *      request.
     *  :arg callback: ``Function`` Optional callback to call when the
     *      features are loaded. This function will be called with the array
     *      of the laoded features (``OpenLayers.Feature.Vector``) as argument.
     *  :arg scope: ``Object`` Optional scope for the callback function.
     */
    loadFeatures: function(filter, callback, scope) {
        if (this.fireEvent("beforequery", this, filter, callback, scope) !== false) {
            this.filter = filter;
            this.pages = null;
            if (callback) {
                this.featureLayer.events.register(
                    "featuresadded", this, function(evt) {
                        if (this._query) {
                            delete this._query;
                            this.featureLayer.events.unregister(
                                "featuresadded", this, arguments.callee
                            );
                            callback.call(scope, evt.features);
                        }
                    }
                );
            }
            this._query = true;
            if (!this.featureStore) {
                this.paging && this.on("layerchange", function() {
                    this.setPage();
                }, this, {single: true});
                this.setFeatureStore(filter, !this.paging);
            } else {
                this.featureStore.setOgcFilter(filter);
                if (this.paging) {
                    this.setPage();
                } else {
                    this.featureStore.load();
                }
            };
        }
    },
    
    /** api: method[clearFeatures]
     *  Unload all features.
     */
    clearFeatures: function() {
        var store = this.featureStore;
        if (store) {
            store.removeAll();
            // TODO: make abort really work in OpenLayers
            var proxy = store.proxy;
            proxy.abortRequest();
            if (proxy.protocol.response) {
                proxy.protocol.response.abort();
            }
        }
    },
    
    /** private: method[setFeatureStore]
     *  :arg filter: ``OpenLayers.Filter``
     *  :arg autoLoad: ``Boolean``
     */
    setFeatureStore: function(filter, autoLoad) {
        var record = this.layerRecord;
        var source = this.target.getSource(record);
        if (source && source instanceof gxp.plugins.WMSSource) {
            source.getSchema(record, function(schema) {
                if (schema === false) {
                    this.clearFeatureStore();
                } else {
                    var fields = [], geometryName;
                    var geomRegex = /gml:((Multi)?(Point|Line|Polygon|Curve|Surface)).*/;
                    var types = {
                        "xsd:boolean": "boolean",
                        "xsd:int": "int",
                        "xsd:integer": "int",
                        "xsd:short": "int",
                        "xsd:long": "int",
                        "xsd:date": "date",
                        "xsd:string": "string",
                        "xsd:float": "float",
                        "xsd:double": "float"
                    };
                    schema.each(function(r) {
                        // TODO: To be more generic, we would look for GeometryPropertyType as well.
                        var match = geomRegex.exec(r.get("type"));
                        if (match) {
                            geometryName = r.get("name");
                            this.geometryType = match[1];
                        } else {
                            // TODO: use (and improve if needed) GeoExt.form.recordToField
                            var type = types[r.get("type")];
                            var field = {
                                name: r.get("name"),
                                type: types[type]
                            };
                            //TODO consider date type handling in OpenLayers.Format
                            if (type == "date") {
                                field.dateFormat = "Y-m-d\\Z";
                            }
                            fields.push(field);
                        }
                    }, this);
                    var protocolOptions = {
                        srsName: this.target.mapPanel.map.getProjection(),
                        url: schema.url,
                        featureType: schema.reader.raw.featureTypes[0].typeName,
                        featureNS: schema.reader.raw.targetNamespace,
                        geometryName: geometryName
                    };
                    this.hitCountProtocol = new OpenLayers.Protocol.WFS(Ext.apply({
                        version: "1.1.0",
                        readOptions: {output: "object"},
                        resultType: "hits",
                        filter: filter
                    }, protocolOptions));
                    this.featureStore = new gxp.data.WFSFeatureStore(Ext.apply({
                        fields: fields,
                        proxy: {
                            protocol: {
                                outputFormat: this.format 
                            }
                        },
                        maxFeatures: this.maxFeatures,
                        layer: this.featureLayer,
                        ogcFilter: filter,
                        autoLoad: autoLoad,
                        autoSave: false,
                        listeners: {
                            "write": function() {
                                record.getLayer().redraw(true);
                            },
                            "load": function() {
                                this.fireEvent("query", this, this.featureStore);
                            },
                            scope: this
                        }
                    }, protocolOptions));
                }
                this.fireEvent("layerchange", this, record, schema);
            }, this);
        } else {
            this.clearFeatureStore();
            this.fireEvent("layerchange", this, record, false);
        }        
    },
    
    /** private: method[clearFeatureStore]
     */
    clearFeatureStore: function() {
        if (this.featureStore) {
            //TODO remove when http://trac.geoext.org/ticket/367 is resolved
            this.featureStore.removeAll();
            this.featureStore.unbind();
            // end remove
            this.featureStore.destroy();
            this.featureStore = null;
            this.geometryType = null;
        }
    },

    /** private: method[processPage]
     *  :arg page: ``Object`` The page to process.
     *  :arg condition: ``Object`` Object with index, next or lonLat
     *      properties. See ``setPage``.
     *  :arg callback: ``Function`` Callback to call when the requested page
     *      is available. Called with the page as 1st argument.
     *  :arg scope: ``The scope for the callback.
     *
     *  Takes a page, which still may have more features than ``maxFeatures``
     *  in its extent, creates leaves if necessary, and returns the correct
     *  leaf in a callback function.
     */
    processPage: function (page, condition, callback, scope) {
        condition = condition || {};
        var index = condition.lonLat ? null : condition.index;
        var next = condition.next;
        var pages = this.pages;
        var i = this.pages.indexOf(page);
        this.setPageFilter(page);
        var nextOk = next ?
            i == (pages.indexOf(next) || pages.length) - 1 : true;
        var lonLatOk = condition.lonLat ?
            page.extent.containsLonLat(condition.lonLat) : true;
        if (lonLatOk && page.numFeatures && page.numFeatures <= this.maxFeatures) {
            // nothing to do, leaf is a valid page
            callback.call(this, page);
        } else if (lonLatOk && (i == index || nextOk)) {
            // get the hit count if the page is relevant for the requested index
            this.hitCountProtocol.read({
                callback: function(response) {
                    var i = index, lonLat = condition.lonLat;
                    if (next) {
                        i = (pages.indexOf(next) || pages.length) - 1;
                    }
                    if (!i && lonLat && page.extent.containsLonLat(lonLat)) {
                        i = pages.indexOf(page);
                    }
                    page.numFeatures = response.numberOfFeatures;
                    if (this.page) {
                        return;
                    }
                    if (page.numFeatures > this.maxFeatures) {
                        this.createLeaf(page, Ext.applyIf({
                            index: i,
                            next: next
                        }, condition), callback, scope);
                    } else if (page.numFeatures == 0 && pages.length > 1) {
                        // remove page, unless it's the only one (which means
                        // that loadFeatures returned no features)
                        pages.remove(page);
                        // move to the next page if the removed page would have
                        // been the one for our location
                        condition.allowEmpty === false && this.setPage({
                            index: index % this.pages.length,
                            allowEmpty: false
                        });
                    } else if (this.pages.indexOf(page) == i) {
                        callback.call(this, page);
                    }
                },
                scope: this
            });
        }
    },
    
    /** private: method[createLeaf]
     *  :arg page: ``Object`` The page to process.
     *  :arg condition: ``Object`` Object with index, next or lonLat
     *      properties. See ``setPage``.
     *  :arg callback: ``Function`` Callback to call when the requested page
     *      is available. Called with the page as 1st argument.
     *  :arg scope: ``The scope for the callback.
     *
     *  Creates the 4 leaves for a page, and calls processPage on each.
     */
    createLeaf: function(page, condition, callback, scope) {
        condition = condition || {};
        var layer = this.layerRecord.getLayer();
        var pageIndex = this.pages.indexOf(page);
        // replace the page with its 4 subpages, so we remove it first.
        this.pages.remove(page);
        var extent = page.extent;
        var center = extent.getCenterLonLat();
        var l = [extent.left, center.lon, extent.left, center.lon];
        var b = [center.lat, center.lat, extent.bottom, extent.bottom];
        var r = [center.lon, extent.right, center.lon, extent.right];
        var t = [extent.top, extent.top, center.lat, center.lat];
        var i, leaf;
        for (i=3; i>=0; --i) {
            leaf = {extent: new OpenLayers.Bounds(l[i], b[i], r[i], t[i])};
            this.pages.splice(pageIndex, 0, leaf);
            this.processPage(leaf, condition, callback, scope);
        }
    },
    
    /** private: method[getPagingExtent]
     *  :arg meth: ``String`` Method to call on the target's map when neither
     *      a filter extent nor a layer extent are available. Useful values
     *      are "getExtent" and "getMaxExtent".
     *  :returns: ``OpenLayers.Bounds`` the extent to use for paging
     *
     *  Gets the extent to use for the root of the paging quad-tree.
     */
    getPagingExtent: function(meth) {
        layer = this.layerRecord.getLayer();
        var filter;
        if (this.filter instanceof OpenLayers.Filter.Spatial && this.filter.type === OpenLayers.Filter.Spatial.BBOX) {
            filter = this.filter;
        } else if (this.filter instanceof OpenLayers.Filter.Logical && this.filter.type === OpenLayers.Filter.Logical.AND) {
            for (var f, i=this.filter.filters.length-1; i>=0; --i) {
                f = this.filter.filters[i];
                if (f instanceof OpenLayers.Filter.Spatial && f.type === OpenLayers.Filter.Spatial.BBOX) {
                    filter = f;
                    break;
                }
            }
        }
        var extent = filter && filter.value;
        return (extent && layer.maxExtent) ?
            extent.containsBounds(layer.maxExtent) ?
                layer.maxExtent :
                extent :
            (layer.maxExtent || this.target.mapPanel.map[meth]());
    },
    
    /** private: method[setPageFilter]
     *  :arg page: ``Object`` The page to create the filter for
     *  :returns: ``OpenLayers.Filter`` The filter to use for the provided page
     *
     *  Creates the filter for a page's extent. This wraps the query filter,
     *  if any.
     */
    setPageFilter: function(page) {
        var filter;
        if (page.extent) {
            var bboxFilter = new OpenLayers.Filter.Spatial({
                type: OpenLayers.Filter.Spatial.BBOX,
                property: this.featureStore.geometryName,
                value: page.extent
            });
            filter = this.filter ?
                new OpenLayers.Filter.Logical({
                    type: OpenLayers.Filter.Logical.AND,
                    filters: [this.filter, bboxFilter]
                }) : bboxFilter;
        } else {
            filter = this.filter;
        }
        this.featureStore.setOgcFilter(filter);
        //TODO the protocol could use a setFilter method
        this.hitCountProtocol.filter = filter;
        this.hitCountProtocol.options.filter = filter;
        return filter;
    },
    
    /** api: method[nextPage]
     *  :arg callback: ``Function`` Optional callback to call when the page
     *      is available. The callback will receive the page as 1st argument.
     *  :arg scope: ``Object`` Optional scope for the callback.
     *
     *  Load the next page.
     */
    nextPage: function(callback, scope) {
        var page = this.page;
        this.page = null;
        var index = (this.pages.indexOf(page) + 1) % this.pages.length;
        this.setPage({index: index, allowEmpty: false}, callback, scope);
    },
    
    /** api: method[previousPage]
     *  :arg callback: ``Function`` Optional callback to call when the page
     *      is available. The callback will receive the page as 1st argument.
     *  :arg scope: ``Object`` Optional scope for the callback.
     *
     *  Load the previous page.
     */
    previousPage: function(callback, scope) {
        var index = this.pages.indexOf(this.page) - 1;
        if (index < 0) {
            index = this.pages.length - 1;
        }
        this.setPage({index: index, allowEmpty: false, next: this.page}, callback);
    },
    
    /** api: method[setPage]
     *  :arg condition: ``Object`` Object to tell the method which page to set.
     *      If "lonLat" (``OpenLayers.LonLat``) is provided, the page
     *      containing the provided location will be loaded.
     *      If only an "index" property (pointing to a page in this tool's
     *      pages array) is provided, the method will load the according page
     *      if it has less then ``maxFeatures`` features. If it does not,
     *      leaves will be created until the top-left page has less than
     *      ``maxFeatures``, and this top-left page will be loaded. If index is
     *      "last", the last page of the quad-tree will be loaded. If an
     *      additional "next" property is provided (a page object is expected
     *      here), the page that would be loaded with ``previousPage`` called
     *      from the provided page will be set. This is the bottom-right page
     *      of the page pointed to with "index".
     *      If the resulting page would be empty, and "allowEmpty" is false,
     *      the next matching page will be loaded.
     *  :arg callback: ``Function`` Optional callback to call when the page
     *      is available. The callback will receive the page as 1st argument.
     *  :arg scope: ``Object`` Optional scope for the callback.
     *
     *  Sets and loads the page specified by the condition argument. This is
     *  usually used to load a page for a specific location, or to load the
     *  first or last page of the quad tree.
     *
     *  Sample code to load the page that contains the (0, 0) location:
     *
     *  .. code-block:: javascript
     *
     *      featureManager.setPage({lonLat: new OpenLayers.LonLat(0, 0)});
     *
     *  Sample code to load the first page of the quad-tree:
     *
     *  .. code-block:: javascript
     *
     *      featureManager.setPage({index: 0});
     *
     *  Sample code to load the last page of the quad-tree:
     *
     *  .. code-block:: javascript
     *
     *      featureManager.setPage({index: "last"});
     *
     *  Sample code to load the first page that contains features:
     *
     *  .. code-block:: javascript
     *
     *      featureManager.setPage();
     */
    setPage: function(condition, callback, scope) {
        if (this.filter instanceof OpenLayers.Filter.FeatureId) {
            // no paging for FeatureId filters - these cannot be combined with
            // BBOX filters
            this.featureStore.load({callback: callback, scope: scope});
            return;
        }
        if (this.fireEvent("beforesetpage", this, condition, callback, scope) !== false) {
            if (!condition) {
                // choose a page on the top left
                var extent = this.getPagingExtent("getExtent");
                condition = {
                    lonLat: new OpenLayers.LonLat(extent.left, extent.top),
                    allowEmpty: false
                };
            }
            condition.index = condition.index || 0;
            if (condition.index == "last") {
                condition.index = this.pages.length - 1;
                condition.next = this.pages[0];
            }
            this.page = null;
            if (!this.pages) {
                var layer = this.layerRecord.getLayer();
                var queryExtent = this.getPagingExtent("getMaxExtent");
                this.pages = [{extent: queryExtent}];
                condition.index = 0;
            } else if (condition.lonLat) {
                for (var i=this.pages.length-1; i>=0; --i) {
                    if (this.pages[i].extent.containsLonLat(condition.lonLat)) {
                        condition.index = i;
                        break;
                    }
                }
            }
            this.processPage(this.pages[condition.index], condition,
                function(page) {
                    var map = this.target.mapPanel.map;
                    this.page = page;
                    this.setPageFilter(page);
                    if (this.autoZoomPage && !map.getExtent().containsLonLat(page.extent.getCenterLonLat())) {
                        map.zoomToExtent(page.extent);
                    }
                    this.fireEvent("setpage", this, condition, callback, scope);
                    this.featureStore.load({callback: callback, scope: scope});
                }, this
            );
        }
    }
    
});

Ext.preg(gxp.plugins.FeatureManager.prototype.ptype, gxp.plugins.FeatureManager);
