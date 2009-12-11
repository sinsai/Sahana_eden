// Show Busy cursor whilst loading Draft Features
OpenLayers.Map.prototype.registerEvents = function(layer) {
	layer.events.register("loadstart", layer, function() {
		document.body.style.cursor = 'wait';
	});
	layer.events.register("loadend", layer, function() {
		document.body.style.cursor = 'auto';
	});
	this.addLayer(layer);
}
