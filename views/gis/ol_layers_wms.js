{{for layer in wms_layers:}}
  {{name = re.sub('\W', '_', layer)}}
    var wmsLayer{{=name}} = new OpenLayers.Layer.WMS( "{{=layer}}", "{{=wms_layers[layer].url}}", {
        wrapDateLine: 'true',
      {{if wms_layers[layer].map:}}
        map: '{{=wms_layers[layer].map}}',
      {{pass}}
      layers: '{{=wms_layers[layer].layers}}',
      {{if wms_layers[layer].format:}}
        type: '{{=wms_layers[layer].format}}',
      {{pass}}
      {{if wms_layers[layer].transparent:}}
        transparent: true,
      {{pass}}
      {{if wms_layers[layer].projection == 4326:}}
        projection: proj4326 }
      {{else:}}
        projection: new OpenLayers.Projection('EPSG:{{=wms_layers[layer].projection}}') }
      {{pass}}  
      {{if wms_layers[layer].base:}}
      {{else:}}
        , { isBaseLayer: false
          {{if wms_layers[layer].visibility:}}
          {{else:}}
            , visibility: false
          {{pass}}
        }
      {{pass}}
        );
    map.addLayer(wmsLayer{{=name}});
{{pass}}
