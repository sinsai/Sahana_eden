<script type="text/javascript">//<![CDATA[
// Unused. We do server-side since easier for the WKTCentroid & anyway we don't want to rely on JS clients
$(function() {
    $('input#submit_button').click(function(event){
        type=$("select#gis_feature_type").val();
        if (type=="point") {
            // Populate WKT field from Lat/Lon
            lat=$("input#gis_feature_lat").val();
            lon=$("input#gis_feature_lon").val();
            wkt='POINT('+lon+' '+lat+')'
            $('input#gis_feature_wkt').val(wkt);
        } else if (type=="line" | type=="polygon") {
            // Need to port Geos' getCentroid routines from C to JavaScript
            // same as: http://www.jennessent.com/arcgis/shapes_poster.htm
            // => easier to do server-side using Shapely!
        }
        // Pass to RESTlike CRUD controller
        event.default();
        return false;
    });
});
//]]></script>