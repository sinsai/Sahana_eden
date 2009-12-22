{{for layer in georss_layers:}}
    {{name = layer.replace(' ', '_')}}
    var georssLayer{{=name}} = new OpenLayers.Layer.GML( "georssLayer{{=name}}", "{{=URL(r=request, c='default', f='download', args=georss_layers[layer].url)}}", {
        format: OpenLayers.Format.GeoRSS,
        'icon': new OpenLayers.Icon("{{=georss_layers[layer].marker}}", new OpenLayers.Size(20,29))
        projection: new.OpenLayers.Projection('EPSG:{{=georss_layers[layer].projection}}')});
    map.addLayer(georssLayer{{=name}});
{{pass}}
