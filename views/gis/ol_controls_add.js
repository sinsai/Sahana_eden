// Add control to add new Points to the map.
pointControl = new OpenLayers.Control.DrawFeature(featuresLayer, OpenLayers.Handler.Point);
pointControl.featureAdded = shn_gis_map_add_geometry;
map.addControl(pointControl);
// Add control to add new Lines to the map.
lineControl = new OpenLayers.Control.DrawFeature(featuresLayer, OpenLayers.Handler.Path);
lineControl.featureAdded = shn_gis_map_add_geometry;
map.addControl(lineControl);
// Add control to add new Polygons to the map.
polygonControl = new OpenLayers.Control.DrawFeature(featuresLayer, OpenLayers.Handler.Polygon);
polygonControl.featureAdded = shn_gis_map_add_geometry;
map.addControl(polygonControl);

// Start with navigate activated.
shn_gis_map_control_navigate();