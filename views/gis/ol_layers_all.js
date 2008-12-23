{{for layer in layers:}}
    // Disable other base layers if using a non-sphericalMercator WMS projection
    {{if projection=="900913":}}
        {{if layer.type=="openstreetmap":}}
            {{osm=db(db.gis_layer_openstreetmap.layer==layer.id).select()[0].type}}
            {{if osm=='Mapnik':}}
                var mapnik = new OpenLayers.Layer.TMS( "{{=layer.name}}", "http://tile.openstreetmap.org/", {type: 'png', getURL: osm_getTileURL, displayOutsideMaxExtent: true, attribution: '<a href="http://www.openstreetmap.org/">OpenStreetMap</a>' } );
                map.addLayer(mapnik);
            {{elif osm=='Osmarender':}}
                var osmarender = new OpenLayers.Layer.TMS( "{{=layer.name}}", "http://tah.openstreetmap.org/Tiles/tile/", {type: 'png', getURL: osm_getTileURL, displayOutsideMaxExtent: true, attribution: '<a href="http://www.openstreetmap.org/">OpenStreetMap</a>' } );
                map.addLayer(osmarender);
            {{elif osm=='Aerial':}}
                var oam = new OpenLayers.Layer.TMS( "{{=layer.name}}", "http://tile.openaerialmap.org/tiles/1.0.0/openaerialmap-900913/", {type: 'png', getURL: osm_getTileURL } );
                map.addLayer(oam);
        {{pass}}
        {{elif layer.type=="google":}}
            {{googl=db(db.gis_layer_google.layer==layer.id).select()[0].type}}
            {{if googl=='Satellite':}}
                var googlesat = new OpenLayers.Layer.Google( "{{=layer.name}}" , {type: G_SATELLITE_MAP, 'sphericalMercator': true } );
                map.addLayer(googlesat);
            {{elif googl=='Maps':}}
                var googlemaps = new OpenLayers.Layer.Google( "{{=layer.name}}" , {type: G_NORMAL_MAP, 'sphericalMercator': true } );
                map.addLayer(googlemaps);
            {{elif googl=='Hybrid':}}
                var googlehybrid = new OpenLayers.Layer.Google( "{{=layer.name}}" , {type: G_HYBRID_MAP, 'sphericalMercator': true } );
                map.addLayer(googlehybrid);
            {{elif googl=='Terrain':}}
                var googleterrain = new OpenLayers.Layer.Google( "{{=layer.name}}" , {type: G_PHYSICAL_MAP, 'sphericalMercator': true } )
                map.addLayer(googleterrain);
        {{pass}}
        {{elif layer.type=="virtualearth":}}
            {{ve=db(db.gis_layer_virtualearth.layer==layer.id).select()[0].type}}
            {{if ve=='Satellite':}}
                var vesat = new OpenLayers.Layer.VirtualEarth( "{{=layer.name}}" , {type: VEMapStyle.Aerial, 'sphericalMercator': true } );
                map.addLayer(vesat);
            {{elif ve=='Maps':}}
                var vemaps = new OpenLayers.Layer.VirtualEarth( "{{=layer.name}}" , {type: VEMapStyle.Road, 'sphericalMercator': true } );
                map.addLayer(vemaps);
            {{elif ve=='Hybrid':}}
                var vehybrid = new OpenLayers.Layer.VirtualEarth( "{{=layer.name}}" , {type: VEMapStyle.Hybrid, 'sphericalMercator': true } );
                map.addLayer(vehybrid);
        {{pass}}
        {{elif layer.type=="yahoo":}}
            {{yhoo=db(db.gis_layer_yahoo.layer==layer.id).select()[0].type}}
            {{if yhoo=='Satellite':}}
                var yahoosat = new OpenLayers.Layer.Yahoo( "{{=layer.name}}" , {type: YAHOO_MAP_SAT, 'sphericalMercator': true } );
                map.addLayer(yahoosat);
            {{elif yhoo=='Maps':}}
                var yahoomaps = new OpenLayers.Layer.Yahoo( "{{=layer.name}}" , {'sphericalMercator': true } );
                map.addLayer(yahoomaps);
            {{elif yhoo=='Hybrid':}}
                var yahoohybrid = new OpenLayers.Layer.Yahoo( "{{=layer.name}}" , {type: YAHOO_MAP_HYB, 'sphericalMercator': true } );
                map.addLayer(yahoohybrid);
        {{pass}}
        {{pass}}
    {{pass}}
{{pass}}
