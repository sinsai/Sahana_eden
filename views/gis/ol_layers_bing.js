{{if bing.Satellite:}}
    var bingsat = new OpenLayers.Layer.VirtualEarth( "{{=bing.Satellite}}" , {type: VEMapStyle.Aerial, 'sphericalMercator': true } );
    map.addLayer(bingsat);
{{pass}}
{{if bing.Maps:}}
    var bingmaps = new OpenLayers.Layer.VirtualEarth( "{{=bing.Maps}}" , {type: VEMapStyle.Road, 'sphericalMercator': true } );
    map.addLayer(bingmaps);
{{pass}}
{{if bing.Hybrid:}}
    var binghybrid = new OpenLayers.Layer.VirtualEarth( "{{=bing.Hybrid}}" , {type: VEMapStyle.Hybrid, 'sphericalMercator': true } );
    map.addLayer(binghybrid);
{{pass}}
{{if bing.Terrain:}}
    var bingterrain = new OpenLayers.Layer.VirtualEarth( "{{=bing.Terrain}}" , {type: VEMapStyle.Shaded, 'sphericalMercator': true } );
    map.addLayer(bingterrain);
{{pass}}
