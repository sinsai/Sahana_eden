function createToolbar(map) {
	return new Ext.Toolbar({map: map});
}

function initToolbarContent(toolbar) {
	function addSeparator(toolbar){
		toolbar.add(new Ext.Toolbar.Spacer());
		toolbar.add(new Ext.Toolbar.Separator());
		toolbar.add(new Ext.Toolbar.Spacer());
	}
    
    var ctrl, toolbarItems = [], action, actions = {};
    
    // Should we bother with these 4 controls or can people just use mouse wheel?
	// ZoomToMaxExtent control, a "button" control
    action = new GeoExt.Action({
        control: new OpenLayers.Control.ZoomToMaxExtent(),
        map: map,
        text: "max extent",
        tooltip: '{{=T("Zoom to maximum map extent")}}'
    });
    actions["max_extent"] = action;
    toolbarItems.push(action);
    toolbarItems.push("-");

	toolbar.addControl(
		new OpenLayers.Control.ZoomBox({
			out: true
		}), {
			iconCls: 'zoomout', 
			tooltip: '{{=T("Zoom Out: click in the map or use the left mouse button and drag to create a rectangle")}}', 
			toggleGroup: 'map'
		}
	);
	toolbar.addControl(
		new OpenLayers.Control.ZoomBox(), {
			iconCls: 'zoomin', 
			tooltip: '{{=T("Zoom In: click in the map or use the left mouse button and drag to create a rectangle")}}', 
			toggleGroup: 'map'
		}
	);
	toolbar.addControl(
		new OpenLayers.Control.DragPan(), {
			iconCls: 'pan', 
			tooltip: '{{=T("Pan Map: keep the left mouse button pressed and drag the map")}}', 
			toggleGroup: 'map'
		}
	);
	addSeparator(toolbar);
    selectControl = new OpenLayers.Control.SelectFeature(featuresLayer, {
        onSelect: onFeatureSelect_1,
        onUnselect: onFeatureUnselect_1,
        multiple: false,
        clickout: true,
        toggle: true,
        isDefault: true
    });
	toolbar.addControl(
		selectControl, {
			iconCls: 'searchclick', 
			tooltip: '{{=T("Query Feature")}}', 
			toggleGroup: 'map'
		}
	);
    //toolbar.addControl(
	//	dragControl, {
	//		iconCls: 'pan', 
	//		tooltip: '{{=T("Drag Feature")}}', 
	//		toggleGroup: 'map'
	//	}
	//);
    toolbar.addControl(
		new OpenLayers.Control.DrawFeature(featuresLayer, OpenLayers.Handler.Point), {
			iconCls: 'drawpoint', 
			tooltip: '{{=T("Add Point")}}', 
			toggleGroup: 'map'
		}
	);
	toolbar.addControl(
		new OpenLayers.Control.DrawFeature(featuresLayer, OpenLayers.Handler.Path), {
			iconCls: 'drawline', 
			tooltip: '{{=T("Add Line")}}', 
			toggleGroup: 'map'
		}
	);
	toolbar.addControl(
		new OpenLayers.Control.DrawFeature(featuresLayer, OpenLayers.Handler.Polygon), {
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
    // ToDo: Make work!
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
