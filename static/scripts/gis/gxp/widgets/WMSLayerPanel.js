/**
 * Copyright (c) 2008-2011 The Open Planning Project
 * 
 * Published under the BSD license.
 * See https://github.com/opengeo/gxp/raw/master/license.txt for the full text
 * of the license.
 */

/** api: (define)
 *  module = gxp
 *  class = WMSLayerPanel
 *  base_link = `Ext.TabPanel <http://extjs.com/deploy/dev/docs/?class=Ext.TabPanel>`_
 */
Ext.namespace("gxp");

/** api: constructor
 *  .. class:: WMSLayerPanel(config)
 *   
 *      Create a dialog for setting WMS layer properties like title, abstract,
 *      opacity, transparency and image format.
 */
gxp.WMSLayerPanel = Ext.extend(Ext.TabPanel, {
    
    /** api: config[layerRecord]
     *  ``GeoExt.data.LayerRecord``
     *  Show properties for this layer record.
     */
    layerRecord: null,
    
    /** api: config[activeTab]
     *  ``String or Number``
     *  A string id or the numeric index of the tab that should be initially
     *  activated on render.  Defaults to ``0``.
     */
    activeTab: 0,
    
    /** api: config[border]
     *  ``Boolean``
     *  Display a border around the panel.  Defaults to ``false``.
     */
    border: false,
    
    /** api: config[imageFormats]
     *  ``RegEx`` Regular expression used to test browser friendly formats for
     *  GetMap requests.  The formats displayed will those from the record that
     *  match this expression.  Default is ``/png|gif|jpe?g/i``.
     */
    imageFormats: /png|gif|jpe?g/i,
    
    /** i18n */
    aboutText: "About",
    titleText: "Title",
    nameText: "Name",
    descriptionText: "Description",
    displayText: "Display",
    opacityText: "Opacity",
    formatText: "Format",
    transparentText: "Transparent",
    cacheText: "Cache",
    cacheFieldText: "Use cached version",
    stylesText: "Styles",
    
    initComponent: function() {
        
        this.addEvents(
            /** api: event[change]
             *  Fires when the ``layerRecord`` is changed using this dialog.
             */
            "change"
        );
        this.items = [
            this.createAboutPanel(),
            this.createDisplayPanel()
        ];

        // only add the Cache panel if we know for sure the WMS is GeoServer
        // which has been integrated with GWC.
        if (this.layerRecord.get("layer").params.TILED != null) {
            this.items.push(this.createCachePanel());
        }
        
        // only add the Styles panel if we know for sure that we have styles
        if (this.layerRecord.get("styles")) {
            var url = this.layerRecord.getLayer().url.split(
                "?").shift().replace(/\/(wms|ows)\/?$/, "/rest");
            this.items.push(this.createStylesPanel(url));
        }

        gxp.WMSLayerPanel.superclass.initComponent.call(this);
    },

    /** private: createCachePanel
     *  Creates the Cache panel.
     */
    createCachePanel: function() {
        return {
            title: this.cacheText,
            layout: "form",
            items: [{
                xtype: "checkbox",
                fieldLabel: this.cacheFieldText,
                checked: (this.layerRecord.get("layer").params.TILED === true),
                listeners: {
                    check: function(checkbox, checked) {
                        var layer = this.layerRecord.get("layer");
                        layer.mergeNewParams({
                            TILED: checked
                        });
                        this.fireEvent("change");
                    },
                    scope: this
                }
            }]    
        };
    },
    
    /** private: createStylesPanel
     *  :arg url: ``String`` url to save styles to
     *
     *  Creates the Styles panel.
     */
    createStylesPanel: function(url) {
        var layer = this.layerRecord.getLayer();
        return {
            title: this.stylesText,
            xtype: "gxp_wmsstylesdialog",
            layerRecord: this.layerRecord,
            plugins: [{
                ptype: "gxp_geoserverstylewriter",
                baseUrl: url
            }],
            listeners: {
                "beforerender": {
                    fn: function(cmp) {
                        Ext.Ajax.request({
                            method: "PUT",
                            url: url + "/styles",
                            callback: function(options, success, response) {
                                // we expect a 405 error code here if we are dealing with
                                // GeoServer and have write access. Otherwise we will
                                // create the panel in readonly mode.
                                cmp.editable = (response.status == 405);
                                cmp.ownerCt.doLayout();
                            }
                        });
                        return false;
                    },
                    single: true
                },
                "styleselected": function(cmp, style) {
                    cmp.modified && layer.mergeNewParams({
                        styles: style
                    });
                },
                "modified": function(cmp, style) {
                    cmp.saveStyles();
                },
                "saved": function(cmp, style) {
                    layer.mergeNewParams({
                        _olSalt: Math.random(),
                        styles: style
                    });
                }
            }
        }
    },
    
    /** private: createAboutPanel
     *  Creates the about panel.
     */
    createAboutPanel: function() {
        return {
            title: this.aboutText,
            style: {"padding": "10px"},
            defaults: {
                border: false
            },
            items: [{
                layout: "form",
                labelWidth: 70,
                items: [{
                    xtype: "textfield",
                    fieldLabel: this.titleText,
                    anchor: "99%",
                    value: this.layerRecord.get("title"),
                    listeners: {
                        change: function(field) {
                            this.layerRecord.set("title", field.getValue());
                            //TODO revisit when discussion on
                            // http://trac.geoext.org/ticket/110 is complete
                            this.layerRecord.commit();
                            this.fireEvent("change");
                        },
                        scope: this
                    }
                }, {
                    xtype: "textfield",
                    fieldLabel: this.nameText,
                    anchor: "99%",
                    value: this.layerRecord.get("name"),
                    readOnly: true
                }]
            }, {
                layout: "form",
                labelAlign: "top",
                items: [{
                    xtype: "textarea",
                    fieldLabel: this.descriptionText,
                    grow: true,
                    growMax: 150,
                    anchor: "99%",
                    value: this.layerRecord.get("abstract"),
                    readOnly: true
                }]
            }]
        };
    },
    
    /** private: createDisplayPanel
     *  Creates the display panel.
     */
    createDisplayPanel: function() {
        var record = this.layerRecord;
        var layer = record.getLayer();
        var opacity = layer.opacity;
        if(opacity == null) {
            opacity = 1;
        }
        var formats = [];
        var currentFormat = layer.params["FORMAT"].toLowerCase();
        Ext.each(record.get("formats"), function(format) {
            if(this.imageFormats.test(format)) {
                formats.push(format.toLowerCase());
            }
        }, this);
        if(formats.indexOf(currentFormat) === -1) {
            formats.push(currentFormat);
        }
        var transparent = layer.params["TRANSPARENT"];
        transparent = (transparent === "true" || transparent === true);
        
        return {
            title: this.displayText,
            style: {"padding": "10px"},
            layout: "form",
            labelWidth: 70,
            items: [{
                xtype: "slider",
                name: "opacity",
                fieldLabel: this.opacityText,
                value: opacity * 100,
                //TODO remove the line below when switching to Ext 3.2 final
                values: [opacity * 100],
                anchor: "99%",
                isFormField: true,
                listeners: {
                    change: function(slider, value) {
                        layer.setOpacity(value / 100);
                        this.fireEvent("change");
                    },
                    scope: this
                }
            }, {
                xtype: "combo",
                fieldLabel: this.formatText,
                store: formats,
                value: currentFormat,
                mode: "local",
                triggerAction: "all",
                editable: false,
                anchor: "99%",
                listeners: {
                    select: function(combo) {
                        layer.mergeNewParams({
                            format: combo.getValue()
                        });
                        this.fireEvent("change");
                    },
                    scope: this
                }
            }, {
                xtype: "checkbox",
                fieldLabel: this.transparentText,
                checked: transparent,
                listeners: {
                    check: function(checkbox, checked) {
                        layer.mergeNewParams({
                            transparent: checked ? "true" : "false"
                        });
                        this.fireEvent("change");
                    },
                    scope: this
                }
            }]
        };
    }    

});

Ext.reg('gxp_wmslayerpanel', gxp.WMSLayerPanel); 
