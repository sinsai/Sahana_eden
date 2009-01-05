{{if openstreetmap.Mapnik:}}
    var mapnik = new OpenLayers.Layer.TMS( "{{=openstreetmap.Mapnik}}", "http://tile.openstreetmap.org/", {type: 'png', getURL: osm_getTileURL, displayOutsideMaxExtent: true, attribution: '<a href="http://www.openstreetmap.org/">OpenStreetMap</a>' } );
    map.addLayer(mapnik);
{{pass}}
{{if openstreetmap.Osmarender:}}
    var osmarender = new OpenLayers.Layer.TMS( "{{=openstreetmap.Osmarender}}", "http://tah.openstreetmap.org/Tiles/tile/", {type: 'png', getURL: osm_getTileURL, displayOutsideMaxExtent: true, attribution: '<a href="http://www.openstreetmap.org/">OpenStreetMap</a>' } );
    map.addLayer(osmarender);
{{pass}}
{{if openstreetmap.Aerial:}}
    var oam = new OpenLayers.Layer.TMS( "{{=openstreetmap.Aerial}}", "http://tile.openaerialmap.org/tiles/1.0.0/openaerialmap-900913/", {type: 'png', getURL: osm_getTileURL } );
    map.addLayer(oam);
{{pass}}
