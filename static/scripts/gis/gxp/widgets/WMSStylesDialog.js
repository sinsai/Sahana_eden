/**
 * Copyright (c) 2010 The Open Planning Project
 */

/**
 * @include widgets/RulePanel.js
 * @include widgets/StylePropertiesDialog.js
 */

/** api: (define)
 *  module = gxp
 *  class = WMSStylesDialog
 *  base_link = `Ext.Container <http://extjs.com/deploy/dev/docs/?class=Ext.Container>`_
 */
Ext.namespace("gxp");

/** api: constructor
 *  .. class:: WMSStylesDialog(config)
 *   
 *      Create a dialog for selecting and layer styles. If the WMS supports
 *      GetStyles, styles can also be edited. The dialog does not provide any
 *      means of writing modified styles back to the server. To save styles,
 *      configure the dialog with a :class:`gxp.plugins.StyleWriter` plugin
 *      and use the plugin's ``write`` method.
 */
gxp.WMSStylesDialog = Ext.extend(Ext.Container, {

    //TODO create a StylesStore which can read styles using GetStyles. Create
    // subclasses for that store with writing capabilities, e.g.
    // for GeoServer's RESTconfig API. This should replace the current
    // StyleWriter plugins.
    
    /** api: config[layerRecord]
     *  ``GeoExt.data.LayerRecord`` The layer to edit/select styles for.
     */
    
    /** private: property[layerRecord]
     *  ``GeoExt.data.LayerRecord`` The layer to edit/select styles for.
     */
    layerRecord: null,
    
    /** api: config[styleName]
     *  ``String`` A style's name to select in the styles combo box. Optional.
     *  If not provided, the layer's current style will be selected.
     */
     
    /** api: config[applySelectedStyle]
     *  ``Boolean`` If set to true, the style selected in the styles combo
     *  will be applied to the layer. Note that once the selected style has
     *  been modified, it will no longer be applied. Default is false.
     */
    
    /** api: config[stylesComboOptions]
     *  ``Object`` configuration options to pass to the styles combo of this
     *  dialog. Optional.
     */
    
    /** api: config[layerDescription]
     *  ``Object`` Array entry of a DescribeLayer response as read by
     *      ``OpenLayers.Format.WMSDescribeLayer``. Optional. If not provided,
     *      a DescribeLayer request will be issued to the WMS.
     */
    
    /** private: property[layerDescription]
     *  ``Object`` Array entry of a DescribeLayer response as read by
     *      ``OpenLayers.Format.WMSDescribeLayer``.
     */
    layerDescription: null,
    
    /** private: property[symbolType]
     *  ``Point`` or ``Line`` or ``Polygon`` - the primary symbol type for the
     *  layer. This is the symbolizer type of the first symbolizer of the
     *  first rule of the current layer style. Only available if the WMS
     *  supports GetStyles.
     */
    symbolType: null,
    
    /** api: property[stylesStore]
     *  ``Ext.data.Store`` A store representing the styles returned from
     *  GetCapabilities and GetStyles. It has "name", "title", "abstract",
     *  "legend" and "userStyle" fields. If the WMS supports GetStyles, the
     *  "legend" field will not be available. If it does not, the "userStyle"
     *  field will not be available.
     */
    stylesStore: null,
    
    /** api: property[selectedStyle]
     *  ``Ext.data.Record`` The currently selected style from the
     *  ``stylesStore``.
     */
    selectedStyle: null,
    
    /** private: property[selectedRule]
     *  ``OpenLayers.Rule`` The currently selected rule, or null if none
     *  selected.
     */
    selectedRule: null,
    
    /** api: config[editable]
     *  ``Boolean`` Set to false if styles should not be editable. Default is
     *  true.
     */
    
    /** api: property[editable]
     *  ``Boolean`` Read-only. True if this component could gather enough
     *  information to allow styles being edited, false otherwise. This is
     *  not supposed to be used before the  ``ready`` event is fired.
     */
    editable: true,
    
    /** private: property[isRaster]
     *  ``Boolean`` Are we dealing with a raster layer with RasterSymbolizer?
     *  This is needed because we create pseudo rules from a RasterSymbolizer's
     *  ColorMap, and for this we need special treatment in some places.
     */
    isRaster: null,
    
    /** private: property[modified]
     *  ``Boolean`` Will be true if styles were modified. Initial state is
     *  false.
     */
    modified: false,
        
    /** private: method[initComponent]
     */
    initComponent: function() {
        this.addEvents(
            /** api: event[ready]
             *  Fires when this component is ready for user interaction.
             */
            "ready",
            
            /** api: event[modified]
             *  Fires on the first style modification.
             */
            "modified",
            
            /** api: event[styleselected]
             *  Fires whenever a style is selected from this dialog's Style
             *  combo box.
             *  
             *  Listener arguments:
             *  * :class:`gxp.WMSStylesDialog` this component
             *  * ``String`` the name of the selected style
             */
            "styleselected",
            
            /** api: event[beforesaved]
             *  Fires before the styles are saved (using a
             *  :class:`gxp.plugins.StyleWriter` plugin)
             *
             *  Listener arguments:
             *  * :class:`gxp.WMSStylesDialog` this component
             *  * ``Object`` options for the ``write`` method of the
             *    :class:`gxp.plugins.StyleWriter`
             */
            "beforesaved",
            
            /** api: event[saved]
             *  Fires when a style was successfully saved.
             */
            "saved"            
        );

        var defConfig = {
            layout: "form",
            disabled: true,
            items: [{
                xtype: "fieldset",
                title: "Styles",
                labelWidth: 85,
                style: "margin-bottom: 0;"
            }, {
                xtype: "toolbar",
                style: "border-width: 0 1px 1px 1px; margin-bottom: 10px;",
                items: [
                    {
                        xtype: "button",
                        iconCls: "add",
                        text: "Add",
                        handler: this.addStyle,
                        scope: this
                    }, {
                        xtype: "button",
                        iconCls: "delete",
                        text: "Remove",
                        handler: function() {
                            this.stylesStore.remove(this.selectedStyle);
                        },
                        scope: this
                    }, {
                        xtype: "button",
                        iconCls: "edit",
                        text: "Edit",
                        handler: function() {
                            var userStyle = this.selectedStyle.get("userStyle");
                            var styleProperties = new Ext.Window({
                                title: "User Style: " + userStyle.name,
                                bodyBorder: false,
                                autoHeight: true,
                                width: 300,
                                modal: true,
                                items: {
                                    border: false,
                                    items: {
                                        xtype: "gx_stylepropertiesdialog",
                                        userStyle: userStyle.clone(),
                                        // styles that came from the server
                                        // have a name that we don't change
                                        nameEditable: this.selectedStyle.id !==
                                            this.selectedStyle.get("name"),
                                        style: "padding: 10px;"
                                    }
                                },
                                buttons: [{
                                    text: "Cancel",
                                    handler: function() {
                                        styleProperties.close();
                                    }
                                }, {
                                    text: "Save",
                                    handler: function() {
                                        var userStyle = 
                                        this.selectedStyle.set(
                                            "userStyle",
                                            styleProperties.items.get(0).items.get(0).userStyle);
                                        styleProperties.close();
                                    },
                                    scope: this
                                }]
                            });
                            styleProperties.show();
                        },
                        scope: this
                    }, {
                        xtype: "button",
                        iconCls: "duplicate",
                        text: "Duplicate",
                        handler: function() {
                            var newStyle = this.selectedStyle.get(
                                "userStyle").clone();
                            newStyle.isDefault = false;
                            newStyle.name = gxp.util.uniqueName(
                                newStyle.name + "_copy", "_");
                            var store = this.stylesStore;
                            store.add(new store.recordType({
                                "name": newStyle.name,
                                "title": newStyle.title,
                                "abstract": newStyle.description,
                                "userStyle": newStyle
                            }));
                        },
                        scope: this
                    }
                ]
            }]
        };
        Ext.applyIf(this, defConfig);
        
        this.createStylesStore();
                
        gxp.util.dispatch([this.getStyles, this.describeLayer], function() {
            this.enable();
        }, this)

        gxp.WMSStylesDialog.superclass.initComponent.apply(this, arguments);
    },
    
    /** api: method[addStyle]
     *  Creates a new style and selects it in the styles combo.
     */
    addStyle: function() {
        if(!this._ready) {
            this.on("ready", this.addStyle, this);
        }
        var store = this.stylesStore;
        var newStyle = new OpenLayers.Style(null, {
            name: gxp.util.uniqueName("New_Style", "_"),
            rules: [this.createRule()]
        });
        store.add(new store.recordType({
            "name": newStyle.name,
            "userStyle": newStyle
        }));
    },
    
    /** api: method[createSLD]
     *  :arg options: ``Object``
     *  :return: ``String`` The current SLD for the NamedLayer.
     *  
     *  Supported ``options``:
     *  * userStyles - ``Array(String)`` list of userStyles (by name) that are
     *    to be included in the SLD. By default, all will be included.
     */
    createSLD: function(options) {
        options = options || {};
        var sld = {
            version: "1.0.0",
            namedLayers: {}
        };
        var layerName = this.layerRecord.get("name");
        sld.namedLayers[layerName] = {
            name: layerName,
            userStyles: []
        };
        this.stylesStore.each(function(r) {
            if(!options.userStyles ||
                    options.userStyles.indexOf(r.get("name")) !== -1) {
                sld.namedLayers[layerName].userStyles.push(r.get("userStyle"));
            }
        });
        return new OpenLayers.Format.SLD().write(sld);
    },
    
    /** api: method[saveStyles]
     *  :arg options: ``Object`` Options to pass to the
     *      :class:`gxp.plugins.StyleWriter` plugin
     */
    saveStyles: function(options) {
        this.fireEvent("beforesaved", this, options);
    },
    
    /** private: method[updateStyleRemoveButton]
     *  Enable/disable the "Remove" button to make sure that we don't delete
     *  the last style.
     */
    updateStyleRemoveButton: function() {
        var userStyle = this.selectedStyle &&
            this.selectedStyle.get("userStyle");
        this.items.get(1).items.get(1).setDisabled(!userStyle ||
            this.stylesStore.getCount() <= 1 ||  userStyle.isDefault === true);
    },
    
    /** private: method[updateRuleRemoveButton]
     *  Enable/disable the "Remove" button to make sure that we don't delete
     *  the last rule.
     */
    updateRuleRemoveButton: function() {
        this.items.get(3).items.get(1).setDisabled(!this.selectedRule ||
            (this.isRaster === false &&
            this.items.get(2).items.get(0).rules.length <= 1));
    },
    
    /** private: method[createRule]
     */
    createRule: function() {
        var symbolizer = {};
        symbolizer[this.isRaster ? "Raster" : this.symbolType] = {};
        return new OpenLayers.Rule({
            name: gxp.util.uniqueName("New Rule"),
            symbolizer: symbolizer
        });
    },
    
    /** private: method[addRulesFieldSet]
     *  Creates the rules fieldSet and adds it to this container.
     */
    addRulesFieldSet: function() {
        var rulesFieldSet = new Ext.form.FieldSet({
            title: "Rules",
            autoScroll: true,
            style: "margin-bottom: 0;"
        });
        var rulesToolbar = new Ext.Toolbar({
            style: "border-width: 0 1px 1px 1px;",
            items: [
                {
                    xtype: "button",
                    iconCls: "add",
                    text: "Add",
                    handler: function() {
                        var legend = this.items.get(2).items.get(0);
                        if (this.isRaster) {
                            legend.rules.push(this.createPseudoRule());
                            this.savePseudoRules();
                        } else {
                            this.selectedStyle.get("userStyle").addRules(
                                [this.createRule()]);
                            legend.update();
                            // mark the style as modified
                            this.selectedStyle.store.afterEdit(this.selectedStyle);
                        }
                        this.updateRuleRemoveButton();
                    },
                    scope: this
                }, {
                    xtype: "button",
                    iconCls: "delete",
                    text: "Remove",
                    handler: function() {
                        var rule = this.selectedRule;
                        var legend = this.items.get(2).items.get(0);
                        if(this.isRaster) {
                            legend.unselect();
                            legend.rules.remove(rule);
                            this.savePseudoRules();
                        } else {
                            this.selectedStyle.get("userStyle").rules.remove(rule);
                            // mark the style as modified
                            this.afterRuleChange();
                        }
                    },
                    scope: this,
                    disabled: true
                }, {
                    xtype: "button",
                    iconCls: "edit",
                    text: "Edit",
                    handler: function() {
                        this.isRaster ?
                            this.editPseudoRule() :
                            this.editRule();
                    },
                    scope: this,
                    disabled: true
                }, {
                    xtype: "button",
                    iconCls: "duplicate",
                    text: "Duplicate",
                    handler: function() {
                        var legend = this.items.get(2).items.get(0);
                        if(this.isRaster) {
                            legend.rules.push(this.createPseudoRule({
                                quantity: this.selectedRule.name,
                                label: this.selectedRule.title,
                                color: this.selectedRule.symbolizer.Polygon.fillColor,
                                opacity: this.selectedRule.symbolizer.Polygon.fillOpacity
                            }));
                            this.savePseudoRules();
                        } else {
                            var newRule = this.selectedRule.clone();
                            newRule.name = gxp.util.uniqueName(
                                (newRule.title || newRule.name) + " (copy)");
                            delete newRule.title;
                            this.selectedStyle.get("userStyle").addRules(
                                [newRule]);
                            legend.update();
                        }
                        this.updateRuleRemoveButton();
                    },
                    scope: this,
                    disabled: true
                }
            ]
        });
        this.add(rulesFieldSet, rulesToolbar);
        this.doLayout();
        return rulesFieldSet;
    },
    
    /** private: method[editRule]
     */
    editRule: function() {
        var rule = this.selectedRule.clone();

        wfsUrl = Ext.urlAppend(this.layerDescription.owsURL, Ext.urlEncode({
            "SERVICE": this.layerDescription.owsType,
            "REQUEST": "DescribeFeatureType",
            "TYPENAME": this.layerDescription.typeName
        }));
        
        var ruleDlg = new Ext.Window({
            title: "Style Rule: " + (rule.title || rule.name),
            width: 340,
            autoHeight: true,
            modal: true,
            items: [{
                xtype: "gx_rulepanel",
                symbolType: this.symbolType,
                rule: rule,
                attributes: new GeoExt.data.AttributeStore({
                    url: wfsUrl
                }),
                border: false,
                defaults: {
                    autoHeight: true,
                    hideMode: "offsets"
                }
            }],
            buttons: [{
                text: "Cancel",
                handler: function() {
                    ruleDlg.close();
                }
            }, {
                text: "Apply",
                handler: function() {
                    this.saveRule(rule);
                    origRule = rule;
                },
                scope: this
            }, {
                text: "Save",
                handler: function() {
                    this.saveRule(rule);
                    ruleDlg.close();
                },
                scope: this
            }]
        });
        ruleDlg.show();
    },
    
    /** private: method[editPseudoRule]
     *  Edit a pseudo rule of a RasterSymbolizer's ColorMap.
     */
    editPseudoRule: function() {
        var rule = this.selectedRule;

        var pseudoRuleDlg = new Ext.Window({
            title: "Color Map Entry: " + rule.name,
            width: 340,
            autoHeight: true,
            modal: true,
            items: [{
                bodyStyle: "padding-top: 5px",
                border: false,
                defaults: {
                    autoHeight: true,
                    hideMode: "offsets"
                },
                items: [{
                    xtype: "form",
                    border: false,
                    labelAlign: "top",
                    defaults: {border: false},
                    style: {"padding": "0.3em 0 0 1em"},
                    items: [{
                        layout: "column",
                        defaults: {
                            border: false,
                            style: {"padding-right": "1em"}
                        },
                        items: [{
                            layout: "form",
                            width: 70,
                            items: [{
                                xtype: "numberfield",
                                anchor: "95%",
                                value: rule.name,
                                fieldLabel: "Quantity",
                                listeners: {
                                    change: function(el, value) {
                                        rule.name = String(value);
                                    }
                                }
                            }]
                        }, {
                            layout: "form",
                            width: 130,
                            items: [{
                                xtype: "textfield",
                                fieldLabel: "Label",
                                anchor: "95%",
                                value: rule.title,
                                listeners: {
                                    change: function(el, value) {
                                        rule.title = value;
                                    }
                                }
                            }]
                        }, {
                            layout: "form",
                            width: 70,
                            items: [new GeoExt.FeatureRenderer({
                                symbolType: this.symbolType,
                                isFormField: true,
                                fieldLabel: "Appearance"
                            })]
                        }]
                    }]
                }, {
                    xtype: "gx_polygonsymbolizer",
                    symbolizer: rule.symbolizer[this.symbolType],
                    bodyStyle: {"padding": "10px"},
                    border: false,
                    labelWidth: 70,
                    defaults: {
                        labelWidth: 70
                    },
                    listeners: {
                        change: function(symbolizer) {
                            var symbolizerSwatch = pseudoRuleDlg.findByType(GeoExt.FeatureRenderer)[0];
                            symbolizerSwatch.setSymbolizers(
                                [symbolizer], {draw: symbolizerSwatch.rendered}
                            );
                        },
                        scope: this
                    }
                }]
            }],
            buttons: [{
                text: "Cancel",
                handler: function() {
                    pseudoRuleDlg.close();
                }
            }, {
                text: "Apply",
                handler: function() {
                    this.savePseudoRules();
                    origRule = rule;
                },
                scope: this
            }, {
                text: "Save",
                handler: function() {
                    this.savePseudoRules();
                    pseudoRuleDlg.close();
                },
                scope: this
            }]
        });
        // remove stroke fieldset
        var strokeSymbolizer = pseudoRuleDlg.findByType("gx_strokesymbolizer")[0];
        strokeSymbolizer.ownerCt.remove(strokeSymbolizer);
        
        pseudoRuleDlg.show();
    },
    
    /** private: method[saveRule]
     *  :arg rule: the rule to save back to the userStyle
     */
    saveRule: function(rule) {
        var style = this.selectedStyle;
        var legend = this.items.get(2).items.get(0);
        var userStyle = style.get("userStyle");
        var i = userStyle.rules.indexOf(this.selectedRule);
        userStyle.rules[i] = rule;
        this.afterRuleChange(rule);
    },
    
    /** private: method[savePseudoRules]
     *  Takes the pseudo rules from the legend and adds them as
     *  RasterSymbolizer ColorMap back to the userStyle.
     */
    savePseudoRules: function() {
        var style = this.selectedStyle;
        var legend = this.items.get(2).items.get(0);
        var userStyle = style.get("userStyle");
        
        var pseudoRules = legend.rules;
        pseudoRules.sort(function(a,b) {
            var left = parseFloat(a.name);
            var right = parseFloat(b.name);
            return left === right ? 0 : (left < right ? -1 : 1);
        });
        
        var symbolizer = userStyle.rules[0].symbolizer["Raster"];
        symbolizer.colorMap = pseudoRules.length > 0 ?
            new Array(pseudoRules.length) : undefined;
        var pseudoRule;
        for (var i=0, len=pseudoRules.length; i<len; ++i) {
            pseudoRule = pseudoRules[i];
            symbolizer.colorMap[i] = {
                quantity: parseFloat(pseudoRule.name),
                label: pseudoRule.title || undefined,
                opacity: pseudoRule.symbolizer.Polygon.fillOpacity,
                color: pseudoRule.symbolizer.Polygon.fillColor || undefined
            }
        }
        this.afterRuleChange(this.selectedRule);
    },
    
    /** private: method[afterRuleChange]
     *  :arg rule: the rule to set as selectedRule, can be null
     *  
     *  Performs actions that are required to update the selectedRule and
     *  selectedStyle after a rule was changed.
     */
    afterRuleChange: function(rule) {
        var legend = this.items.get(2).items.get(0);
        this.selectedRule = rule;
        // mark the style as modified
        this.selectedStyle.store.afterEdit(this.selectedStyle);
    },
    
    /** private: method[removeRulesFieldSet[
     *  Removes rulesFieldSet when the legend image cannot be loaded
     */
    removeRulesFieldSet: function() {
        // remove the toolbar
        this.remove(this.items.get(3));
        // and the fieldset itself
        this.remove(this.items.get(2));
        this.doLayout();
    },

    /** private: method[parseSLD]
     *  :arg response: ``Object``
     *  :arg options: ``Object``
     *  
     *  Success handler for the GetStyles response. Includes a fallback
     *  to GetLegendGraphic if no valid SLD is returned.
     */
    parseSLD: function(response, options) {
        var data = response.responseXML;
        if (!data || !data.documentElement) {
            data = new OpenLayers.Format.XML().read(response.responseText);
        }
        var layerParams = this.layerRecord.get("layer").params;

        var initialStyle = this.initialConfig.styleName || layerParams.STYLES;
        if (initialStyle) {
            this.selectedStyle = this.stylesStore.getAt(
                this.stylesStore.findExact("name", initialStyle));
        }
        
        try {
            var sld = new OpenLayers.Format.SLD().read(data);
            
            // add userStyle objects to the stylesStore
            //TODO this only works if the LAYERS param contains one layer
            var userStyles = sld.namedLayers[layerParams.LAYERS].userStyles;
            
            // our stylesStore comes from the layerRecord's styles - clear it
            // and repopulate from GetStyles
            this.stylesStore.removeAll();
            var userStyle, record;
            for (var i=0, len=userStyles.length; i<len; ++i) {
                userStyle = userStyles[i];
                record = new this.stylesStore.recordType({
                    "name": userStyle.name,
                    "title": userStyle.title,
                    "abstract": userStyle.description,
                    "userStyle": userStyle
                });
                record.phantom = false;
                this.stylesStore.add(record);
                // set the default style if no STYLES param is set on the layer
                if (initialStyle === userStyle.name ||
                                                userStyle.isDefault === true) {
                    this.selectedStyle = record;
                }
            }
            
            var rulesFieldSet = this.addRulesFieldSet();
            var rules = this.selectedStyle.get("userStyle").rules;
            if (rules[0] && rules[0].symbolizer["Raster"]) {
                rulesFieldSet.setTitle("Color Map Entries");
                this.isRaster = true;
                this.addRasterLegend(rules);
            } else {
                rulesFieldSet.setTitle("Rules");
                this.isRaster = false;
                this.addVectorLegend(rules);
            }
            this.stylesStoreReady();
        }
        catch(e) {
            this.setupNonEditable();
        }
    },
    
    /** private: methos[setNonEditable]
     */
    setupNonEditable: function() {
        this.editable = false;
        // disable styles toolbar
        this.items.get(1).disable();
        this.addRulesFieldSet().add(this.createLegendImage());
        this.doLayout();
        // disable rules toolbar
        this.items.get(3).disable();
        this.stylesStoreReady();
    },
    
    /** private: method[stylesStoreReady]
     *  Adds listeners and triggers the ``load`` event of the ``styleStore``.
     */
    stylesStoreReady: function() {
        // start with a clean store
        this.stylesStore.commitChanges();
        this.stylesStore.on({
            "load": function() {
                this.addStylesCombo();
                this.updateStyleRemoveButton();
            },
            "add": function(store, records, index) {
                this.updateStyleRemoveButton();
                // update the "Choose style" combo's value
                var combo = this.items.get(0).items.get(0);
                this.markModified();
                combo.fireEvent("select", combo, store.getAt(index), index);
                combo.setValue(this.selectedStyle.get("name"));
            },
            "remove": function(store, record, index) {
                var newIndex =  Math.min(index, store.getCount() - 1);
                this.updateStyleRemoveButton();
                // update the "Choose style" combo's value
                var combo = this.items.get(0).items.get(0);
                this.markModified();
                combo.fireEvent("select", combo, store.getAt(newIndex), newIndex);
                combo.setValue(this.selectedStyle.get("name"));
            },
            "update": function(store, record) {
                var userStyle = record.get("userStyle");
                var data = {
                    "name": userStyle.name,
                    "title": userStyle.title,
                    "abstract": userStyle.description
                };
                Ext.apply(record.data, data);
                // make sure that the legend gets updated
                this.changeStyle(record);
                // update the combo's value with the new name
                this.items.get(0).items.get(0).setValue(userStyle.name);
                this.markModified();
            },
            scope: this
        });

        this.stylesStore.fireEvent("load", this.stylesStore,
            this.stylesStore.getRange())

        this._ready = true;
        this.fireEvent("ready");
    },
    
    /** private: method[markModified]
     */
    markModified: function() {
        if(this.modified === false) {
            this.modified = true;
            this.fireEvent("modified");
        }
    },
    
    /** private: method[createStylesStore]
     */
    createStylesStore: function(callback) {
        var styles = this.layerRecord.get("styles");
        this.stylesStore = new Ext.data.JsonStore({
            data: {
                styles: styles
            },
            idProperty: "name",
            root: "styles",
            // add a userStyle field (not included in styles from
            // GetCapabilities), which will be populated with the userStyle
            // object if GetStyles is supported by the WMS
            fields: ["name", "title", "abstract", "legend", "userStyle"]
        });
    },
    
    /** private: method[getStyles]
     *  :arg callback: ``Function`` function that will be called when the
     *      request result was returned.
     */
    getStyles: function(callback) {
        var layer = this.layerRecord.get("layer");
        if(this.editable === true) {
            Ext.Ajax.request({
                url: layer.url,
                params: {
                    "REQUEST": "GetStyles",
                    "LAYERS": layer.params.LAYERS
                },
                success: this.parseSLD,
                failure: this.setupNonEditable,
                callback: callback,
                scope: this
            });            
        } else {
            this.setupNonEditable();
        }
    },
    
    /** private: method[describeLayer]
     *  :arg callback: ``Function`` function that will be called when the
     *      request result was returned.
     */
    describeLayer: function(callback) {
        if(this.layerDescription) {
            callback.call(this);
            return;
        }
        var layer = this.layerRecord.get("layer");
        Ext.Ajax.request({
            url: layer.url,
            params: {
                "VERSION": layer.params["VERSION"],
                "REQUEST": "DescribeLayer",
                "LAYERS": [layer.params["LAYERS"]].join(",")
            },
            disableCaching: false,
            success: function(response) {
                var result = new OpenLayers.Format.WMSDescribeLayer().read(
                    response.responseXML && response.responseXML.documentElement ?
                        response.responseXML : response.responseText);
                this.layerDescription = result[0];
            },
            callback: callback,
            scope: this
        });
    },
    
    /** private: method[addStylesCombo]
     * 
     *  Adds a combo box with the available style names found for the layer
     *  in the capabilities document to this component's stylesFieldset.
     */
    addStylesCombo: function() {
        var store = this.stylesStore;
        var combo = new Ext.form.ComboBox(Ext.apply({
            fieldLabel: "Choose style",
            store: store,
            editable: false,
            displayField: "name",
            value: this.selectedStyle ?
                this.selectedStyle.get("name") :
                this.layerRecord.get("layer").params.STYLES || "default",
            disabled: !store.getCount(),
            mode: "local",
            typeAhead: true,
            triggerAction: "all",
            forceSelection: true,
            anchor: "100%",
            listeners: {
                "select": function(combo, record) {
                    this.changeStyle(record);
                    this.fireEvent("styleselected", this, record.get("name"));
                },
                scope: this
            }
        }, this.initialConfig.stylesComboOptions));
        // add combo to the styles fieldset
        this.items.get(0).add(combo);
        this.doLayout();
    },
    
    /** private: method[createLegendImage]
     *  :return: ``GeoExt.LegendImage`` or undefined if none available.
     * 
     *  Creates a legend image for the first style of the current layer. This
     *  is used when GetStyles is not available from the layer's WMS.
     */
    createLegendImage: function() {
        var legend = new GeoExt.WMSLegend({
            showTitle: false,
            layerRecord: this.layerRecord,
            defaults: {
                listeners: {
                    "render": function() {
                        this.getEl().on({
                            "load": this.doLayout,
                            "error": this.removeRulesFieldSet,
                            scope: this
                        });
                    },
                    scope: this
                }
            }
        });
        return legend;
    },
    
    /** private: method[changeStyle]
     *  :arg value: ``Ext.data.Record``
     * 
     *  Handler for the stylesCombo's ``select`` and the store's ``update``
     *  event. Updates the layer and the rules fieldset.
     */
    changeStyle: function(record) {
        var legend = this.items.get(2).items.get(0);
        this.selectedStyle = record;
        this.updateStyleRemoveButton();            
        var styleName = record.get("name");
        
        //TODO remove when support for GeoServer < 2.0.2 is dropped. See
        // http://jira.codehaus.org/browse/GEOS-3921
        var wmsLegend = record.get("legend");
        if (wmsLegend) {
            var urlParts = wmsLegend.href.split("?");
            var params = Ext.urlDecode(urlParts[1]);
            params.STYLE = styleName;
            urlParts[1] = Ext.urlEncode(params);
            wmsLegend.href = urlParts.join("?");
        }
        //TODO end remove
        
        if (this.editable === true) {
            var userStyle = record.get("userStyle");
            if (userStyle.isDefault === true) {
                styleName = "";
            }
            var ruleIdx = legend.rules.indexOf(this.selectedRule);
            // replace the legend
            legend.ownerCt.remove(legend);
            this.isRaster ?
                this.addRasterLegend(userStyle.rules, {
                    selectedRuleIndex: ruleIdx
                }) :
                this.addVectorLegend(userStyle.rules);
        }
        var layer = this.layerRecord.get("layer");
        var oldStyleName = layer.params.STYLES;
        if(this.initialConfig.applySelectedStyle === true &&
                    oldStyleName !== styleName && this.modified === false) {
            layer.mergeNewParams({styles: styleName});
        }
    },
    
    /** private: method[addVectorLegend]
     *  :arg rules: ``Array``
     *  :return: ``GeoExt.VectorLegend`` the legend that was created
     *
     *  Creates the vector legend for the provided rules and adds it to the
     *  rules fieldset.
     */
    addVectorLegend: function(rules) {
        var typeHierarchy = ["Point", "Line", "Polygon"];
        var highest;
        if (this.isRaster) {
            // Polygon symbolizer type for pseudo rules
            highest = 2;
        } else {
            // use the highest symbolizer type of the 1st rule
            var highest = 0;
            for (var symbolType in rules[0].symbolizer) {
                highest = Math.max(highest, typeHierarchy.indexOf(symbolType));
            }
        }
        this.symbolType = typeHierarchy[highest];
        var legend = this.items.get(2).add({
            xtype: "gx_vectorlegend",
            showTitle: false,
            rules: rules,
            symbolType: this.symbolType,
            selectOnClick: true,
            enableDD: !this.isRaster,
            listeners: {
                "ruleselected": function(cmp, rule) {
                    this.selectedRule = rule;
                    // enable the Remove, Edit and Duplicate buttons
                    var tbItems = this.items.get(3).items;
                    this.updateRuleRemoveButton();
                    tbItems.get(2).enable();
                    tbItems.get(3).enable();
                },
                "ruleunselected": function(cmp, rule) {
                    this.selectedRule = null;
                    // disable the Remove, Edit and Duplicate buttons
                    var tbItems = this.items.get(3).items;
                    tbItems.get(1).disable();
                    tbItems.get(2).disable();
                    tbItems.get(3).disable();
                },
                "afterlayout": function() {
                    // restore selection
                    //TODO QA: avoid accessing private properties/methods
                    if (this.selectedRule !== null &&
                            legend.selectedRule === null &&
                            legend.rules.indexOf(this.selectedRule) !== -1) {
                        legend.selectRuleEntry(this.selectedRule);
                    }
                },
                scope: this
            }
        });
        this.doLayout();
        return legend;
    },
    
    /** private: method[addRasterLegend]
     *  :arg rules: ``Array``
     *  :arg options: ``Object`` Additional options for this method.
     *  :return: ``GeoExt.VectorLegend`` the legend that was created
     *
     *  Creates the vector legend for the pseudo rules that are created from
     *  the RasterSymbolizer of the first rule and adds it to the rules
     *  fieldset.
     *  
     *  Supported options:
     *  * selectedRuleIndex: ``Number`` The index of a pseudo rule to select
     *    in the legend.
     */  
    addRasterLegend: function(rules, options) {
        options = options || {};
        //TODO raster styling support is currently limited to one rule, and
        // we can only handle a color map. No band selection and other stuff.
        var symbolizer = rules[0].symbolizer["Raster"];
        var colorMap = symbolizer.colorMap || [];
        var pseudoRules = [];
        var colorMapEntry;
        for (var i=0, len=colorMap.length; i<len; i++) {
            pseudoRules.push(this.createPseudoRule(colorMap[i]));
        }
        this.selectedRule = options.selectedRuleIndex != null ?
            pseudoRules[options.selectedRuleIndex] : null;
        return this.addVectorLegend(pseudoRules);
    },
    
    /** private: method[createPseudoRule]
     *  :arg colorMapEntry: ``Object``
     *  
     *  Creates a pseudo rule from a ColorMapEntry.
     */
    createPseudoRule: function(colorMapEntry) {
        colorMapEntry = Ext.applyIf(colorMapEntry || {}, {
            quantity: 0,
            color: "#000000",
            opacity: 1
        });
        return new OpenLayers.Rule({
            title: colorMapEntry.label,
            name: String(colorMapEntry.quantity),
            symbolizer: {
                "Polygon": {
                    fillColor: colorMapEntry.color,
                    fillOpacity: colorMapEntry.opacity,
                    stroke: false
                }
            }
        });
    }
    
});

/** api: xtype = gx_wmsstylesdialog */
Ext.reg('gx_wmsstylesdialog', gxp.WMSStylesDialog);