// Used by the S3LocationSelectorWidget (modules/widgets.py)
// This script is in Static to allow caching
// Dynamic constants (e.g. Internationalised strings) are set in server-generated script

function s3_gis_dropdown_select(level) {
    // Read the new value of the dropdown
    var new_id = $('#gis_location_L' + (level - 1)).val();
    if (new_id) {
        // Pull down contents of new level of hierarchy by AJAX
        var this_url  = s3_gis_url + '/search.json?filter=%3D&field=level&value=L' + level + '&parent=' + new_id;
        var s3_gis_load_locations = function(data, status){
            var options;
            var v = '';
            if (data.length == 0) {
                options = s3_gis_empty_set;
            } else {
                options = s3_gis_select_location;
                for (var i = 0; i < data.length; i++){
                    v = data[i].id;
                    options += '<option value="' +  data[i].id + '">' + data[i].name + '</option>';
                }
            }
            $('#gis_location_L' + level).html(options);
            if (level == s3_gis_maxlevel && options == s3_gis_empty_set) {
                // Don't show the last dropdown unless it has data in
                $('#gis_location_L' + level).hide();
                $('#gis_location_label_L' + level).hide();
            }
        }
        $.getJSONS3(this_url, s3_gis_load_locations, false);

        // Show the new level
        $('#gis_location_L' + level).removeClass('hidden').show();
        $('#gis_location_label_L' + level).removeClass('hidden').show();

        // Hide other levels & reset their contents
        s3_gis_dropdown_hide(level + 1);

        // Populate the real location_id field (unless a name is already present)
        if ( '' == $('#gis_location_name').val() ) {
            $('#' + s3_gis_location_id).val(new_id);
        }

    } else {
        // Zero selected: Hide other levels & reset their contents
        s3_gis_dropdown_hide(level);
        
        // If we're the top-level selector & there is no name defined
        if (( 1 == level ) && ( '' == $('#gis_location_name').val() )) {
            // Clear the real location_id field
            $('#' + s3_gis_location_id).val('');
        }
    }
}

function s3_gis_dropdown_hide(level) {
    // Hide other levels & reset their contents
    for (l=level; l <= 5; l=l + 1) {
        $('#gis_location_L' + l).hide().html(s3_gis_loading_locations);
        $('#gis_location_label_L' + l).hide();
    }
}

function s3_gis_save_location(name, lat, lon, addr_street) {
    // Locate the Parent - try the lowest level 1st
    var _parent = $('#gis_location_L5').val();
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
    var url;
    if ('' == S3.gis.uuid) {
        // Create a new record
        url = s3_gis_url + '/create.url?name=' + name;
    } else {
        // Update an existing record
        url = s3_gis_url + 'update.url?uuid=' + S3.gis.uuid + '&name=' + name;
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
                $('#' + s3_gis_location_id).val(new_id);
                // Store the UUID for future updates
                //var url_read = gis_url + '/' + new_id + '.json';
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

function s3_gis_geolocate(position) {
    // Get the current location
    var lat = position.coords.latitude;
    var lon = position.coords.longitude;
    //var elevation = position.coords.altitude;
    //var ce = position.coords.accuracy;
    //var le = position.coords.altitudeAccuracy;
    //position.coords.heading;
    //position.coords.speed;
    $('#gis_location_lat').val(lat);
    $('#gis_location_lon').val(lon);
}

// Coordinate Calculations
var s3_gis_calcDone = false;   // to track for finish button
var s3_gis_calcAnswer;         // a global answer to fill back using 1 function

function s3_gis_convertDD() {
    // Convert Degrees Minutes Seconds to Decimal Degrees
    var deg = $('#DDMMSS_deg').val();
    var min = $('#DDMMSS_min').val();
    var sec = $('#DDMMSS_sec').val();

    var invalid = false;

    if (deg == '') {
        deg = 0;
    } else if (isNaN(deg) || deg > 180 || deg < -180) {
        alert(s3_gis_degrees_validation_error);
        invalid = true;
    }
    if (min == '') {
        min = 0;
    } else if (isNaN(min) || min > 60 || min < 0) {
        alert(s3_gis_minutes_validation_error);
        invalid = true;
    }
    if (sec == '') {
        sec = 0;
    } else if (isNaN(sec) || sec > 60 || sec < 0) {
        alert(s3_gis_seconds_validation_error);
        invalid = true;
    }
    if (invalid == false) {
        var dec_min = (min*1.0 + (sec/60.0));
        if (deg > 0){
            s3_gis_calcAnswer = deg*1.0 + (dec_min/60.0);
        } else {
            s3_gis_calcAnswer = deg*1.0 - (dec_min/60.0);
        }
        $('#DDMMSS_dec').val(s3_gis_calcAnswer);
        s3_gis_calcDone = true;
    }
}

function s3_gis_convertGps() {
    // Convert GPS Coordinates to Decimal Degrees
    var deg = 0;
    var min = 0;
    deg = $('#gps_deg').val();
    min = $('#gps_min').val();

    var invalid = false;

    if (deg == '') {
        deg = 0;
    } else if (isNaN(deg) || deg > 180 || deg < -180) {
        alert(s3_gis_degrees_validation_error);
        invalid = true;
    }
    if (min == '') {
        min = 0;
    } else if (isNaN(min) || min > 60 || min < 0) {
        alert(s3_gis_minutes_validation_error);
        invalid = true;
    }
    if (invalid == false) {
        if (deg > 0){
            s3_gis_calcAnswer = (deg*1.0) + min/60.0;
        } else {
            s3_gis_calcAnswer = (deg*1.0) - min/60.0;
        }
        $('#gps_dec').val(s3_gis_calcAnswer);
        s3_gis_calcDone = true;
    }
}

function s3_gis_convertFillBack(whereto) {
    // Fill calculated values into main page in background
    if (s3_gis_calcDone == true) {
        if (whereto == 1) {
            $('#gis_location_lat').attr('value', s3_gis_calcAnswer);
        } else {
            $('#gis_location_lon').attr('value', s3_gis_calcAnswer);
        }
        return true;
    } else {
        alert(s3_gis_no_calculations_error);
    }
    return false;
}


$(function(){
    if ( typeof(s3_gis_location_id) == "undefined" ) {
        // This page doesn't include the Location Selector Widget
    } else {
        // Listen for Events & take appropriate Actions
    
        // When dropdowns are selected, open the next one in the hierarchy
        $('#gis_location_L0').change( function() {
            s3_gis_dropdown_select(1);
        });
        $('#gis_location_L1').change( function() {
            s3_gis_dropdown_select(2);
        });
        $('#gis_location_L2').change( function() {
            s3_gis_dropdown_select(3);
        });
        $('#gis_location_L3').change( function() {
            s3_gis_dropdown_select(4);
        });
        $('#gis_location_L4').change( function() {
            s3_gis_dropdown_select(5);
        });

        $('#gis_location_add-btn').click( function() {
            // When 'Add Location' pressed
            // Hide the now-redundant button
            $('#gis_location_add-btn').hide();
            // unhide the next part
            if (navigator.geolocation) {
                // HTML5 geolocation is available :)
                $('#gis_location_geolocate-btn').removeClass('hidden').show();
            } else {
                // geolocation is not available...IE sucks! ;)
            }
            $('#gis_location_map-btn').removeClass('hidden').show();
            $('#gis_location_name_label').removeClass('hidden').show();
            $('#gis_location_name').removeClass('hidden').show();
            $('#gis_location_addr_street_label').removeClass('hidden').show();
            $('#gis_street_addr_row').removeClass('hidden').show();
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

        $('#gis_location_geolocate-btn').click( function() {
            // Do an HTML5 GeoLocate: http://dev.w3.org/geo/api/spec-source.html
            navigator.geolocation.getCurrentPosition(s3_gis_geolocate);
        });

        $('form').submit( function() {
            // The form is being submitted

            // Do the normal form-submission tasks
            // @ToDo: Look to have this happen automatically
            // http://forum.jquery.com/topic/multiple-event-handlers-on-form-submit
            // http://api.jquery.com/bind/
            S3ClearNavigateAwayConfirm();

            // Check if a new location should be created
            var name = $('#gis_location_name').val();
            var lat = $('#gis_location_lat').val();
            var lon = $('#gis_location_lon').val();
            var addr_street = $('#gis_location_addr_street').val();

            // Only save a new Location if we have data
            if ('' == name) {
                if (('' == lat || '' == lon) && ('' == addr_street)) {
                    // There are no specific location details specified
                    // (Hierarchy may have been done but that's not our issue here)
                    // Allow the Form's save to continue
                    return true;
                } else {
                    // We don't have a name, but we do have details, so prompt the user?
                    // Need to distinguish between details from hierarchy & real details
                    // @ToDo
                    return true;
                }
            }
            // Save the new location
            s3_gis_save_location(name, lat, lon, addr_street);

            // Allow the Form's save to continue
            return true;
        });
    }
});

// Popups: Map & GPS Converter
Ext.onReady(function(){
    var converterWin;
    var converterButton = Ext.get('gis_location_converter-btn');
    var mapButton = Ext.get('gis_location_map-btn');

    if (mapButton) {
        mapButton.on('click', function() {
            // @ToDo: create the window on the first click and reuse on subsequent clicks
            mapWin.show(this);
        });
    }

    if (converterButton) {
        converterButton.on('click', function() {
            // create the window on the first click and reuse on subsequent clicks
            if (!converterWin) {
                converterWin = new Ext.Window({
                    applyTo: 'convert-win',
                    layout: 'fit',
                    width: 400,
                    height: 250,
                    closeAction: 'hide',
                    plain: true,

                    items: new Ext.TabPanel({
                        applyTo: 'convert-tabs',
                        autoTabs: true,
                        activeTab: 0,
                        deferredRender: false,
                        border: false
                    }),

                    buttons: [{
                        text: s3_gis_fill_lat,
                        disabled: false,
                        handler: function() {
                            if ( s3_gis_convertFillBack(1) ) {
                                s3_gis_calcDone = false;
                                $('#DDMMSS_dec').val('');
                                $('#gps_dec').val('');
                                //converterWin.hide();
                            }
                        }
                    },{
                        text: s3_gis_fill_lon,
                        handler: function() {
                            if ( s3_gis_convertFillBack(2) ) {
                                s3_gis_calcDone = false;
                                $('#DDMMSS_dec').val('');
                                $('#gps_dec').val('');
                                //converterWin.hide();
                            }
                        }
                    }]
                });
            }
            converterWin.show(this);
        });
    }
});
