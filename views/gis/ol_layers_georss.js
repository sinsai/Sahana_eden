var georssLayers = new Array();
{{for layer in georss_layers:}}
  {{name = re.sub('\W', '_', layer)}}
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
        strategies: [ strategy ],
        format: OpenLayers.Format.GeoRSS, style: style_marker,
        formatOptions: {
            // adds the thumbnail attribute to the feature
            createFeatureFromItem: function(item) {
                var feature = OpenLayers.Format.GeoRSS.prototype.createFeatureFromItem.apply(this, arguments);
                //feature.attributes.thumbnail =
                //        this.getElementsByTagNameNS(
                //        item, "*", "thumbnail")[0].getAttribute("url");
                return feature;
            }
        },
      {{if georss_layers[layer].projection == 4326:}}
        projection: proj4326});
      {{else:}}
        projection: new OpenLayers.Projection('EPSG:{{=georss_layers[layer].projection}}')});
      {{pass}} 
    {{if georss_layers[layer].visibility:}}
      georssLayer{{=name}}.setVisibility(true);
    {{else:}}
      georssLayer{{=name}}.setVisibility(false);
    {{pass}}
    map.addLayer(georssLayer{{=name}});
    georssLayers.push(georssLayer{{=name}});
    georssLayer{{=name}}.events.on({ "featureselected": onGeorssFeatureSelect, "featureunselected": onFeatureUnselect });
{{pass}}
{{if georss_layers:}}
allLayers = allLayers.concat(georssLayers);

function onGeorssFeatureSelect(event) {
    var feature = event.feature;
    var selectedFeature = feature;
    if (undefined == feature.attributes.description) {
        var popup = new OpenLayers.Popup.FramedCloud("chicken", 
        feature.geometry.getBounds().getCenterLonLat(),
        new OpenLayers.Size(200,200),
        "<h2>" + feature.attributes.title + "</h2>",
        null, true, onPopupClose);
    } else {
        var popup = new OpenLayers.Popup.FramedCloud("chicken",
        feature.geometry.getBounds().getCenterLonLat(),
        new OpenLayers.Size(200,200),
        "<h2>" + feature.attributes.title + "</h2>" + feature.attributes.description,
        null, true, onPopupClose);
    };
    feature.popup = popup;
    popup.feature = feature;
    map.addPopup(popup);
}

{{pass}}
