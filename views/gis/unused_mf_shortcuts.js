// These should be retrieved from the database (can be static via Web2Py, not dynamic via AJAX)
// Also need to be transformed for the current projection
//latlon.transform(map.getProjectionObject(), proj4326);
function createShortcutsStore() {
    return new Ext.data.SimpleStore({
		fields: ["value", "text", "bbox"],
		data: [['OC', 'Oceania', new OpenLayers.Bounds(56.0234375, -72.53125, 214.2265625, 32.9375)],
			['NA', 'North America', new OpenLayers.Bounds(-186.37890625, -2.21875, -28.17578125, 103.25)],
			['SA', 'South America', new OpenLayers.Bounds(-146.828125, -71.828125, 11.375, 33.640625)],
			['AF', 'Africa', new OpenLayers.Bounds(-58.9375, -51.7890625, 99.265625, 53.6796875)],
			['EU', 'Europe', new OpenLayers.Bounds(-23.078125, 26.2578125, 56.0234375, 78.9921875)],
			['AS', 'Asia', new OpenLayers.Bounds(15.59375, -21.90625, 173.796875, 83.5625)]]
	});
}
