{{if yahoo.Satellite:}}
    var yahoosat = new OpenLayers.Layer.Yahoo( "{{=yahoo.Satellite}}" , {type: YAHOO_MAP_SAT, 'sphericalMercator': true } );
    map.addLayer(yahoosat);
{{pass}}
{{if yahoo.Maps:}}
    var yahoomaps = new OpenLayers.Layer.Yahoo( "{{=yahoo.Maps}}" , {'sphericalMercator': true } );
    map.addLayer(yahoomaps);
{{pass}}
{{if yahoo.Hybrid:}}
    var yahoohybrid = new OpenLayers.Layer.Yahoo( "{{=yahoo.Hybrid}}" , {type: YAHOO_MAP_HYB, 'sphericalMercator': true } );
    map.addLayer(yahoohybrid);
{{pass}}
