// Data provided by Controller (port underway in ol_layers_features2.py)
{{for feature in features:}}
    //only works for points!
    var coords = new Array(new OpenLayers.Geometry.Point((new OpenLayers.LonLat({{=feature.lon}}, {{=feature.lat}}).transform(proj4326, proj_current)).lon, (new OpenLayers.LonLat({{=feature.lon}}, {{=feature.lat}}).transform(proj4326, proj_current)).lat));
    //var coords = {{#=feature.coords}};
    //var popupContentHTML = "{{#=feature.html}}";
    var popupContentHTML = "";
    var geom = coordToGeom(coords, '{{=feature.type}}');
    {{#if feature.marker:}}
        //var iconURL = '{{#=URL(r=request,c='default',f='download',args=[feature.marker])}}';
    {{#else:}}
        var iconURL = '{{=URL(r=request,c='default',f='download',args=[features_marker])}}';
    {{#pass}}
    add_Feature_with_popup(featuresLayer, '{{=feature.id}}', geom, popupContentHTML, iconURL);
{{pass}}
