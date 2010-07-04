    feature_type=$("select#gis_location_gis_feature_type").val();
    if (feature_type==1) {
        // Point
        // Hide the WKT input
        $("#gis_location_wkt__row").hide();
    } else if (feature_type==2) {
        // Line
        // Hide the Lat/Lon inputs
        $("#gis_location_lat__row").hide();
        $("#gis_location_lon__row").hide();
        if ($('input#gis_location_wkt').val()===''){
            // Pre-populate the WKT field
            $(this).val('LINESTRING( , , )')
        }
    } else if (feature_type==3) {
        // Polygon
        // Hide the Lat/Lon inputs
        $("#gis_location_lat__row").hide();
        $("#gis_location_lon__row").hide();
        if ($('input#gis_location_wkt').val()===''){
            // Pre-populate the WKT field
            $(this).val('POLYGON(( , , ))')
        }
    }
    // When the Type changes:
	$("select#gis_location_gis_feature_type").change(function() {
		// What is the new type?
        feature_type=$(this).val();
        if (feature_type==1) {
            // Point
            // Hide the WKT input
            $("#gis_location_wkt__row").hide();
            // Show the Lat/Lon inputs
            $("#gis_location_lat__row").show();
            $("#gis_location_lon__row").show();
        } else if (feature_type==2) {
            // Line
            // Hide the Lat/Lon inputs
            $("#gis_location_lat__row").hide();
            $("#gis_location_lon__row").hide();
            // Show the WKT input
            $("#gis_location_wkt__row").show();
            if ($('input#gis_location_wkt').val()===''){
                // Pre-populate the WKT field
                $('input#gis_location_wkt').val('LINESTRING( , , )')
            }
        } else if (feature_type==3) {
            // Polygon
            // Hide the Lat/Lon inputs
            $("#gis_location_lat__row").hide();
            $("#gis_location_lon__row").hide();
            // Show the WKT input
            $("#gis_location_wkt__row").show();
            if ($('input#gis_location_wkt').val()===''){
                // Pre-populate the WKT field
                $('input#gis_location_wkt').val('POLYGON(( , , ))')
            }
        }
    })
