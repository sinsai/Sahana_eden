{{if projection==900913:}}
    {{if openstreetmap:}}
        {{include 'gis/ol_layers_openstreetmap.js'}}
    {{pass}}
    {{if google:}}
        {{include 'gis/ol_layers_google.js'}}
    {{pass}}
    {{if yahoo:}}
        {{include 'gis/ol_layers_yahoo.js'}}
    {{pass}}
    {{if virtualearth:}}
        {{include 'gis/ol_layers_virtualearth.js'}}
    {{pass}}
{{else:}}
    // Disable other base layers if using a non-sphericalMercator WMS projection
{{pass}}