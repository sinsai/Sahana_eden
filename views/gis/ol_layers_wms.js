{{for layer in wms_layers:}}
  {{name = layer.replace(' ', '_')}}
    var wmsLayer{{=name}} = new OpenLayers.Layer.WMS( "wmsLayer{{=name}}", "wms_layers[layer].url)}}", {
      {{if wms_layers[layer].base:}}
        isBaseLayer: 'true',
      {{pass}}
        wrapDateLine: 'true',
      {{if wms_layers[layer].map:}}
        map: '$map',
      {{pass}}
      {{if wms_layers[layer].format:}}
        type: '$format',
      {{pass}}
      {{if wms_layers[layer].transparent:}}
        transparent: true,
      {{pass}}
        projection: new.OpenLayers.Projection('EPSG:{{=wms_layers[layer].projection}}')});
    map.addLayer(wmsLayer{{=name}});
{{pass}}
