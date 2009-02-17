featuresLayer = new OpenLayers.Layer.Vector("Internal Features", { 
		displayInLayerSwitcher: false
	});
var proj_current = map.getProjectionObject();
{{include 'gis/ol_layers_features2.js'}}
    
// Add Feature layer
map.addLayer(featuresLayer);

// We do this here instead of in ol_controls_features.js
// otherwise we get this.layer undefined
featuresLayer.events.register('featureadded', featuresLayer, function(){
       shn_gis_map_create_feature; 
});

// Show Busy cursor whilst loading Features
// - function defined in ol_vector_registerEvents.js
map.registerEvents(featuresLayer);

