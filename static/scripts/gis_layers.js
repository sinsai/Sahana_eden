//<![CDATA[
// Used in GIS:
// map_service_catalogue.html, update_layer.html
$(function() {
    // What is the initial type?
    var type = $("select[@name=type]").val();
    // OpenStreetMap
    if (type==1) {
        var fields_hide=["key"];
    // Google
    } else if (type==2) {
        var fields_hide=[];
    // Virtual Earth
    } else if (type==3) {
        var fields_hide=["key"];
    // Yahoo
    } else if (type==4) {
        var fields_hide=[];
    }
    // Hide fields irrelevant for the type
    for (var i = 0; i < fields_hide.length; i++) {
        var selector = "#"+fields_hide[i]
        $(selector).hide();
    }
    
    // When the type changes:
	$("select[@name=type]").change(function() {
		// What is the new type?
        type=$(this).val();
        // OpenStreetMap
        if (type==1) {
            var fields_hide=["key"];
            var fields_show=["subtype"];
            var options_subtype=["Mapnik", "Osmarender", "Aerial"];
        // Google
        } else if (type==2) {
            var fields_hide=[];
            var fields_show=["subtype","key"];
            var options_subtype=["Satellite", "Maps", "Hybrid", "Terrain"];
        // Virtual Earth
        } else if (type==3) {
            var fields_hide=["key"];
            var fields_show=["subtype"];
            var options_subtype=["Satellite", "Maps", "Hybrid"];
        // Yahoo
        } else if (type==4) {
            var fields_hide=[];
            var fields_show=["subtype","key"];
            var options_subtype=["Satellite", "Maps", "Hybrid"];
        }
        // Hide fields no longer relevant for the new type
        for (var i = 0; i < fields_hide.length; i++) {
            var selector = "#"+fields_hide[i]
            $(selector).hide();
        }
		// Show all fields relevant to the new type
        for (var i = 0; i < fields_show.length; i++) {
            var selector = "#"+fields_show[i]
            $(selector).show();
        }
        // Refresh the subtypes lookuplist
        // ToDo: Pull from Database using AJAX/JSON:
        // http://remysharp.com/2007/01/20/auto-populating-select-boxes-using-jquery-ajax/
		var options = '';
        //for (var i = 0; i < options_subtype.length; i++) {
        for(key in options_subtype) {
            options += '<option value="' + options_subtype[key] + '">' + options_subtype[key] + '</option>';
        }
        $("select[@name=subtype]").html(options);
        // ToDo: Provide option to update the Key field from DB using AJAX/JSON
	})
});
//]]>