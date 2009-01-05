{{if google.Satellite:}}
    var googlesat = new OpenLayers.Layer.Google( "{{=google.Satellite}}" , {type: G_SATELLITE_MAP, 'sphericalMercator': true } );
    map.addLayer(googlesat);
{{pass}}
{{if google.Maps:}}
    var googlemaps = new OpenLayers.Layer.Google( "{{=google.Maps}}" , {type: G_NORMAL_MAP, 'sphericalMercator': true } );
    map.addLayer(googlemaps);
{{pass}}
{{if google.Hybrid:}}
    var googlehybrid = new OpenLayers.Layer.Google( "{{=google.Hybrid}}" , {type: G_HYBRID_MAP, 'sphericalMercator': true } );
    map.addLayer(googlehybrid);
{{pass}}
{{if google.Terrain:}}
    var googleterrain = new OpenLayers.Layer.Google( "{{=google.Terrain}}" , {type: G_PHYSICAL_MAP, 'sphericalMercator': true } )
    map.addLayer(googleterrain);
{{pass}}
