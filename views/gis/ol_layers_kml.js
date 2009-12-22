{{for layer in kml_layers:}}
    {{name = layer.replace(' ', '_')}}
    var kmlLayer{{=name}} = new OpenLayers.Layer.GML( "{{=layer}}", "{{=kml_layers[layer].url}}", {
        format: OpenLayers.Format.KML, formatOptions: { extractStyles: true, extractAttributes: true }, projection: proj4326});
    map.addLayer(georssLayer{{=name}});
{{pass}}
