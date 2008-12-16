OpenLayers.Map.prototype.registerEvents = function(layer) {
	layer.events.register("loadstart", layer, function() {
		document.body.style.cursor = 'wait';
	});
	layer.events.register("loadend", layer, function() {
		document.body.style.cursor = 'auto';
	});
	this.addLayer(layer);
}

function createToolbar(map) {
	return new mapfish.widgets.toolbar.Toolbar({map: map});
}

function initToolbarContent(toolbar) {
	function addSeparator(toolbar){
		toolbar.add(new Ext.Toolbar.Spacer());
		toolbar.add(new Ext.Toolbar.Separator());
		toolbar.add(new Ext.Toolbar.Spacer());
	} 

	toolbar.addControl(
		new OpenLayers.Control.ZoomToMaxExtent({map: map}), {
			iconCls: "zoomfull", 
			tooltip: '{{=T("Zoom Out Full")}}', 
			toggleGroup: "map"
		}
	);
	addSeparator(toolbar);
	toolbar.addControl(
		new OpenLayers.Control.ZoomBox(), {
			iconCls: 'zoomin', 
			tooltip: '{{=T("Zoom In")}}', 
			toggleGroup: 'map'
		}
	);
	toolbar.addControl(
		new OpenLayers.Control.ZoomBox({
			out: true
		}), {
			iconCls: 'zoomout', 
			tooltip: '{{=T("Zoom Out")}}', 
			toggleGroup: 'map'
		}
	);
	toolbar.addControl(
		new OpenLayers.Control.DragPan({
			isDefault: true
		}), {
			iconCls: 'pan', 
			tooltip: '{{=T("Drag")}}', 
			toggleGroup: 'map'
		}
	);
	addSeparator(toolbar);
	toolbar.addControl(
		new OpenLayers.Control.DrawFeature(vectorLayer, OpenLayers.Handler.Point), {
			iconCls: 'drawpoint', 
			tooltip: '{{=T("Add Point")}}', 
			toggleGroup: 'map'
		}
	);
	toolbar.addControl(
		new OpenLayers.Control.DrawFeature(vectorLayer, OpenLayers.Handler.Path), {
			iconCls: 'drawline', 
			tooltip: '{{=T("Add Line")}}', 
			toggleGroup: 'map'
		}
	);
	toolbar.addControl(
		new OpenLayers.Control.DrawFeature(vectorLayer, OpenLayers.Handler.Polygon), {
			iconCls: 'drawpolygon', 
			tooltip: '{{=T("Add Area")}}', 
			toggleGroup: 'map'
		}
	);
	addSeparator(toolbar);
	var nav = new OpenLayers.Control.NavigationHistory();
	map.addControl(nav);
	nav.activate();
	toolbar.add(
		new Ext.Toolbar.Button({
			iconCls: 'back',
			tooltip: '{{=T("Previous View")}}', 
			handler: nav.previous.trigger
		})
	);
	toolbar.add(
		new Ext.Toolbar.Button({
			iconCls: 'next',
			tooltip: '{{=T("Next View")}}', 
			handler: nav.next.trigger
		})
	);
	addSeparator(toolbar);
	var saveButton = new Ext.Toolbar.Button({
			iconCls: 'save',
			tooltip: '{{=T("Save Viewport")}}', 
			handler: function saveViewport(map) {
				// Read current settings from map
				var lonlat = map.getCenter();
				var zoom_current = map.getZoom();
				// Convert back to LonLat for saving
				//var proj4326 = new OpenLayers.Projection("EPSG:4326");
				lonlat.transform(map.getProjectionObject(), proj4326);
				//alert("{{=T("Latitude")}}: " + lat);
                // Use AJAX to send back
			}
		})
	toolbar.add(
		saveButton
	);
	addSeparator(toolbar);
	toolbar.activate();
}
