// Add control to select features (showing info popup).
selectControl = new OpenLayers.Control.SelectFeature(featuresLayer, {
    onSelect: onFeatureSelect_1,
    onUnselect: onFeatureUnselect_1,
    multiple: false,
    clickout: true,
    toggle: true
});
map.addControl(selectControl);

// Add control to drag internal features around the map.
dragControl = new OpenLayers.Control.DragFeature(featuresLayer, {
    onComplete: shn_gis_popup_edit_position
});
map.addControl(dragControl);

// Add control to modify the shape of internal features on the map.
// WARNING this seems to cause select feature to behaviour strangely 
//(eg being able to drag a selected feature even if modify is disabled)
//modifyControl = new OpenLayers.Control.ModifyFeature(featuresLayer);
//map.addControl(modifyControl);
//modifyControl.mode = OpenLayers.Control.ModifyFeature.RESHAPE;
//modifyControl.mode &= ~OpenLayers.Control.ModifyFeature.DRAG;

// Add control to add new points to the map.
pointControl = new OpenLayers.Control.DrawFeature(featuresLayer, OpenLayers.Handler.Point);
pointControl.featureAdded = shn_gis_map_create_feature;
map.addControl(pointControl);

// Add control to add new lines to the map.
lineControl = new OpenLayers.Control.DrawFeature(featuresLayer, OpenLayers.Handler.Path);
lineControl.featureAdded = shn_gis_map_create_feature;
map.addControl(lineControl);

// Add control to add new polygons to the map.
polygonControl = new OpenLayers.Control.DrawFeature(featuresLayer, OpenLayers.Handler.Polygon);
polygonControl.featureAdded = shn_gis_map_create_feature;
map.addControl(polygonControl);

// Start with select activated.
shn_gis_map_control_select();