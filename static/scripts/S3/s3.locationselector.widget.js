// Used by the S3LocationSelectorWidget (modules/widgets.py)
// This script is in Static to allow caching
// Dynamic constants (e.g. Internationalised strings) are set in server-side script

var gis_dropdown_select = function(level) {
    // When the dropdown is selected
    var new_id = $('#gis_location_L' + level).val();
    if (('' == $('#gis_location_lat').val() || '' == $('#gis_location_lon').val()) && ('' == $('#gis_location_addr_street').val()) ) {
        // Populate the real location_id field (unless a lat/lon/addr_street are present)
        if ('' != new_id) {
            $('#' + gis_location_id).val(new_id);
        }
        // Set the name box to this value
        $('#gis_location_name').val($('#gis_location_L' + level - 1 + ':selected').text());
    }
    // Show the next level of hierarchy
    $('#gis_location_L' + level).removeClass('hidden').show();
    $('#gis_location_label_L' + level).removeClass('hidden').show();
    // Pull down contents by AJAX
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
    // Hide other levels & reset their contents
    for (l=level +1; l <= 5; l=l + 1) {
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
    // When 'Add Location' pressed, unhide the next part
    // Why not working?
    $('gis_location_add-btn').click( function() {
        $('gis_location_geolocate-btn').removeClass('hidden').show();
        $('gis_location_map-btn').removeClass('hidden').show();
        $('gis_location_name_label').removeClass('hidden').show();
        $('gis_location_name').removeClass('hidden').show();
        $('gis_location_addr_street_label').removeClass('hidden').show();
        $('gis_location_addr_street').removeClass('hidden').show();
        $('gis_location_advanced_div').removeClass('hidden').show();
    });
    // When 'Advanced' checked, unhide the next part
    $('gis_location_advanced_checkbox').change( function() {
        // @ToDo Hide again if unticked
        $('gis_location_lat_label').removeClass('hidden').show();
        $('gis_location_lat_row').removeClass('hidden').show();
        $('gis_location_lon_label').removeClass('hidden').show();
        $('gis_location_lon_row').removeClass('hidden').show();
    });
});