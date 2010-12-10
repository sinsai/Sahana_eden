// Used by the S3LocationSelectorWidget (modules/widgets.py)
// This script is in Static to allow caching
// Dynamic constants (e.g. Internationalised strings) are set in server-side script

var gis_dropdown_select = function(level) {
    // When the dropdown is selected
    var new_id = $('#gis_location_L' + (level - 1)).val();
    // Pull down contents of new level of hierarchy by AJAX
    var this_url  = gis_url + '&value=L' + level + '&parent=' + new_id;
    var gis_load_locations = function(data, status){
        var options;
        var v = '';
        if (data.length == 0) {
            options = gis_empty_set;
        } else {
            options = gis_select_location;
            for (var i = 0; i < data.length; i++){
                v = data[i].id;
                options += '<option value="' +  data[i].id + '">' + data[i].name + '</option>';
            }
        }
        $('#gis_location_L' + level).html(options);
        if (level == gis_maxlevel && options == gis_empty_set) {
            // Don't show the last dropdown unless it has data in
            $('#gis_location_L' + level).hide();
            $('#gis_location_label_L' + level).hide();
        }
    }
    $.getJSONS3(this_url, gis_load_locations, false);
    // Show the new level
    $('#gis_location_L' + level).removeClass('hidden').show();
    $('#gis_location_label_L' + level).removeClass('hidden').show();
    // Populate the real location_id field (unless a lat/lon or addr_street are already present)
    if (('' == $('#gis_location_lat').val() || '' == $('#gis_location_lon').val()) && ('' == $('#gis_location_addr_street').val()) ) {
        if ('' != new_id) {
            $('#' + gis_location_id).val(new_id);
        }
        // Set the name box to this value
        //$('#gis_location_name').val($('#gis_location_L' + level - 1 + ':selected').text());
    }
    // Hide other levels & reset their contents
    for (l=level + 1; l <= 5; l=l + 1) {
        $('#gis_location_L' + l).hide().html(gis_loading_locations);
        $('#gis_location_label_L' + l).hide();
    }
}

$(function(){
    // When dropdowns are selected, open the next one in the hierarchy
    $('#gis_location_L0').change( function() {
        gis_dropdown_select(1);
    });
    $('#gis_location_L1').change( function() {
        gis_dropdown_select(2);
    });
    $('#gis_location_L2').change( function() {
        gis_dropdown_select(3);
    });
    $('#gis_location_L3').change( function() {
        gis_dropdown_select(4);
    });
    $('#gis_location_L4').change( function() {
        gis_dropdown_select(5);
    });
    $('#gis_location_add-btn').click( function() {
        // When 'Add Location' pressed
        // Hide the now-redundant button
        $('#gis_location_add-btn').hide();
        // unhide the next part
        $('#gis_location_geolocate-btn').removeClass('hidden').show();
        $('#gis_location_map-btn').removeClass('hidden').show();
        $('#gis_location_name_label').removeClass('hidden').show();
        $('#gis_location_name').removeClass('hidden').show();
        $('#gis_location_addr_street_label').removeClass('hidden').show();
        $('#gis_location_addr_street').removeClass('hidden').show();
        $('#gis_location_advanced_div').removeClass('hidden').show();
    });
    $('#gis_location_advanced_checkbox').change( function() {
        if ($('#gis_location_advanced_checkbox').is(':checked')) {
            // When 'Advanced' checked, unhide the next part
            $('#gis_location_lat_label').removeClass('hidden').show();
            $('#gis_location_lat_row').removeClass('hidden').show();
            $('#gis_location_lon_label').removeClass('hidden').show();
            $('#gis_location_lon_row').removeClass('hidden').show();
        } else {
            // Hide again
            $('#gis_location_lat_label').hide();
            $('#gis_location_lat_row').hide();
            $('#gis_location_lon_label').hide();
            $('#gis_location_lon_row').hide();
        }
    });
});