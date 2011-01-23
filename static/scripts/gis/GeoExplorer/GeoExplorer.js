/**
 * Copyright (c) 2009-2010 The Open Planning Project
 */

/**
 * Add transforms for EPSG:102113.  This is web mercator to ArcGIS 9.3.
 */
OpenLayers.Projection.addTransform(
    "EPSG:4326", "EPSG:102113",
    OpenLayers.Layer.SphericalMercator.projectForward
);
OpenLayers.Projection.addTransform(
    "EPSG:102113", "EPSG:4326",
    OpenLayers.Layer.SphericalMercator.projectInverse
);


/**
 * api: (define)
 * module = GeoExplorer
 * extends = Ext.Observable
 */

/** api: constructor
 *  .. class:: GeoExplorer(config)
 *     Create a new GeoExplorer application.
 *
 *     Parameters:
 *     config - {Object} Optional application configuration properties.
 *
 *     Valid config properties:
 *     map - {Object} Map configuration object.
 *     sources - {Object} An object with properties whose values are WMS endpoint URLs
 *     alignToGrid - {boolean} if true, align tile requests to the grid 
 *         enforced by tile caches such as GeoWebCache or Tilecache
 *
 *     Valid map config properties:
 *         projection - {String} EPSG:xxxx
 *         units - {String} map units according to the projection
 *         maxResolution - {Number}
 *         layers - {Array} A list of layer configuration objects.
 *         center - {Array} A two item array with center coordinates.
 *         zoom - {Number} An initial zoom level.
 *
 *     Valid layer config properties (WMS):
 *     name - {String} Required WMS layer name.
 *     title - {String} Optional title to display for layer.
 */
var GeoExplorer = Ext.extend(gxp.Viewer, {

    // Begin i18n.
    zoomSliderText: "<div>Zoom Level: {zoom}</div><div>Scale: 1:{scale}</div>",
    loadConfigErrorText: "Trouble reading saved configuration: <br />",
    loadConfigErrorDefaultText: "Server Error.",
    xhrTroubleText: "Communication Trouble: Status ",
    addLayersText: "Add Layers",
    removeLayerText: "Remove Layer",
    layersText: "Layers",
    overlaysText: "Overlays",
    baseLayersText: "Base Layers",
    layerPropertiesText: "Layer Properties",
    zoomToLayerExtentText: "Zoom to Layer Extent",
    legendText: "Legend",
    abstractTemplateText: "<p><b>Abstract:</b> {abstract}</p>",
    titleText: "Title",
    idText: "Id",
    viewDataText: "View available data from:",
    addServerText: "Add a New Server",
    layerSourceDefaultTitleText: "Untitled",
    addLayerSourceError1Text: "Error getting WMS capabilities (",
    addLayerSourceError2Text: ").\nPlease check the url and try again.",
    availableLayersText: "Available Layers",
    addLayersText: "Add Layers",
    doneText: "Done",
    zoomLevelText: "Zoom level",
    zoomPreviousText: "Zoom to Previous Extent",
    zoomNextText: "Zoom to Next Extent",
    featureInfoText: "Get Feature Info",
    switch3dText: "Switch to 3D Viewer",
    previewText: "Print Preview",
    printText: "Print Map",
    notAllNotPrintableText: "Not All Layers Can Be Printed", 
    nonePrintableText: "None of your current map layers can be printed",
    someNotPrintableText: "Some map layers cannot be printed: ",
    featureInfoText: "Feature Info",
    saveErrorText: "Trouble saving: ",
    bookmarkText: "Bookmark URL",
    permakinkText: 'Permalink',
    appInfoText: "GeoExplorer",
    aboutText: "About GeoExplorer",
    mapInfoText: "Map Info",
    descriptionText: "Description",
    contactText: "Contact",
    aboutThisMapText: "About this Map",
    // End i18n.
    
    /**
     * private: property[mapPanel]
     * the :class:`GeoExt.MapPanel` instance for the main viewport
     */
    mapPanel: null,

    /**
     * api: config[alignToGrid]
     * A boolean indicating whether or not to restrict tile request to tiled
     * mapping service recommendation.
     *
     * True => align to grid 
     * False => unrestrained tile requests
     */
    alignToGrid: false,
    
    /**
     * private: property[capGrid]
     * :class:`Ext.Window` The window containing the CapabilitiesGrid panel to 
     * use when the user is adding new layers to the map.
     */
    capGrid: null,

    constructor: function(config) {

        this.mapItems = [{
            xtype: "gx_zoomslider",
            vertical: true,
            height: 100,
            plugins: new GeoExt.ZoomSliderTip({
                template: this.zoomSliderText
            })
        }];

        this.toggleGroup = 'toolGroup';

        config.tools = [
            {
                ptype: "gxp_navigation", toggleGroup: this.toggleGroup,
                actionTarget: {target: "paneltbar", index: 6}
            }, {
                ptype: "gx_wmsgetfeatureinfo", toggleGroup: this.toggleGroup,
                actionTarget: {target: "paneltbar", index: 7}
            }, {
                ptype: "gxp_measure", toggleGroup: this.toggleGroup,
                actionTarget: {target: "paneltbar", index: 8}
            }, {
                ptype: "gxp_zoom",
                actionTarget: {target: "paneltbar", index: 9}
            }, {
                ptype: "gxp_navigationhistory",
                actionTarget: {target: "paneltbar", index: 11}
            }, {
                ptype: "gxp_zoomtoextent",
                actionTarget: {target: "paneltbar", index: 13}
            }
        ];
        
        GeoExplorer.superclass.constructor.apply(this, arguments);
    }, 
    
    loadConfig: function(config) {
        
        var mapUrl = window.location.hash.substr(1);
        var match = mapUrl.match(/^maps\/(\d+)$/);
        if (match) {
            this.id = Number(match[1]);
            OpenLayers.Request.GET({
                url: mapUrl,
                success: function(request) {
                    var addConfig = Ext.util.JSON.decode(request.responseText);
                    this.applyConfig(Ext.applyIf(addConfig, config));
                },
                failure: function(request) {
                    var obj;
                    try {
                        obj = Ext.util.JSON.decode(request.responseText);
                    } catch (err) {
                        // pass
                    }
                    var msg = this.loadConfigErrorText;
                    if (obj && obj.error) {
                        msg += obj.error;
                    } else {
                        msg += this.loadConfigErrorDefaultText;
                    }
                    this.on({
                        ready: function() {
                            this.displayXHRTrouble(msg, request.status);
                        },
                        scope: this
                    });
                    delete this.id;
                    window.location.hash = "";
                    this.applyConfig(config);
                },
                scope: this
            });
        } else {
            var query = Ext.urlDecode(document.location.search.substr(1));
            if (query && query.q) {
                var queryConfig = Ext.util.JSON.decode(query.q);
                Ext.apply(config, queryConfig);
            }
            this.applyConfig(config);
        }
        
    },
    
    displayXHRTrouble: function(msg, status) {
        
        Ext.Msg.show({
            title: this.xhrTroubleText + status,
            msg: msg,
            icon: Ext.MessageBox.WARNING
        });
        
    },
    
    /** private: method[initPortal]
     * Create the various parts that compose the layout.
     */
    initPortal: function() {
        
        // TODO: make a proper component out of this
        var mapOverlay = this.createMapOverlay();
        this.mapPanel.add(mapOverlay);
        
        var addLayerButton = new Ext.Button({
            tooltip : this.addLayersText,
            disabled: true,
            iconCls: "icon-addlayers",
            handler : this.showCapabilitiesGrid,
            scope: this
        });
        this.on("ready", function() {addLayerButton.enable();});
        
        var getRecordFromNode = function(node) {
            if(node && node.layer) {
                var layer = node.layer;
                var store = node.layerStore;
                record = store.getAt(store.findBy(function(r) {
                    return r.get("layer") === layer;
                }));
            }
            return record;
        };

        var getSelectedLayerRecord = function() {
            var node = layerTree.getSelectionModel().getSelectedNode();
            return getRecordFromNode(node);
        };
        
        var removeLayerAction = new Ext.Action({
            text: this.removeLayerText,
            iconCls: "icon-removelayers",
            disabled: true,
            tooltip: this.removeLayerText,
            handler: function() {
                var record = getSelectedLayerRecord();
                if(record) {
                    this.mapPanel.layers.remove(record);
                    removeLayerAction.disable();
                }
            },
            scope: this
        });

        var treeRoot = new Ext.tree.TreeNode({
            text: this.layersText,
            expanded: true,
            isTarget: false,
            allowDrop: false
        });
        treeRoot.appendChild(new GeoExt.tree.LayerContainer({
            text: this.baseLayersText,
            iconCls: "gx-folder",
            expanded: true,
            group: "background",
            loader: new GeoExt.tree.LayerLoader({
                baseAttrs: {checkedGroup: "background"},
                store: this.mapPanel.layers,
                filter: function(record) {
                    return record.get("group") === "background" &&
                        record.get("layer").displayInLayerSwitcher == true;
                },
                createNode: function(attr) {
                    var layer = attr.layer;
                    var store = attr.layerStore;
                    if (layer && store) {
                        var record = store.getAt(store.findBy(function(r) {
                            return r.get("layer") === layer;
                        }));
                        if (record) {
                            if (!record.get("queryable")) {
                                attr.iconCls = "gx-tree-rasterlayer-icon";
                            }
                            if (record.get("fixed")) {
                                attr.allowDrag = false;
                            }
                        }
                    }
                    return GeoExt.tree.LayerLoader.prototype.createNode.apply(this, arguments);
                }
            }),
            singleClickExpand: true,
            allowDrag: false,
            listeners: {
                append: function(tree, node) {
                    node.expand();
                }
            }
        }));
        
        treeRoot.appendChild(new GeoExt.tree.LayerContainer({
            text: this.overlaysText,
            iconCls: "gx-folder",
            expanded: true,
            loader: new GeoExt.tree.LayerLoader({
                store: this.mapPanel.layers,
                filter: function(record) {
                    return !record.get("group") &&
                        record.get("layer").displayInLayerSwitcher == true;
                },
                createNode: function(attr) {
                    var layer = attr.layer;
                    var store = attr.layerStore;
                    if (layer && store) {
                        var record = store.getAt(store.findBy(function(r) {
                            return r.get("layer") === layer;
                        }));
                        if (record && !record.get("queryable")) {
                            attr.iconCls = "gx-tree-rasterlayer-icon";
                        }
                    }
                    return GeoExt.tree.LayerLoader.prototype.createNode.apply(this, [attr]);
                }
            }),
            singleClickExpand: true,
            allowDrag: false,
            listeners: {
                append: function(tree, node) {
                    node.expand();
                }
            }
        }));
        
        this.treeRoot = treeRoot;
        
        var layerPropertiesDialog;
        var showPropertiesAction = new Ext.Action({
            text: this.layerPropertiesText,
            iconCls: "icon-properties",
            disabled: true,
            tooltip: this.layerPropertiesText,
            handler: function() {
                var record = getSelectedLayerRecord();
                if (record) {
                    var type = record.get("properties");
                    if (type) {
                        if(layerPropertiesDialog) {
                            layerPropertiesDialog.close();
                        }
                        layerPropertiesDialog = new Ext.Window({
                            title: this.layerPropertiesText + ": " + record.get("title"),
                            width: 250,
                            height: 250,
                            layout: "fit",
                            items: [{
                                xtype: type,
                                layerRecord: record,
                                defaults: {style: "padding: 10px"}
                            }]
                        });
                        layerPropertiesDialog.show();
                    }
                }
            },
            scope: this
        });
        
        var updateLayerActions = function(sel, node) {
            if(node && node.layer) {
                // allow removal if more than one non-vector layer
                var count = this.mapPanel.layers.queryBy(function(r) {
                    return !(r.get("layer") instanceof OpenLayers.Layer.Vector);
                }).getCount();
                if(count > 1) {
                    removeLayerAction.enable();
                } else {
                    removeLayerAction.disable();
                }
                var record = getRecordFromNode(node);
                if (record.get("properties")) {
                    showPropertiesAction.enable();                    
                } else {
                    showPropertiesAction.disable();
                }
            } else {
                removeLayerAction.disable();
                showPropertiesAction.disable();
            }
        };

        var layerTree = new Ext.tree.TreePanel({
            root: treeRoot,
            rootVisible: false,
            border: false,
            enableDD: true,
            selModel: new Ext.tree.DefaultSelectionModel({
                listeners: {
                    beforeselect: updateLayerActions,
                    scope: this
                }
            }),
            listeners: {
                contextmenu: function(node, e) {
                    if(node && node.layer) {
                        node.select();
                        var c = node.getOwnerTree().contextMenu;
                        c.contextNode = node;
                        c.showAt(e.getXY());
                    }
                },
                beforemovenode: function(tree, node, oldParent, newParent, index) {
                    // change the group when moving to a new container
                    if(oldParent !== newParent) {
                        var store = newParent.loader.store;
                        var index = store.findBy(function(r) {
                            return r.getLayer() === node.layer;
                        });
                        if (index > -1) {
                            store.getAt(index).set("group", newParent.attributes.group);
                        }
                    }
                },                
                scope: this
            },
            contextMenu: new Ext.menu.Menu({
                items: [
                    {
                        text: this.zoomToLayerExtentText,
                        iconCls: "icon-zoom-to",
                        handler: function() {
                            var node = layerTree.getSelectionModel().getSelectedNode();
                            if (node && node.layer) {
                                var map = this.mapPanel.map;
                                var layer = node.layer;
                                var extent = layer.restrictedExtent || layer.maxExtent || map.maxExtent;
                                map.zoomToExtent(extent, true);
                            }
                        },
                        scope: this
                    },
                    removeLayerAction,
                    showPropertiesAction
                ]
            })
        });
        
        var layersContainer = new Ext.Panel({
            autoScroll: true,
            border: false,
            region: 'center',
            title: this.layersText,
            items: [layerTree],
            tbar: [
                addLayerButton,
                Ext.apply(new Ext.Button(removeLayerAction), {text: ""}),
                Ext.apply(new Ext.Button(showPropertiesAction), {text: ""})
            ]
        });

        var legendContainer = new GeoExt.LegendPanel({
            title: this.legendText,
            border: false,
            region: 'south',
            height: 200,
            collapsible: true,
            split: true,
            autoScroll: true,
            ascending: false,
            map: this.mapPanel.map,
            defaults: {cls: 'legend-item'}
            // TODO: remove when http://trac.geoext.org/ticket/305 is fixed
            //,items: []
        });        

        var westPanel = new Ext.Panel({
            border: true,
            layout: "border",
            region: "west",
            width: 250,
            split: true,
            collapsible: true,
            collapseMode: "mini",
            header: false,
            items: [
                layersContainer, legendContainer
            ]
        });
        
        this.toolbar = new Ext.Toolbar({
            disabled: true,
            id: 'paneltbar',
            items: this.createTools()
        });
        this.on("ready", function() {
            // enable only those items that were not specifically disabled
            var disabled = this.toolbar.items.filterBy(function(item) {
                return item.initialConfig && item.initialConfig.disabled;
            });
            this.toolbar.enable();
            disabled.each(function(item) {
                item.disable();
            });
        });

        var googleEarthPanel = new gxp.GoogleEarthPanel({
            mapPanel: this.mapPanel,
            listeners: {
                beforeadd: function(record) {
                    return record.get("group") !== "background";
                }
            }
        });

        googleEarthPanel.on("show", function() {
            if (layersContainer.rendered) {
                layersContainer.getTopToolbar().disable();
            }
            layerTree.getSelectionModel().un("beforeselect", updateLayerActions, this);
        }, this);

        googleEarthPanel.on("hide", function() {
            if (layersContainer.rendered) {
                layersContainer.getTopToolbar().enable();
            }
            var sel = layerTree.getSelectionModel();
            var node = sel.getSelectedNode();
            updateLayerActions.apply(this, [sel, node]);
            sel.on(
                "beforeselect", updateLayerActions, this
            );
        }, this);

        this.mapPanelContainer = new Ext.Panel({
            layout: "card",
            region: "center",
            defaults: {
                border: false
            },
            items: [
                this.mapPanel,
                // This needs commenting out to be able to open with Firebug open
                googleEarthPanel
            ],
            activeItem: 0
        });
        
        this.portalItems = [{
            region: "center",
            layout: "border",
            tbar: this.toolbar,
            items: [
                this.mapPanelContainer,
                westPanel
            ]
        }];
        
        GeoExplorer.superclass.initPortal.apply(this, arguments);        
    },
    
    /**
     * private: method[initCapGrid]
     * Constructs a window with a capabilities grid.
     */
    initCapGrid: function() {
        
        var source, data = [];        
        for (var id in this.layerSources) {
            source = this.layerSources[id];
            if (source.store) {
                data.push([id, this.layerSources[id].title || id]);                
            }
        }
        var sources = new Ext.data.ArrayStore({
            fields: ["id", "title"],
            data: data
        });

        var expander = new Ext.grid.RowExpander({
            tpl: new Ext.Template(this.abstractTemplateText)
        });
        
        var addLayers = function() {
            var key = sourceComboBox.getValue();
            var layerStore = this.mapPanel.layers;
            var source = this.layerSources[key];
            var records = capGridPanel.getSelectionModel().getSelections();
            var record;
            for (var i=0, ii=records.length; i<ii; ++i) {
                record = source.createLayerRecord({
                    name: records[i].get("name"),
                    source: key
                });
                if (record) {
                    if (record.get("group") === "background") {
                        layerStore.insert(0, [record]);
                    } else {
                        layerStore.add([record]);
                    }
                }
            }
        };

        var capGridPanel = new Ext.grid.GridPanel({
            store: this.layerSources[data[0][0]].store,
            layout: "fit",
            region: "center",
            autoScroll: true,
            autoExpandColumn: "title",
            plugins: [expander],
            colModel: new Ext.grid.ColumnModel([
                expander,
                {id: "title", header: this.titleText, dataIndex: "title", sortable: true},
                {header: this.idText, dataIndex: "name", width: 150, sortable: true}
            ]),
            listeners: {
                rowdblclick: addLayers,
                scope: this
            }
        });
        
        var sourceComboBox = new Ext.form.ComboBox({
            store: sources,
            valueField: "id",
            displayField: "title",
            triggerAction: "all",
            editable: false,
            allowBlank: false,
            forceSelection: true,
            mode: "local",
            value: data[0][0],
            listeners: {
                select: function(combo, record, index) {
                    var store = this.layerSources[record.get("id")].store;
                    capGridPanel.reconfigure(store, capGridPanel.getColumnModel());
                    // TODO: remove the following when this Ext issue is addressed
                    // http://www.extjs.com/forum/showthread.php?100345-GridPanel-reconfigure-should-refocus-view-to-correct-scroller-height&p=471843
                    capGridPanel.getView().focusRow(0);
                },
                scope: this
            }
        });
        
        var capGridToolbar = null;
        if (this.proxy || data.length > 1) {
            capGridToolbar = [
                new Ext.Toolbar.TextItem({
                    text: this.viewDataText
                }),
                sourceComboBox
            ];
        }
        
        if (this.proxy) {
            capGridToolbar.push("-", new Ext.Button({
                text: this.addServerText,
                iconCls: "icon-addserver",
                handler: function() {
                    newSourceWindow.show();
                }
            }));
        }
        
        var newSourceWindow = new GeoExplorer.NewSourceWindow({
            modal: true,
            listeners: {
                "server-added": function(url) {
                    newSourceWindow.setLoading();
                    this.addLayerSource({
                        config: {url: url}, // assumes default of gx_wmssource
                        callback: function(id) {
                            // add to combo and select
                            var record = new sources.recordType({
                                id: id,
                                title: this.layerSources[id].title || this.layerSourceDefaultTitleText // TODO: titles
                            });
                            sources.insert(0, [record]);
                            sourceComboBox.onSelect(record, 0);
                            newSourceWindow.hide();
                        },
                        fallback: function(source, msg) {
                            newSourceWindow.setError(
                                this.addLayerSourceError1Text + msg + this.addLayerSourceError2Text
                            );
                        },
                        scope: this
                    });
                },
                scope: this
            }
        });

        this.capGrid = new Ext.Window({
            title: this.availableLayersText,
            closeAction: "hide",
            layout: "border",
            height: 300,
            width: 450,
            modal: true,
            items: [capGridPanel],
            tbar: capGridToolbar,
            bbar: [
                "->",
                new Ext.Button({
                    text: this.addLayersText,
                    iconCls: "icon-addlayers",
                    handler: addLayers,
                    scope : this
                }),
                new Ext.Button({
                    text: this.doneText,
                    handler: function() {
                        this.capGrid.hide();
                    },
                    scope: this
                })
            ],
            listeners: {
                hide: function(win){
                    capGridPanel.getSelectionModel().clearSelections();
                }
            }
        });
 
    },

    /** private: method[showCapabilitiesGrid]
     * Shows the window with a capabilities grid.
     */
    showCapabilitiesGrid: function() {
        if(!this.capGrid) {
            this.initCapGrid();
        }
        this.capGrid.show();
    },

    /** private: method[createMapOverlay]
     * Builds the :class:`Ext.Panel` containing components to be overlaid on the
     * map, setting up the special configuration for its layout and 
     * map-friendliness.
     */
    createMapOverlay: function() {
        var scaleLinePanel = new Ext.BoxComponent({
            autoEl: {
                tag: "div",
                cls: "olControlScaleLine overlay-element overlay-scaleline"
            }
        });

        scaleLinePanel.on('render', function(){
            var scaleLine = new OpenLayers.Control.ScaleLine({
                div: scaleLinePanel.getEl().dom
            });

            this.mapPanel.map.addControl(scaleLine);
            scaleLine.activate();
        }, this);

        var zoomStore = new GeoExt.data.ScaleStore({
            map: this.mapPanel.map
        });

        var zoomSelector = new Ext.form.ComboBox({
            emptyText: this.zoomLevelText,
            tpl: '<tpl for="."><div class="x-combo-list-item">1 : {[parseInt(values.scale)]}</div></tpl>',
            editable: false,
            triggerAction: 'all',
            mode: 'local',
            store: zoomStore,
            width: 110
        });

        zoomSelector.on({
            click: function(evt) {
                evt.stopEvent();
            },
            mousedown: function(evt) {
                evt.stopEvent();
            },
            select: function(combo, record, index) {
                this.mapPanel.map.zoomTo(record.data.level);
            },
            scope: this
        })

        var zoomSelectorWrapper = new Ext.Panel({
            items: [zoomSelector],
            cls: 'overlay-element overlay-scalechooser',
            border: false 
        });

        this.mapPanel.map.events.register('zoomend', this, function() {
            var scale = zoomStore.queryBy(function(record) {
                return this.mapPanel.map.getZoom() == record.data.level;
            }, this);

            if (scale.length > 0) {
                scale = scale.items[0];
                zoomSelector.setValue("1 : " + parseInt(scale.data.scale, 10));
            } else {
                if (!zoomSelector.rendered) {
                    return;
                }
                zoomSelector.clearValue();
            }
        });

        var mapOverlay = new Ext.Panel({
            // title: "Overlay",
            cls: 'map-overlay',
            items: [
                scaleLinePanel,
                zoomSelectorWrapper
            ]
        });


        mapOverlay.on("afterlayout", function(){
            scaleLinePanel.getEl().dom.style.position = 'relative';
            scaleLinePanel.getEl().dom.style.display = 'inline';

            mapOverlay.getEl().on("click", function(x){x.stopEvent();});
            mapOverlay.getEl().on("mousedown", function(x){x.stopEvent();});
        }, this);

        return mapOverlay;
    },

    /** private: method[createTools]
     * Create the toolbar configuration for the main panel.  This method can be 
     * overridden in derived explorer classes such as :class:`GeoExplorer.Composer`
     * or :class:`GeoExplorer.Viewer` to provide specialized controls.
     */
    createTools: function() {
        

        var toolGroup = this.toggleGroup;

        var enable3DButton = new Ext.Button({
            iconCls: "icon-3D",
            tooltip: this.switch3dText,
            enableToggle: true,
            toggleHandler: function(button, state) {
                if (state === true) {
                    this.mapPanelContainer.getLayout().setActiveItem(1);
                    this.toolbar.disable();
                    button.enable();
                } else {
                    this.mapPanelContainer.getLayout().setActiveItem(0);
                    this.toolbar.enable();
                }
            },
            scope: this
        });
    
        var tools = [
            this.printService && this.createPrintButton() || "-",
            "-",
            enable3DButton
        ];

        return tools;
    },
    
    /**
     * Candidate for a shared gxp action.
     * TODO: push some part of this to gxp (preferably less tangled)
     */
    createPrintButton: function() {

        var printProvider = new GeoExt.data.PrintProvider({
            url: this.printService,
            listeners: {
                beforeprint: function() {
                    // The print module does not like array params.
                    //TODO Remove when http://trac.geoext.org/ticket/216 is fixed.
                    printWindow.items.get(0).printMapPanel.layers.each(function(l) {
                        var params = l.get("layer").params;
                        for(var p in params) {
                            if (params[p] instanceof Array) {
                                params[p] = params[p].join(",");
                            }
                        }
                    })
                },
                loadcapabilities: function() {
                    // TODO: http://trac.geoext.org/ticket/304
                    // so we don't have to race to define the button
                    printButton.initialConfig.disabled = false;
                    printButton.disabled = false;
                    printButton.enable();
                },
                print: function() {
                    try {
                        printWindow.close();                        
                    } catch (err) {
                        // TODO: improve destroy
                    }
                }
            }
        });
        
        var unsupportedLayers;
        var printWindow;
        var someSupportedLayers;
        
        function destroyPrintComponents() {
            if (printWindow) {
                // TODO: fix this in GeoExt
                try {
                    var panel = printWindow.items.first();
                    panel.printMapPanel.printPage.destroy();
                    //panel.printMapPanel.destroy();                    
                } catch (err) {
                    // TODO: improve destroy
                }
                printWindow = null;
            }
        }

        function createPrintWindow() {
            someSupportedLayers = false;
            unsupportedLayers = [];
            printWindow = new Ext.Window({
                title: this.previewText,
                modal: true,
                border: false,
                resizable: false,
                width: 360,
                items: [
                    new GeoExt.ux.PrintPreview({
                        autoHeight: true,
                        mapTitle: this.about["title"],
                        comment: this.about["abstract"],
                        printMapPanel: {
                            map: Ext.applyIf({
                                controls: [
                                    new OpenLayers.Control.Navigation(),
                                    new OpenLayers.Control.PanPanel(),
                                    new OpenLayers.Control.ZoomPanel(),
                                    new OpenLayers.Control.Attribution()
                                ],
                                eventListeners: {
                                    preaddlayer: function(evt) {
                                        if (!(evt.layer instanceof OpenLayers.Layer.WMS) && !(evt.layer instanceof OpenLayers.Layer.OSM)) {
                                            // special treatment for "None" layer
                                            if (evt.layer.CLASS_NAME !== "OpenLayers.Layer") {
                                                unsupportedLayers.push(evt.layer.name);
                                            }
                                            return false;
                                        } else {
                                            someSupportedLayers = true;
                                        }
                                    },
                                    scope: this
                                }
                            }, this.mapPanel.initialConfig.map),
                            items: [{
                                xtype: "gx_zoomslider",
                                vertical: true,
                                height: 100,
                                aggressive: true
                            }]
                        },
                        printProvider: printProvider,
                        includeLegend: false,
                        sourceMap: this.mapPanel
                    })
                ],
                listeners: {
                    beforedestroy: destroyPrintComponents
                }
            }); 
        }
        
        function showPrintWindow() {
            printWindow.show();
            
            // measure the window content width by it's toolbar
            printWindow.setWidth(0);
            var tb = printWindow.items.get(0).items.get(0);
            var w = 0;
            tb.items.each(function(item) {
                if(item.getEl()) {
                    w += item.getWidth();
                }
            });
            printWindow.setWidth(
                Math.max(printWindow.items.get(0).printMapPanel.getWidth(),
                w + 20)
            );
            printWindow.center();            
        }

        var printButton = new Ext.Button({
            tooltip: this.printText,
            iconCls: "icon-print",
            disabled: true,
            handler: function() {
                createPrintWindow.call(this);
                if (!someSupportedLayers) {
                    Ext.Msg.alert(
                        this.notAllPrintableText, 
                        this.nonePrintableText
                    );
                    destroyPrintComponents();
                } else {
                    if (unsupportedLayers.length) {
                        Ext.Msg.alert(
                            this.notAllPrintableText, 
                            this.someNotPrintableText + "<ul><li>" + unsupportedLayers.join("</li><li>") + "</li></ul>",
                            showPrintWindow,
                            this
                        );                    
                    } else {
                        showPrintWindow.call(this);
                    }                    
                }

            },
            scope: this
        });

        return printButton;      
    },

    /** private: method[save]
     *
     * Saves the map config and displays the URL in a window.
     */ 
    save: function(callback, scope) {
        var configStr = Ext.util.JSON.encode(this.getState());
        var method, url;
        if (this.id) {
            method = "PUT";
            url = "maps/" + this.id;
        } else {
            method = "POST";
            url = "maps"
        }
        OpenLayers.Request.issue({
            method: method,
            url: url,
            data: configStr,
            callback: function(request) {
                this.handleSave(request);
                if (callback) {
                    callback.call(scope || this);
                }
            },
            scope: this
        });
    },
        
    /** private: method[handleSave]
     *  :arg: ``XMLHttpRequest``
     */
    handleSave: function(request) {
        if (request.status == 200) {
            var config = Ext.util.JSON.decode(request.responseText);
            var mapId = config.id;
            if (mapId) {
                this.id = mapId;
                window.location.hash = "#maps/" + mapId;
            }
        } else {
            throw this.saveErrorText + request.responseText;
        }
    },
    
    /** private: method[showUrl]
     */
    showUrl: function() {
        var win = new Ext.Window({
            title: this.bookmarkText,
            layout: 'form',
            labelAlign: 'top',
            modal: true,
            bodyStyle: "padding: 5px",
            width: 300,
            items: [{
                xtype: 'textfield',
                fieldLabel: this.permakinkText,
                readOnly: true,
                anchor: "100%",
                selectOnFocus: true,
                value: window.location.href
            }]
        });
        win.show();
        win.items.first().selectText();
    },
    
    /** api: method[getBookmark]
     *  :return: ``String``
     *
     *  Generate a bookmark for an unsaved map.
     */
    getBookmark: function() {
        var params = Ext.apply(
            OpenLayers.Util.getParameters(),
            {q: Ext.util.JSON.encode(this.getState())}
        );
        
        // disregard any hash in the url, but maintain all other components
        var url = 
            document.location.href.split("?").shift() +
            "?" + Ext.urlEncode(params);
        
        return url;
    },

    /** private: method[displayAppInfo]
     * Display an informational dialog about the application.
     */
    displayAppInfo: function() {
        var appInfo = new Ext.Panel({
            title: this.appInfoText,
            html: "<iframe style='border: none; height: 100%; width: 100%' src='about.html' frameborder='0' border='0'><a target='_blank' href='about.html'>"+this.aboutText+"</a> </iframe>"
        });

        var about = Ext.applyIf(this.about, {
            title: '', 
            "abstract": '', 
            contact: ''
        });

        var mapInfo = new Ext.Panel({
            title: this.mapInfoText,
            html: '<div class="gx-info-panel">' +
                  '<h2>'+this.titleText+'</h2><p>' + about.title +
                  '</p><h2>'+this.descriptionText+'</h2><p>' + about['abstract'] +
                  '</p> <h2>'+this.contactText+'</h2><p>' + about.contact +'</p></div>',
            height: 'auto',
            width: 'auto'
        });

        var tabs = new Ext.TabPanel({
            activeTab: 0,
            items: [mapInfo, appInfo]
        });

        var win = new Ext.Window({
            title: this.aboutThisMapText,
            modal: true,
            layout: "fit",
            width: 300,
            height: 300,
            items: [tabs]
        });
        win.show();
    }
});

