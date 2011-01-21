/**
 * Copyright (c) 2008-2010 The Open Source Geospatial Foundation
 *
 * http://trac.geoext.org/ticket/195
 *
 * Published under the BSD license.
 * See http://svn.geoext.org/core/trunk/geoext/license.txt for the full text
 * of the license.
 */

/** api: (define)
 *  module = GeoExt.Toolbar
 *  class = GeoExt.Toolbar.ControlDisplay
 *  base_link = `Ext.Toolbar.TextItem <http://dev.sencha.com/deploy/dev/docs/?class=Ext.Toolbar.TextItem>`_
 */
Ext.namespace("GeoExt.Toolbar");

GeoExt.Toolbar.ControlDisplay = Ext.extend(Ext.Toolbar.TextItem, {

    control: null,
    map: null,

    /** private */
    onRender: function(ct, position) {
        this.text = this.text ? this.text : '&nbsp;';

        GeoExt.Toolbar.ControlDisplay.superclass.onRender.call(this, ct, position);

        this.control.div = this.el.dom;

        if (!this.control.map && this.map) {
            this.map.addControl(this.control);
        }
    }
});