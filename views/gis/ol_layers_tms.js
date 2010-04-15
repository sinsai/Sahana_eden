{{for layer in tms_layers:}}
  {{name = re.sub('\W', '_', layer)}}
    var tmsLayer{{=name}} = new OpenLayers.Layer.TMS( "{{=layer}}", "{{=tms_layers[layer].url}}", {
        layername: '{{=tms_layers[layer].layers}}',
      {{if tms_layers[layer].format:}}
        type: '$format',
      {{pass}}
        });
    map.addLayer(tmsLayer{{=name}});
{{pass}}
