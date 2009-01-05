{{if virtualearth.Satellite:}}
    var virtualearthsat = new OpenLayers.Layer.VirtualEarth( "{{=virtualearth.Satellite}}" , {type: VEMapStyle.Aerial, 'sphericalMercator': true } );
    map.addLayer(virtualearthsat);
{{pass}}
{{if virtualearth.Maps:}}
    var virtualearthmaps = new OpenLayers.Layer.VirtualEarth( "{{=virtualearth.Maps}}" , {type: VEMapStyle.Road, 'sphericalMercator': true } );
    map.addLayer(virtualearthmaps);
{{pass}}
{{if virtualearth.Hybrid:}}
    var virtualearthhybrid = new OpenLayers.Layer.VirtualEarth( "{{=virtualearth.Hybrid}}" , {type: VEMapStyle.Hybrid, 'sphericalMercator': true } );
    map.addLayer(virtualearthhybrid);
{{pass}}
