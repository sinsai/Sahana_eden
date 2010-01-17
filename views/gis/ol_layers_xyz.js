{{for layer in xyz_layers:}}
  {{name = layer.replace(' ', '_')}}
    var xyzLayer{{=name}} = new OpenLayers.Layer.XYZ( "{{=layer}}", "{{=xyz_layers[layer].url}}", {
      {{if xyz_layers[layer].sphericalMercator:}}
        sphericalMercator: 'true',
      {{pass}}
      {{if xyz_layers[layer].transitionEffect:}}
        transitionEffect: '{{=xyz_layers[layer].transitionEffect}}',
      {{pass}}
      {{if xyz_layers[layer].numZoomLevels:}}
        numZoomLevels: '{{=xyz_layers[layer].numZoomLevels}}'
      {{pass}}
      {{if xyz_layers[layer].base:}}
        isBaseLayer: 'true'
      {{else:}}
        {{if xyz_layers[layer].transparent:}}
          transparent: 'true',
        {{pass}}
        {{if xyz_layers[layer].visible:}}
          visibility: 'true',
        {{pass}}
        {{if xyz_layers[layer].opacity:}}
          opacity: '{{=xyz_layers[layer].opacity}}',
        {{pass}}
        isBaseLayer: 'false'
      {{pass}}
    });
    map.addLayer(xyzLayer{{=name}});
{{pass}}
