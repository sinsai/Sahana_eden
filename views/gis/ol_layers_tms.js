{{for layer in tms_layers:}}
  {{name = layer.replace(' ', '_')}}
    var tmsLayer{{=name}} = new OpenLayers.Layer.TMS( "tmsLayer{{=name}}", "{{=tms_layers[layer].url)}}", {
        layername: '{{=tms_layers[layer].layers}}',
      {{if tms_layers[layer].format:}}
        type: '$format',
      {{pass}}
        });
    map.addLayer(tmsLayer{{=name}});
{{pass}}
