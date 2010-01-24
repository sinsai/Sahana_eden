toolbar = mapPanel.getTopToolbar();

var toggleGroup = "controls";

// OpenLayers controls
var length = new OpenLayers.Control.Measure(OpenLayers.Handler.Path, {
    eventListeners: {
        measure: function(evt) {
            alert("{{=T('The length was ')}}" + evt.measure + evt.units);
        }
    }
});

var area = new OpenLayers.Control.Measure(OpenLayers.Handler.Polygon, {
    eventListeners: {
        measure: function(evt) {
            alert("{{=T('The area was ')}}" + evt.measure + evt.units);
        }
    }
});

// Controls for Draft Features
// - interferes with Feature Layers!
//var selectControl = new OpenLayers.Control.SelectFeature(featuresLayer, {
//    onSelect: onFeatureSelect,
//    onUnselect: onFeatureUnselect,
//    multiple: false,
//    clickout: true,
//    isDefault: true
//});

var removeControl = new OpenLayers.Control.RemoveFeature(featuresLayer, 
    {onDone: function(feature) {console.log(feature)}
});

var nav = new OpenLayers.Control.NavigationHistory();

// GeoExt Buttons
var zoomfull = new GeoExt.Action({
    control: new OpenLayers.Control.ZoomToMaxExtent(),
    map: map,
    iconCls: 'zoomfull',
    tooltip: '{{=T("Zoom to maximum map extent")}}'
});
    
var zoomout = new GeoExt.Action({
    control: new OpenLayers.Control.ZoomBox({ out: true }),
    map: map,
    iconCls: 'zoomout',
    tooltip: '{{=T("Zoom Out: click in the map or use the left mouse button and drag to create a rectangle")}}',
    toggleGroup: toggleGroup
});
    
var zoomin = new GeoExt.Action({
    control: new OpenLayers.Control.ZoomBox(),
    map: map,
    iconCls: 'zoomin',
    tooltip: '{{=T("Zoom In: click in the map or use the left mouse button and drag to create a rectangle")}}',
    toggleGroup: toggleGroup
});

var pan = new GeoExt.Action({
    control: new OpenLayers.Control.Navigation(),
    map: map,
    iconCls: 'pan-off',
    tooltip: '{{=T("Pan Map: keep the left mouse button pressed and drag the map")}}',
    toggleGroup: toggleGroup,
    //allowDepress: false,
    pressed: true
});

var lengthButton = new GeoExt.Action({
    control: length,
    map: map,
    iconCls: 'measure-off',
    tooltip: '{{=T("Measure Length: Click the points along the path & end with a double-click")}}',
    toggleGroup: toggleGroup
});

var areaButton = new GeoExt.Action({
    control: area,
    map: map,
    iconCls: 'measure-area',
    tooltip: '{{=T("Measure Area: Click the points around the polygon & end with a double-click")}}',
    toggleGroup: toggleGroup
});

{{if mgrs:}}
// MGRS Control
var mgrsButton = new GeoExt.Action({
    text: "Select {{=mgrs.name}}",
    control: selectPdfControl,
    map: map,
    toggleGroup: toggleGroup,
    allowDepress: false,
    tooltip: "Select {{=mgrs.name}}",
    // check item options group: "draw"
});
{{pass}}

var selectButton = new GeoExt.Action({
    //control: selectControl,
    map: map,
    iconCls: 'searchclick',
    tooltip: '{{=T("Query Feature")}}',
    toggleGroup: toggleGroup
});

var pointButton = new GeoExt.Action({
    control: new OpenLayers.Control.DrawFeature(featuresLayer, OpenLayers.Handler.Point),
    map: map,
    iconCls: 'drawpoint-off',
    tooltip: '{{=T("Add Point")}}',
    toggleGroup: toggleGroup
});

var lineButton = new GeoExt.Action({
    control: new OpenLayers.Control.DrawFeature(featuresLayer, OpenLayers.Handler.Path),
    map: map,
    iconCls: 'drawline-off',
    tooltip: '{{=T("Add Line")}}',
    toggleGroup: toggleGroup
});

var polygonButton = new GeoExt.Action({
    control: new OpenLayers.Control.DrawFeature(featuresLayer, OpenLayers.Handler.Polygon),
    map: map,
    iconCls: 'drawpolygon-off',
    tooltip: '{{=T("Add Polygon")}}',
    toggleGroup: toggleGroup
});

var dragButton = new GeoExt.Action({
    control: new OpenLayers.Control.DragFeature(featuresLayer),
    map: map,
    iconCls: 'movefeature',
    tooltip: '{{=T("Move Feature: Drag feature to desired location")}}',
    toggleGroup: toggleGroup
});

var resizeButton = new GeoExt.Action({
    control: new OpenLayers.Control.ModifyFeature(featuresLayer, { mode: OpenLayers.Control.ModifyFeature.RESIZE }),
    map: map,
    iconCls: 'resizefeature',
    tooltip: '{{=T("Resize Feature: Select the feature you wish to resize & then Drag the associated dot to your desired size")}}',
    toggleGroup: toggleGroup
});

var rotateButton = new GeoExt.Action({
    control: new OpenLayers.Control.ModifyFeature(featuresLayer, { mode: OpenLayers.Control.ModifyFeature.ROTATE }),
    map: map,
    iconCls: 'rotatefeature',
    tooltip: '{{=T("Rotate Feature: Select the feature you wish to rotate & then Drag the associated dot to rotate to your desired location")}}',
    toggleGroup: toggleGroup
});

var modifyButton = new GeoExt.Action({
    control: new OpenLayers.Control.ModifyFeature(featuresLayer),
    map: map,
    iconCls: 'modifyfeature',
    tooltip: '{{=T("Modify Feature: Select the feature you wish to deform & then Drag one of the dots to deform the feature in your chosen manner")}}',
    toggleGroup: toggleGroup
});

var removeButton = new GeoExt.Action({
    control: removeControl,
    map: map,
    iconCls: 'removefeature',
    tooltip: '{{=T("Remove Feature: Select the feature you wish to remove & press the delete key")}}',
    toggleGroup: toggleGroup
});

var navPreviousButton = new Ext.Toolbar.Button({
    iconCls: 'back',
    tooltip: '{{=T("Previous View")}}', 
    handler: nav.previous.trigger
});

var navNextButton = new Ext.Toolbar.Button({
    iconCls: 'next',
    tooltip: '{{=T("Next View")}}', 
    handler: nav.next.trigger
});

var saveButton = new Ext.Toolbar.Button({
    // ToDo: Make work!
    iconCls: 'save',
    tooltip: '{{=T("Save: Default Lat, Lon & Zoom for the Viewport")}}', 
    handler: function saveViewport(map) {
        // Read current settings from map
        var lonlat = map.getCenter();
        var zoom_current = map.getZoom();
        // Convert back to LonLat for saving
        //var proj4326 = new OpenLayers.Projection("EPSG:4326");
        lonlat.transform(map.getProjectionObject(), proj4326);
        //alert("{{=T("Latitude")}}: " + lat);
        // Use AJAX to send back
        var url = "{{=URL(r=request, c='gis', f='config', args=['update', 1], vars={'format':'json'})}}";
    }
});

// Add to Map & Toolbar
toolbar.add(zoomfull);
toolbar.add(zoomout);
toolbar.add(zoomin);
toolbar.add(pan);
toolbar.addSeparator();
// Measure Tools
toolbar.add(lengthButton);
toolbar.add(areaButton);
toolbar.addSeparator();
{{if mgrs:}}
toolbar.add(mgrsButton);
toolbar.addSeparator();
{{pass}}
// Draw Controls
//toolbar.add(selectButton);
//toolbar.add(pointButton);
//toolbar.add(lineButton);
//toolbar.add(polygonButton);
//toolbar.add(dragButton);
//toolbar.add(resizeButton);
//toolbar.add(rotateButton);
//toolbar.add(modifyButton);
//toolbar.add(removeButton);
//toolbar.addSeparator();
// Navigation
map.addControl(nav);
nav.activate();
toolbar.addButton(navPreviousButton);
toolbar.addButton(navNextButton);
toolbar.addSeparator();
// Save Viewport
toolbar.addButton(saveButton);
