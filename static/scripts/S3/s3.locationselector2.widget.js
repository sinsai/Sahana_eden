// Used by the S3LocationSelectorWidget (modules/widgets.py)
// This script is in Static to allow caching
// Dynamic constants (e.g. Internationalised strings) are set in server-generated script

// Main jQuery function
$(function(){
     if ( typeof(s3_gis_location_id) == "undefined" ) {
        // This page doesn't include the Location Selector Widget
    } else {
        // Hide the Label row
        // (we add a new label inside the widget boundary)
        $('#' + s3_gis_location_id + '__row1').hide();

        // Listen for Events & take appropriate Actions

        // L0
        $('#gis_location_L0').change( function() {
            s3_gis_l0_select();
        });

        // Street Address
        $('#gis_location_street').blur( function() {
            // @ToDo: Geocoder lookup
        });

        // Tabs
        $('#gis_location_search-btn').click( function(evt) {
            s3_gis_search_tab();
            evt.preventDefault();
        });

        $('#gis_location_add-btn').click( function(evt) {
            s3_gis_add_tab();
            evt.preventDefault();
        });

        // Set initial Autocompletes
        $('#gis_location_L1_ac').autocomplete({
            source: s3_gis_ac_set_source(1),
            minLength: 2,
            search: function(event, ui) {
                $( '#gis_location_L1_throbber' ).removeClass('hidden').show();
                return true;
            },
            response: function(event, ui, content) {
                $( '#gis_location_L1_throbber' ).hide();
                return content;
            },
            focus: function( event, ui ) {
                $('#gis_location_L1_ac').val( ui.item.name );
                return false;
            },
            select: function( event, ui ) {
                $('#gis_location_L1_ac').val( ui.item.name );
                $('#gis_location_L1').val( ui.item.id );
                // Hide the search results
                $('ul.ui-autocomplete').hide();
                return false;
            }
        }).data( 'autocomplete' )._renderItem = function( ul, item ) {
            return $( '<li></li>' )
                .data( 'item.autocomplete', item )
                .append( '<a>' + item.name + '</a>' )
                .appendTo( ul );
        };

        // L2
        $('#gis_location_L2_ac').autocomplete({
            source: s3_gis_ac_set_source(2),
            minLength: 2,
            search: function(event, ui) {
                $( '#gis_location_L2_throbber' ).removeClass('hidden').show();
                return true;
            },
            response: function(event, ui, content) {
                $( '#gis_location_L2_throbber' ).hide();
                return content;
            },
            focus: function( event, ui ) {
                $('#gis_location_L2_ac').val( ui.item.name );
                return false;
            },
            select: function( event, ui ) {
                $('#gis_location_L2_ac').val( ui.item.name );
                $('#gis_location_L2').val( ui.item.id );
                // Hide the search results
                $('ul.ui-autocomplete').hide();
                return false;
            }
        }).data( 'autocomplete' )._renderItem = function( ul, item ) {
            return $( '<li></li>' )
                .data( 'item.autocomplete', item )
                .append( '<a>' + item.name + '</a>' )
                .appendTo( ul );
        };
        
        $('form').submit( function() {
            // The form is being submitted

            // Do the normal form-submission tasks
            // @ToDo: Look to have this happen automatically
            // http://forum.jquery.com/topic/multiple-event-handlers-on-form-submit
            // http://api.jquery.com/bind/
            S3ClearNavigateAwayConfirm();

            // Save the location(s)
            s3_gis_save_locations();

            // Allow the Form's save to continue
            return true;
        });
    }
});

// Main Ext function
Ext.onReady(function(){
    // Map Popup
    var mapButton = Ext.get('gis_location_map-btn');
    if (mapButton) {
        mapButton.on('click', function() {
            mapWin.show(this);
        });
    }
});

function s3_gis_ac_set_source(level) {
    // Set the source for an Autocomplete

    // Lookup the immediate parent
    var parent = $('#gis_location_L' + (level - 1)).val();

    var grandparent;
    if (('' == parent) && (level > 1)) {
        // Lookup a grandparent
        grandparent = $('#gis_location_L' + (level - 2)).val();
        if (('' == grandparent) && (level > 2)) {
            grandparent = $('#gis_location_L' + (level - 2)).val();
            if (('' == grandparent) && (level > 3)) {
                grandparent = $('#gis_location_L' + (level - 3)).val();
                if (('' == grandparent) && (level > 4)) {
                    grandparent = $('#gis_location_L' + (level - 4)).val();
                    if (('' == grandparent) && (level > 5)) {
                        grandparent = $('#gis_location_L' + (level - 5)).val();
                    }
                }
            }
        }
    }

    if (parent) {
        // Filter on parent
        var source = s3_gis_url + '/search.json?filter=~&field=name&level=L' + level + '&parent=' + parent;
    } else if (grandparent) {
        // Filter on children (slower)
        var source = s3_gis_url + '/search.json?filter=~&field=name&level=L' + level + '&children=' + grandparent;
    } else {
        // No Filter possible beyond Level
        var source = s3_gis_url + '/search.json?filter=~&field=name&level=L' + level;
    }
    return source;
}

function s3_gis_show_level(level) {
    // Unhide field & label
    $( '#gis_location_L' + level + '_label__row' ).removeClass('hidden').show();
    $( '#gis_location_L' + level + '__row' ).removeClass('hidden').show();
}

function s3_gis_l0_select() {
    // @ToDo: Pull down the relevant hierarchy levels & labels

    // Unhide the appropriate hierarchy levels
    // Q: Is it better to have L1 & L2 unhidden to start with & simply change their labels quietly?
    // - Less Flashing Around
    //s3_gis_show_level(2);
    //s3_gis_show_level(1);

    // Set the Autocompletes' filters
    $( '#gis_location_L1_ac' ).autocomplete( 'option', 'source',  s3_gis_ac_set_source(1) );
    $( '#gis_location_L2_ac' ).autocomplete( 'option', 'source',  s3_gis_ac_set_source(2) );
}

function s3_gis_search_tab() {
    // 'Select Existing Location' tab has been selected

    // Hide the Add rows
    $('#gis_location_L0_label__row').hide();
    $('#gis_location_L0__row').hide();
    $('#gis_location_L1_label__row').hide();
    $('#gis_location_L1__row').hide();
    $('#gis_location_L2_label__row').hide();
    $('#gis_location_L2__row').hide();
    $('#gis_location_L3_label__row').hide();
    $('#gis_location_L3__row').hide();
    $('#gis_location_L4_label__row').hide();
    $('#gis_location_L4__row').hide();
    $('#gis_location_L5_label__row').hide();
    $('#gis_location_L5__row').hide();
    $('#gis_location___row').hide();
    $('#gis_location__label__row').hide();
    $('#gis_location_details-btn').hide();

    // Show the Search rows
    

    // Set the Classes on the tabs
    $('#gis_loc_add_tab').removeClass('tab_here').addClass('tab_other');
    $('#gis_loc_search_tab').removeClass('tab_last').addClass('tab_here');
}

function s3_gis_add_tab() {
    // 'Create New Location' tab has been selected
    
    // Hide the Search rows
    

    // Show the Add rows
    

    // Set the Classes on the tabs
    $('#gis_loc_add_tab').removeClass('tab_other').addClass('tab_here');
    $('#gis_loc_search_tab').removeClass('tab_here').addClass('tab_last');
}

function s3_gis_save_locations() {
    // Read current form values
    var name = $('#gis_location_name').val();
    var lat = $('#gis_location_lat').val();
    var lon = $('#gis_location_lon').val();
    var addr_street = $('#gis_location_addr_street').val();
    var addr_postcode = $('#gis_location_postcode').val();
    var L0 = $('#gis_location_L0').val();
    var L1 = $('#gis_location_L1').val();
    var L2 = $('#gis_location_L2').val();
    var L3 = $('#gis_location_L3').val();
    var L4 = $('#gis_location_L4').val();
    var L5 = $('#gis_location_L5').val();

    // Save Lx locations
    s3_gis_save_hierarchy(1);
    s3_gis_save_hierarchy(2);
    s3_gis_save_hierarchy(3);
    s3_gis_save_hierarchy(4);
    s3_gis_save_hierarchy(5);
    
    // Save this location
    s3_gis_save_location();
}

function s3_gis_save_hierarchy(level) {
    // Save the hierarchy locations if they have text visible but no selected ID
    // @ToDo: have the back-end function this calls return the existing ID if there is a location with the same name at this level/filter

    var name = $( '#gis_location_L' + level + '_ac' ).val();
    var id = $( '#gis_location_L' + level).val();
    if ((name != '') && (id == '')) {
        // Read the Parent
        var parent = $( '#gis_location_L' + (level - 1)).val();
        if (('' == parent) && (level > 1)) {
            // Lookup a grandparent to use instead
            // @ToDo: Check for mode strict
            parent = $('#gis_location_L' + (level - 2)).val();
            if (('' == arent) && (level > 2)) {
                parent = $('#gis_location_L' + (level - 2)).val();
                if (('' == parent) && (level > 3)) {
                    parent = $('#gis_location_L' + (level - 3)).val();
                    if (('' == parent) && (level > 4)) {
                        parent = $('#gis_location_L' + (level - 4)).val();
                        if (('' == parent) && (level > 5)) {
                            parent = $('#gis_location_L' + (level - 5)).val();
                        }
                    }
                }
            }
        }

        // Prepare the URL
        var url = s3_gis_url + '/create.url?name=' + name;
        if (undefined == parent || '' == parent){
            // pass
        } else {
            url = url + '&parent=' + parent;
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
                    // Update the real Lx value to ensure parents set appropriately for future records
                    $( '#gis_location_L' + level).val(new_id);
                }
            }
        });
    }
}

function s3_gis_save_location() {
    // Save the main location record
}