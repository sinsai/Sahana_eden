{{for layer in georss_layers:}}
  {{name = layer.replace(' ', '_')}}
    iconURL = "{{=URL(r=request, c='default', f='download', args=georss_layers[layer].marker)}}";
    icon_img.src = iconURL;
    width = icon_img.width;
    height = icon_img.height;
    if(width > max_w){
        height = ((max_w / width) * height);
        width = max_w;
    }
    if(height > max_h){
        width = ((max_h / height) * width);
        height = max_h;
    }
    style_marker.graphicWidth = width;
    style_marker.graphicHeight = height;
    style_marker.graphicXOffset = -(width / 2);
    style_marker.graphicYOffset = -height;
    style_marker.externalGraphic = iconURL;
    var georssLayer{{=name}} = new OpenLayers.Layer.GML( "{{=layer}}", "{{=georss_layers[layer].url}}", {
        format: OpenLayers.Format.GeoRSS, style: style_marker,
        {{if georss_layers[layer].projection == 4326:}}
        projection: proj4326});
      {{else:}}
        projection: new OpenLayers.Projection('EPSG:{{=georss_layers[layer].projection}}')});
      {{pass}} 
    map.addLayer(georssLayer{{=name}});
{{pass}}
