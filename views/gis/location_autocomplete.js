{{_gis = response.s3.gis}}
<script type="text/javascript">//<![CDATA[
$(function() {
    var row, label, widget, comment, country_id, parent, url;
    var l1, l2, l3, l4, l5;

  {{try:}}
  {{uuid = oldlocation.uuid}}
    S3.gis.uuid = '{{=uuid}}';
    var old_level = '{{=oldlocation.level}}';
    var old_parent = '{{=oldlocation.parent}}';
    var old_name = '{{=oldlocation.name}}';
    var old_lat = '{{=oldlocation.lat}}';
    var old_lon = '{{=oldlocation.lon}}';
    var old_addr_street = '{{=oldlocation.addr_street}}';
  {{except:}}
    S3.gis.uuid = '';
    var old_level = '';
    var old_parent = '';
    var old_name = '';
    var old_lat = '';
    var old_lon = '';
    var old_addr_street = '';
  {{pass}}

    if (undefined == location_id){
        // If the calling view hasn't provided a value then use the default
        var location_id = '{{=request.controller + "_" + request.function + "_location_id"}}';
    }
    var location_id_row = '#' + location_id + '__row';

    // Hide the real Input row
    $(location_id_row).hide();
    
    // Section delimiter
    widget = '------------------------------------------------------------------------------------------------------------------------'
    row = "<tr id='gis_location_start__row'><td colspan='3' align='left'>" + widget + '</td></tr>';
    $(location_id_row).before(row);

    // Section header
    label = '{{=B(T("Location"))}}';
    row = "<tr id='gis_location_header__row'><td><label>" + label + '</label></td><td></td><td></td></tr>';
    $(location_id_row).before(row);

    // Help section
    //label = '{{=T("Select an existing Location")}}:'
    //row = "<tr id='gis_location_help__row'><td colspan='2'><label>" + label + '</label></td><td></td></tr>';
    //$(location_id_row).before(row);

  {{level = "0"}}
  {{try:}}
  {{label = _gis.location_hierarchy["L" + level]}}
    // L{{=level}}
    label = '{{=label}}';
  {{if len(_gis.countries) == 1:}}
    // Country is hardcoded
    country_id = {{=_gis.countries[response.s3.countries[0]].id}};
    widget = "<input id='gis_location_l{{=level}}' />";
    row = "<tr id='gis_location_l{{=level}}__row'><td><label>" + label + ':' + '</label></td><td>' + widget + '</td><td></td></tr>';
    $(location_id_row).before(row);
    $('#gis_location_l{{=level}}').val(country_id);
    // Hide
    $('#gis_location_l{{=level}}__row').hide();
    // Show the next level of hierarchy
    // (called after it has been defined)
  {{else:}}
    // Dropdown
    widget = "<select id='gis_location_l{{=level}}'></select>";
    comment = "<div title='" + label + '|' + '{{=T("Select to see a list of subdivisions.")}}' + "' id='gis_location_l{{=level}}_tooltip' class='tooltip'></div>";
    row = "<tr id='gis_location_l{{=level}}__row'><td><label>" + label + ':' + '</label></td><td>' + widget + '</td><td>' + comment + '</td></tr>';
    $(location_id_row).before(row);
    // Apply the tooltip which was missed 1st time round
    $('#gis_location_l{{=level}}_tooltip').cluetip({activation: 'hover', sticky: false, splitTitle: '|'});

    // Load locations
    url = '{{=URL(r=request, c="gis", f="location", args="search.json", vars={"filter":"=", "field":"level", "value":"L" + level})}}';
    load_locations = function(data, status){
	    var options = '';
	    var v = '';
	    if (data.length == 0) {
            options += '<option value="">' + '{{=T("No locations registered at this level")}}</options>';
        } else {
            options += '<option value="" selected>' + '{{=T("Select a location")}}' + '...</option>';
            for (var i = 0; i < data.length; i++){
                v = data[i].id;
                options += '<option value="' +  data[i].id + '">' + data[i].name + '</option>';
            }
	    }
	    $('#gis_location_l{{=level}}').html(options); 
	};	
    $.getJSONS3(url, load_locations, '{{=T("locations")}}');

    // When dropdown is selected
    $('#gis_location_l{{=level}}').change(function() {
        if (('' == $('#gis_location_lat').val() || '' == $('#gis_location_lon').val()) && ('' == $('#gis_location_addr_street').val()) ) {
            // Populate the real location_id field (unless a lat/lon/addr_street are present)
            var new_id = $(this).val();
            if ('' != new_id) {
                $('#' + location_id).val(new_id);
            }
        }
        // Show the next level of hierarchy
        s3_gis_locations_l{{=int(level) + 1}}();
    });
  {{pass}}
  {{except:}}
  {{pass}}

  {{level = "1"}}
    var s3_gis_locations_l{{=level}} = function(){
  {{try:}}
  {{label = _gis.location_hierarchy["L" + level]}}
    // L{{=level}}
    label = '{{=label}}';
    // Dropdown
    if (null == l{{=level}}) {
        widget = "<select id='gis_location_l{{=level}}'></select>";
        comment = "<div title='" + label + '|' + '{{=T("Select to see a list of subdivisions.")}}' + " id='gis_location_l{{=level}}_tooltip' class='tooltip'></div>";
        row = "<tr id='gis_location_l{{=level}}__row'><td><label>" + label + ':' + '</label></td><td>' + widget + '</td><td>' + comment + '</td></tr>';
        $('#gis_location_addr_street__row').before(row);
        l{{=level}} = true;
        // Apply the tooltip which was missed 1st time round
        $('#gis_location_l{{=level}}_tooltip').cluetip({activation: 'hover', sticky: false, splitTitle: '|'});
    }
    // Load locations
    parent = $('#gis_location_l{{=int(level) - 1}}').val();
    url = '{{=URL(r=request, c="gis", f="location", args="search.json", vars={"filter":"=", "field":"level", "value":"L" + level})}}&parent=' + parent;
    load_locations = function(data, status){
	    var options=''
	    var v = ''
	    if (data.length == 0) {
            options += '<option value="">' + '{{=T("No locations registered at this level")}}</options>';
        } else {
            options += '<option value="" selected>' + '{{=T("Select a location")}}' + '...</option>';
            for (var i = 0; i < data.length; i++){
                v = data[i].id;
                options += '<option value="' +  data[i].id + '">' + data[i].name + '</option>';
            }
	    }
	    $('#gis_location_l{{=level}}').html(options); 
	};	
    $.getJSONS3(url, load_locations, '{{=T("locations")}}');
    
    // When dropdown is selected
    $('#gis_location_l{{=level}}').change(function() {
        if (('' == $('#gis_location_lat').val() || '' == $('#gis_location_lon').val()) && ('' == $('#gis_location_addr_street').val()) ) {
            // Populate the real location_id field (unless a lat/lon/addr_street are present)
            var new_id = $(this).val();
            if ('' != new_id) {
                $('#' + location_id).val(new_id);
            }
        }
        // Show the next level of hierarchy
        s3_gis_locations_l{{=int(level) + 1}}();
    });
  {{except:}}
  {{pass}}
    }

  {{level = "2"}}
    var s3_gis_locations_l{{=level}} = function(){
  {{try:}}
  {{label = _gis.location_hierarchy["L" + level]}}
    // L{{=level}}
    label = '{{=label}}:';
    // Dropdown
    if (null == l{{=level}}) {
        widget = "<select id='gis_location_l{{=level}}'></select>";
        row = "<tr id='gis_location_l{{=level}}__row'><td><label>" + label + '</label></td><td>' + widget + '</td><td></td></tr>';
        $('#gis_location_addr_street__row').before(row);
        l{{=level}} = true;
    }
    // Load locations
    parent = $('#gis_location_l{{=int(level) - 1}}').val();
    url = '{{=URL(r=request, c="gis", f="location", args="search.json", vars={"filter":"=", "field":"level", "value":"L" + level})}}&parent=' + parent;
    load_locations = function(data, status){
	    var options=''
	    var v = ''
	    if (data.length == 0) {
            options += '<option value="">' + '{{=T("No locations registered at this level")}}</options>';
        } else {
            options += '<option value="" selected>' + '{{=T("Select a location")}}' + '...</option>';
            for (var i = 0; i < data.length; i++){
                v = data[i].id;
                options += '<option value="' +  data[i].id + '">' + data[i].name + '</option>';
            }
	    }
	    $('#gis_location_l{{=level}}').html(options); 
	};	
    $.getJSONS3(url, load_locations, '{{=T("locations")}}');
    
    // When dropdown is selected
    $('#gis_location_l{{=level}}').change(function() {
        if (('' == $('#gis_location_lat').val() || '' == $('#gis_location_lon').val()) && ('' == $('#gis_location_addr_street').val()) ) {
            // Populate the real location_id field (unless a lat/lon/addr_street are present)
            var new_id = $(this).val();
            if ('' != new_id) {
                $('#' + location_id).val(new_id);
            }
        }
        // Show the next level of hierarchy
        s3_gis_locations_l{{=int(level) + 1}}();
    });
  {{except:}}
  {{pass}}
    }

  {{level = "3"}}
    var s3_gis_locations_l{{=level}} = function(){
  {{try:}}
  {{label = _gis.location_hierarchy["L" + level]}}
    // L{{=level}}
    label = '{{=label}}:';
    // Dropdown
    if (null == l{{=level}}) {
        widget = "<select id='gis_location_l{{=level}}'></select>";
        row = "<tr id='gis_location_l{{=level}}__row'><td><label>" + label + '</label></td><td>' + widget + '</td><td></td></tr>';
        $('#gis_location_addr_street__row').before(row);
        l{{=level}} = true;
    }
    // Load locations
    parent = $('#gis_location_l{{=int(level) - 1}}').val();
    url = '{{=URL(r=request, c="gis", f="location", args="search.json", vars={"filter":"=", "field":"level", "value":"L" + level})}}&parent=' + parent;
    load_locations = function(data, status){
	    var options=''
	    var v = ''
	    if (data.length == 0) {
            options += '<option value="">' + '{{=T("No locations registered at this level")}}</options>';
        } else {
            options += '<option value="" selected>' + '{{=T("Select a location")}}' + '...</option>';
            for (var i = 0; i < data.length; i++){
                v = data[i].id;
                options += '<option value="' +  data[i].id + '">' + data[i].name + '</option>';
            }
	    }
	    $('#gis_location_l{{=level}}').html(options); 
	};	
    $.getJSONS3(url, load_locations, '{{=T("locations")}}');
    
    // When dropdown is selected
    $('#gis_location_l{{=level}}').change(function() {
        if (('' == $('#gis_location_lat').val() || '' == $('#gis_location_lon').val()) && ('' == $('#gis_location_addr_street').val()) ) {
            // Populate the real location_id field (unless a lat/lon/addr_street are present)
            var new_id = $(this).val();
            if ('' != new_id) {
                $('#' + location_id).val(new_id);
            }
        }
        // Show the next level of hierarchy
        s3_gis_locations_l{{=int(level) + 1}}();
    });
  {{except:}}
  {{pass}}
    }

  {{level = "4"}}
    var s3_gis_locations_l{{=level}} = function(){
  {{try:}}
  {{label = _gis.location_hierarchy["L" + level]}}
    // L{{=level}}
    label = '{{=label}}:';
    // Dropdown
    if (null == l{{=level}}) {
        widget = "<select id='gis_location_l{{=level}}'></select>";
        row = "<tr id='gis_location_l{{=level}}__row'><td><label>" + label + '</label></td><td>' + widget + '</td><td></td></tr>';
        $('#gis_location_addr_street__row').before(row);
        l{{=level}} = true;
    }
    // Load locations
    parent = $('#gis_location_l{{=int(level) - 1}}').val();
    url = '{{=URL(r=request, c="gis", f="location", args="search.json", vars={"filter":"=", "field":"level", "value":"L" + level})}}&parent=' + parent;
    load_locations = function(data, status){
	    var options=''
	    var v = ''
	    if (data.length == 0) {
            options += '<option value="">' + '{{=T("No locations registered at this level")}}</options>';
        } else {
            options += '<option value="" selected>' + '{{=T("Select a location")}}' + '...</option>';
            for (var i = 0; i < data.length; i++){
                v = data[i].id;
                options += '<option value="' +  data[i].id + '">' + data[i].name + '</option>';
            }
	    }
	    $('#gis_location_l{{=level}}').html(options); 
	};	
    $.getJSONS3(url, load_locations, '{{=T("locations")}}');
    
    // When dropdown is selected
    $('#gis_location_l{{=level}}').change(function() {
        if (('' == $('#gis_location_lat').val() || '' == $('#gis_location_lon').val()) && ('' == $('#gis_location_addr_street').val()) ) {
            // Populate the real location_id field (unless a lat/lon/addr_street are present)
            var new_id = $(this).val();
            if ('' != new_id) {
                $('#' + location_id).val(new_id);
            }
        }
        // Show the next level of hierarchy
        s3_gis_locations_l{{=int(level) + 1}}();
    });
  {{except:}}
  {{pass}}
    }

  {{level = "5"}}
    var s3_gis_locations_l{{=level}} = function(){
  {{try:}}
  {{label = _gis.location_hierarchy["L" + level]}}
    // L{{=level}}
    label = '{{=label}}:';
    // Dropdown
    if (null == l{{=level}}) {
        widget = "<select id='gis_location_l{{=level}}'></select>";
        row = "<tr id='gis_location_l{{=level}}__row'><td><label>" + label + '</label></td><td>' + widget + '</td><td></td></tr>';
        $('#gis_location_addr_street__row').before(row);
        l{{=level}} = true;
    }
    // Load locations
    parent = $('#gis_location_l{{=int(level) - 1}}').val();
    url = '{{=URL(r=request, c="gis", f="location", args="search.json", vars={"filter":"=", "field":"level", "value":"L" + level})}}&parent=' + parent;
    load_locations = function(data, status){
	    var options=''
	    var v = ''
	    if (data.length == 0) {
            options += '<option value="">' + '{{=T("No locations registered at this level")}}</options>';
        } else {
            options += '<option value="" selected>' + '{{=T("Select a location")}}' + '...</option>';
            for (var i = 0; i < data.length; i++){
                v = data[i].id;
                options += '<option value="' +  data[i].id + '">' + data[i].name + '</option>';
            }
	    }
	    $('#gis_location_l{{=level}}').html(options); 
	};	
    $.getJSONS3(url, load_locations, '{{=T("locations")}}');
    
    // When dropdown is selected
    $('#gis_location_l{{=level}}').change(function() {
        if (('' == $('#gis_location_lat').val() || '' == $('#gis_location_lon').val()) && ('' == $('#gis_location_addr_street').val()) ) {
            // Populate the real location_id field (unless a lat/lon/addr_street are present)
            var new_id = $(this).val();
            if ('' != new_id) {
                $('#' + location_id).val(new_id);
            }
        }
        // Show the next level of hierarchy
        s3_gis_locations_l{{=int(level) + 1}}();
    });
  {{except:}}
  {{pass}}
    }

    // Name
    // @ToDo: Localise according to current user's preference
    label = '{{=T("Name")}}:';
    widget = "<input id='gis_location_name' class='ac_input string' size='50' value='" + old_name + "' />";
    comment = "<div title='" + label + '|' + '{{=T("Enter a few characters of the name to select an existing Location or else simply type the name of the new Location.")}}' + "' id='gis_location_name_tooltip' class='tooltip'></div>";
    row = "<tr id='gis_location_addr_street__row'><td><label>" + label + '</label></td><td>' + widget + '</td><td>' + comment + '</td></tr>';
    $(location_id_row).before(row);
    // Apply the tooltip which was missed 1st time round
    $('#gis_location_name_tooltip').cluetip({activation: 'hover', sticky: false, splitTitle: '|'});

    // Autocomplete-enable the Name Input
    $('#gis_location_name').autocomplete('{{=URL(r=request, c="gis", f="location", args="search.json", vars={"filter":"~", "field":"name"})}}', {
        extraParams: {
            // Read 'parent' field dynamically
            // @ToDo: ensure that the parent search is hierarchical!
            parent: function() {
                        var parent = $('#gis_location_l5').val();
                        if (undefined == parent || '' == parent) {
                            parent = $('#gis_location_l4').val();
                            if (undefined == parent || '' == parent) {
                                parent = $('#gis_location_l3').val();
                                if (undefined == parent || '' == parent) {
                                    parent = $('#gis_location_l2').val();
                                    if (undefined == parent || '' == parent) {
                                        parent = $('#gis_location_l1').val();
                                        if (undefined == parent || '' == parent) {
                                            parent = $('#gis_location_l0').val();
                                        }
                                    }
                                }
                            }
                        }
                        return parent
                    }
        },
        // Don't cache
        cacheLength: 1,
        minChars: 2,
		//mustMatch: true,
		matchContains: true,
        dataType: 'json',
        parse: function(data) {
            var rows = new Array();
            for(var i=0; i<data.length; i++){
                rows[i] = { data:data[i], value:data[i].id, result:data[i].name };
            }
            return rows;
        },
        formatItem: function(row, i, n) {
            {{try:}}
            {{test = _gis.location_hierarchy["L1"]}}
            if (row.level == 'L1') {
                return row.name + ' ({{=_gis.location_hierarchy["L1"]}})';
            {{try:}}
            {{test = _gis.location_hierarchy["L2"]}}
            } else if (row.level == 'L2') {
                return row.name + ' ({{=_gis.location_hierarchy["L2"]}})';
            {{except:}}
            {{pass}}
            {{try:}}
            {{test = _gis.location_hierarchy["L3"]}}
            } else if (row.level == 'L3') {
                return row.name + ' ({{=_gis.location_hierarchy["L3"]}})';
            {{except:}}
            {{pass}}
            {{try:}}
            {{test = _gis.location_hierarchy["L4"]}}
            } else if (row.level == 'L4') {
                return row.name + ' ({{=_gis.location_hierarchy["L4"]}})';
            {{except:}}
            {{pass}}
            {{try:}}
            {{test = _gis.location_hierarchy["L5"]}}
            } else if (row.level == 'L5') {
                return row.name + ' ({{=_gis.location_hierarchy["L5"]}})';
            {{except:}}
            {{pass}}
            } else {
            {{except:}}
            {{pass}}
                return row.name;
            }
		}
    });
    $('#gis_location_name').change(function() {
        // If a new name is typed into the field, then we want to create a new Location, not update an existing one.
        $('#' + location_id).val('');
        S3.gis.uuid = '';
        // If a name is selected from the Autocomplete
        // Populate the ID, Street Address & Lat/Lon when the Name is selected
        $('#gis_location_name').result(function(event, data, formatted) {
            $('#' + location_id).val(data.id);
            S3.gis.uuid = data.uuid;
            $('#gis_location_lat').val(data.lat);
            $('#gis_location_lon').val(data.lon);
            $('#gis_location_addr_street').val(data.addr_street);
        });
    });
    
    // Street Address
    label = '{{=db.gis_location.addr_street.label}}:';
    widget = "<textarea id='gis_location_addr_street' class='text' rows='5' cols='46' value='" + old_addr_street + "' />";
    // ToDo: GeoCoder widget here
    comment = "<div title='" + label + '|' + "{{=T("This can either be the postal address or a simpler description (such as `Next to the Fuel Station`).")}}" + "' id='gis_location_add_street_tooltip' class='tooltip'></div>";
    row = "<tr id='gis_location_addr_street__row'><td><label>" + label + '</label></td><td>' + widget + '</td><td>' + comment + '</td></tr>';
    $(location_id_row).before(row);
    // Apply the tooltip which was missed 1st time round
    $('#gis_location_add_street_tooltip').cluetip({activation: 'hover', sticky: false, splitTitle: '|'});

  {{if len(_gis.countries) == 1:}}
    // Country hard-coded, so display L1
    // (needs to be called after definition of both the function & the addr_street)
    s3_gis_locations_l1();
  {{else:}}
  {{pass}}

  {{if _gis.map_selector:}}
    // Map-based selector
    label = '';
    widget = "<a id='openMap' href='#'>{{=T("Open Map")}}</a> ({{=Tstr("Can use this to identify the Location")}})";
    row = "<tr id='gis_location_map__row'><td><label>" + label + '</label></td><td>' + widget + '</td><td></td></tr>';
    $(location_id_row).before(row);
    var mapButton = Ext.get('openMap');
    mapButton.on('click', function(){
        win.show(this);
    });
  {{else:}}
  {{pass}}
  
    // Lat/Lon entry
    label = '{{=db.gis_location.lat.label}}:';
    widget = "<input id='gis_location_lat' value='" + old_lat + "' />";
    comment = '{{=db.gis_location.lat.comment}}';
    row = "<tr id='gis_location_lat__row'><td><label>" + label + '</label></td><td>' + widget + '</td><td>' + comment + '</td></tr>';
    $(location_id_row).before(row);
    // Apply the tooltip which was missed 1st time round
    $('#gis_location_lat_tooltip').cluetip({activation: 'hover', sticky: false, splitTitle: '|'});
    
    label = '{{=db.gis_location.lon.label}}:';
    widget = "<input id='gis_location_lon' value='" + old_lon + "' />";
    comment = '{{=db.gis_location.lon.comment}}';
    row = "<tr id='gis_location_lon__row'><td><label>" + label + '</label></td><td>' + widget + '</td><td>' + comment + '</td></tr>';
    $(location_id_row).before(row);
    
    // Submit button
    var buttonLabel = '{{=T("Save Location")}}';
    widget = "<a href='#' id='gis_location_submit_button' class='action-btn'>" + buttonLabel + '</a>';
    row = "<tr id='gis_location_submit__row'><td><label></label></td><td>" + widget + '</td><td></td></tr>';
    $(location_id_row).before(row);
    $('#gis_location_submit_button').click(function(){
        // Read the values
        var lat = $('#gis_location_lat').val();
        var lon = $('#gis_location_lon').val();
        var addr_street = $('#gis_location_addr_street').val();
        if (('' == lat || '' == lon) && ('' == addr_street) ) {
            // Don't save a location if we have no Lat/Lon
            return false;
        }
        // Use the Location name, if-defined
        var name = $('#gis_location_name').val();
        if (undefined == name || '' == name) {
            // Use the Resource name, if-defined
            name = $('#{{=request.controller + "_" + request.function + "_name"}}').val();
            if (undefined == name || '' == name) {
                // Define our own name
                name = '{{=request.controller + "_" + request.function}}' + Math.floor(Math.random()*1001);
            }
        }
        parent = $('#gis_location_l5').val();
        if (undefined == parent || '' == parent){
            parent = $('#gis_location_l4').val();
            if (undefined == parent || '' == parent){
                parent = $('#gis_location_l3').val();
                if (undefined == parent || '' == parent){
                    parent = $('#gis_location_l2').val();
                    if (undefined == parent || '' == parent){
                        parent = $('#gis_location_l1').val();
                        if (undefined == parent || '' == parent){
                            parent = $('#gis_location_l0').val();
                        }
                    }
                }
            }
        }
        
        // Submit the record
        if ('' == S3.gis.uuid) {
            url = '{{=URL(r=request, c="gis", f="location", args=["create.url"])}}' + '?name=' + name;
        } else {
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
        if (undefined == parent || '' == parent){
            // pass
        } else {
            url = url + '&parent=' + parent;
        }
        $.getJSON(url, function(data) {
            // Report Success/Failure
            showStatus(data.message);
            if (data.status == 'success') {
                if ('' == S3.gis.uuid) {
                    // Parse the new location
                    var new_id = data.message.split('=')[1];
                    // Update the value of the real field
                    $('#' + location_id).val(new_id);
                    // Store the UUID for future updates
                    var url_read = '{{=URL(r=request, c="gis", f="location")}}' + '/' + new_id + '.json';
                    $.getJSON(url_read, function(data) {
                        var domain = data['@domain'];
                        // Set 'global' variable for later pickup
                        var uuid = data['$_gis_location'][0]['@uuid'];
                        if (uuid.split('/')[0] == domain) {
                            S3.gis.uuid = uuid.split('/')[1];
                        } else {
                            S3.gis.uuid = uuid;
                        }
                    });
                }
            }
            
        });
    });
    
    // Section delimiter
    widget = '------------------------------------------------------------------------------------------------------------------------'
    row = "<tr id='gis_location_end__row'><td colspan='3' align='left'>" + widget + '</td></tr>';
    $(location_id_row).after(row);

});
//]]></script>

{{try:}}
{{=XML(_map)}}
{{except:}}
{{pass}}

{{include "gis/convert_gps.html"}}