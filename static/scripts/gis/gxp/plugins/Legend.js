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
 *  class = Legend
 */

/** api: (extends)
 *  plugins/Tool.js
 */
Ext.namespace("gxp.plugins");

/** api: constructor
 *  .. class:: Legend(config)
 *
 *    Provides an action to display a legend in a new window.
 */
gxp.plugins.Legend = Ext.extend(gxp.plugins.Tool, {
    
    /** api: ptype = gxp_legend */
    ptype: "gxp_legend",
    
    /** api: config[menuText]
     *  ``String``
     *  Text for legend menu item (i18n).
     */
    menuText: "Legend",

    /** api: config[tooltip]
     *  ``String``
     *  Text for legend action tooltip (i18n).
     */
    tooltip: "Show Legend",

    /** api: config[actionTarget]
     *  ``Object`` or ``String`` or ``Array`` Where to place the tool's actions
     *  (e.g. buttons or menus)? Use null as the default since our tool has both 
     *  output and action(s).
     */
    actionTarget: null,

    /** private: method[constructor]
     */
    constructor: function(config) {
        gxp.plugins.Legend.superclass.constructor.apply(this, arguments);
    },

    /** api: method[addActions]
     */
    addActions: function() {
        var actions = [{
            menuText: this.menuText,
            iconCls: "gxp-icon-legend",
            tooltip: this.tooltip,
            handler: function() {
                this.addOutput();
            },
            scope: this
        }];
        return gxp.plugins.Legend.superclass.addActions.apply(this, [actions]);
    },

    /** private: method[addOutput]
     *  :arg config: ``Object``
     */
    addOutput: function(config) {
        config = Ext.apply({
            autoScroll: true,
            width: 300,
            height: 400,
            defaults: {cls: 'gxp-legend-item'},
            title: this.menuText,
            items: [{
                xtype: 'gx_legendpanel',
                ascending: false,
                border: false,
                layerStore: this.target.mapPanel.layers
            }]
        }, config || {});

        var legend = gxp.plugins.Legend.superclass.addOutput.call(this, config);
        return legend;
    }

});

Ext.preg(gxp.plugins.Legend.prototype.ptype, gxp.plugins.Legend);
