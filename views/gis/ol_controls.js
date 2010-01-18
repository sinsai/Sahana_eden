// No need to duplicate this functionality - done nicer by GeoExt
//map.addControl(new OpenLayers.Control.LayerSwitcher());

// Small one already present & takes up less space
//map.addControl(new OpenLayers.Control.PanZoomBar());

map.addControl(new OpenLayers.Control.ScaleLine());
map.addControl(new OpenLayers.Control.MousePosition());
map.addControl(new OpenLayers.Control.Permalink());
map.addControl(new OpenLayers.Control.OverviewMap({mapOptions: options}));popupControl = new OpenLayers.Control.SelectFeature(allLayers);
map.addControl(popupControl);
popupControl.activate();

