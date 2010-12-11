// Used by the S3LocationSelectorWidget (modules/widgets.py)
// This script is in Static to allow caching
// Dynamic constants (e.g. Internationalised strings) are set in server-side script

var gis_dropdown_select = function(level) {
    // Read the new value of the dropdown
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

var gis_save_location = function(name, lat, lon, addr_street) {
        // Locate the Parent - try the lowest level 1st
        _parent = $('#gis_location_L5').val();
        if (undefined == _parent || '' == _parent){
            _parent = $('#gis_location_L4').val();
            if (undefined == _parent || '' == _parent){
                _parent = $('#gis_location_L3').val();
                if (undefined == _parent || '' == _parent){
                    _parent = $('#gis_location_L2').val();
                    if (undefined == _parent || '' == _parent){
                        _parent = $('#gis_location_L1').val();
                        if (undefined == _parent || '' == _parent){
                            _parent = $('#gis_location_L0').val();
                        }
                    }
                }
            }
        }
        // Build the URL
        if ('' == S3.gis.uuid) {
            // Create a new record
            url = '{{=URL(r=request, c="gis", f="location", args=["create.url"])}}' + '?name=' + name;
        } else {
            // Update an existing record
            url = '{{=URL(r=request, c="gis", f="location", args=["update.url"])}}' + '?uuid=' + S3.gis.uuid + '&name=' + name;
        }
        if ('' == lat || '' == lon) {
            // pass
        } else {
            url = url + '&lat=' + lat + '&lon=' + lon;
        }
        if ('' == addr_street) {
            // pass
        } else {
            url = url + '&addr_street=' + addr_street;
        }
        if (undefined == _parent || '' == _parent){
            // pass
        } else {
            url = url + '&parent=' + _parent;
        }
        // Submit the Location record
        $.ajax({
                // Block the form's return until we've updated the record
                async: false,
                url: url,
                dataType: 'json',
                success: function(data) {
                    // Report Success/Failure
                    //showStatus(data.message);

                    if (('' == S3.gis.uuid) && (data.status == 'success')) {
                        // Parse the new location
                        var new_id = data.message.split('=')[1];
                        // Update the value of the real field
                        $('#' + location_id).val(new_id);
                        // Store the UUID for future updates
                        //var url_read = '{{=URL(r=request, c="gis", f="location")}}' + '/' + new_id + '.json';
                        //$.getJSON(url_read, function(data) {
                        //    var domain = data['@domain'];
                            // Set global variable for later pickup
                        //    var uuid = data['$_gis_location'][0]['@uuid'];
                        //    if (uuid.split('/')[0] == domain) {
                        //        S3.gis.uuid = uuid.split('/')[1];
                        //    } else {
                        //        S3.gis.uuid = uuid;
                        //    }
                        //});
                    }

                }
            });
        
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
        $('#gis_location_geocoder-btn').removeClass('hidden').show();
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
    $('form').submit( function() {
        // The form is being submitted

        // Check if a new location should be created
        var name = $('#gis_location_name').val();
        var lat = $('#gis_location_lat').val();
        var lon = $('#gis_location_lon').val();
        var addr_street = $('#gis_location_addr_street').val();

        // Only save a new Location if we have data
        if ('' == name)) {
            if (('' == lat || '' == lon) && ('' == addr_street)) {
                // We don't have a name, but we do have details, so prompt the user
                // @ToDo!
            } else {
                // There are no specific location details specified
                // (Hierarchy may have been done but that's not our issue here)
                // Allow the Form's save to continue
                return true;
            }
        }
        // Save the new location
        gis_save_location(name, lat, lon, addr_street);

        // Allow the Form's save to continue
        return true;
    });
});