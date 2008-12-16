// No need to duplicate this functionality - done nicer by MapFish
//map.addControl(new OpenLayers.Control.LayerSwitcher());

// Doesn't work in our app :/
//map.addControl(new OpenLayers.Control.Permalink());

// Small one already present & takes up less space
//map.addControl(new OpenLayers.Control.PanZoomBar());

map.addControl(new OpenLayers.Control.ScaleLine());
map.addControl(new OpenLayers.Control.MousePosition());
map.addControl(new OpenLayers.Control.OverviewMap({mapOptions: options}));
