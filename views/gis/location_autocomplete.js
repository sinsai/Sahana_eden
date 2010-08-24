{{_gis = response.s3.gis}}
{{try:}}
{{level = oldlocation.level}}
{{parent = oldlocation.parent}}
{{except:}}
{{pass}}
<script type="text/javascript">//<![CDATA[
$(function() {
    var row, label, widget, comment, country_id, parent, url;
    var l1, l2, l3, l4, l5;

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
    label = '{{=T("There are several ways which you can use to select the Location.")}}'
    row = "<tr id='gis_location_start__row'><td colspan='2'><label>" + label + '</label></td><td></td></tr>';
    $(location_id_row).before(row);
    label = '{{=T("Choose from one of the following options")}}:'
    row = "<tr id='gis_location_start__row'><td colspan='2'><label>" + label + '</label></td><td></td></tr>';
    $(location_id_row).before(row);

  {{if _gis.map_selector:}}
    // Map-based selector
    label = '{{=T("Click on a Map")}}:';
    widget = "<a id='openMap' href='#'>{{=T("Open Map")}}</a>";
    row = "<tr id='gis_location_start__row'><td><label>" + label + '</label></td><td>' + widget + '</td><td></td></tr>';
    $(location_id_row).before(row);
    var mapButton = Ext.get('openMap');
    mapButton.on('click', function(){
        win.show(this);
    });
  {{else:}}
  {{pass}}
  
  {{level = "0"}}
  {{try:}}
  {{label = _gis.location_hierarchy["L" + level]}}
    // L{{=level}}
    label = '{{=label}}:';
  {{if len(_gis.countries) == 1:}}
    // Country is hardcoded
    country_id = {{=_gis.countries[response.s3.countries[0]].id}};
    widget = "<input id='gis_location_l{{=level}}' />";
    row = "<tr id='gis_location_l{{=level}}__row'><td><label>" + label + '</label></td><td>' + widget + '</td><td></td></tr>';
    $(location_id_row).before(row);
    $('#gis_location_l{{=level}}').val(country_id);
    // Hide
    $('#gis_location_l{{=level}}__row').hide();
    // Show the next level of hierarchy
    s3_gis_locations_l{{=int(level) + 1}}(country_id);
  {{else:}}
    // Dropdown
    widget = "<select id='gis_location_l{{=level}}'></select>";
    row = "<tr id='gis_location_l{{=level}}__row'><td><label>" + label + '</label></td><td>' + widget + '</td><td></td></tr>';
    $(location_id_row).before(row);

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
    label = '{{=label}}:';
    // Dropdown
    if (null == l{{=level}}) {
        widget = "<select id='gis_location_l{{=level}}'></select>";
        row = "<tr id='gis_location_l{{=level}}__row'><td><label>" + label + '</label></td><td>' + widget + '</td><td></td></tr>';
        $('#gis_location_lat__row').before(row);
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
        $('#gis_location_lat__row').before(row);
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
        $('#gis_location_lat__row').before(row);
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
        $('#gis_location_lat__row').before(row);
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
        $('#gis_location_lat__row').before(row);
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
        // Show the next level of hierarchy
        s3_gis_locations_l{{=int(level) + 1}}();
    });
  {{except:}}
  {{pass}}
    }

    // Lat/Lon entry
    label = '{{=db.gis_location.lat.label}}:';
  {{try:}}
  {{lat = oldlocation.lat}}
    widget = "<input id='gis_location_lat' value='{{=lat}}' />";
  {{except:}}
    widget = "<input id='gis_location_lat' />";
  {{pass}} 
    comment = '{{=db.gis_location.lat.comment}}';
    row = "<tr id='gis_location_lat__row'><td><label>" + label + '</label></td><td>' + widget + '</td><td>' + comment + '</td></tr>';
    $(location_id_row).before(row);
    // Apply the tooltip which was missed 1st time round
    $('#gis_location_lat_tooltip').cluetip({activation: 'click', sticky: true, closePosition: 'title',closeText: '<img src="/{{=request.application}}/static/img/cross2.png" alt="close" />',splitTitle: '|'});
    
    label = '{{=db.gis_location.lon.label}}:';
  {{try:}}
  {{lon = oldlocation.lon}}
    widget = "<input id='gis_location_lon' value='{{=lon}}' />";
  {{except:}}
    widget = "<input id='gis_location_lon' />";
  {{pass}} 
    comment = '{{=db.gis_location.lon.comment}}';
    row = "<tr id='gis_location_lon__row'><td><label>" + label + '</label></td><td>' + widget + '</td><td>' + comment + '</td></tr>';
    $(location_id_row).before(row);
    
    // Submit button
  {{try:}}
  {{oldlocation = oldlocation.id}}
    var buttonLabel = '{{=T("Update")}}';
  {{except:}}
    var buttonLabel = '{{=T("Add New")}}';
  {{pass}}
    widget = "<a href='#' id='gis_location_submit_button' class='action-btn'>" + buttonLabel + '</a>';
    row = "<tr id='gis_location_submit__row'><td><label></label></td><td>" + widget + '</td><td></td></tr>';
    $(location_id_row).before(row);
    $('#gis_location_submit_button').click(function(){
        // Read the values
        var lat = $('#gis_location_lon').val();
        var lon = $('#gis_location_lon').val();
        if ('' == lat || '' == lon) {
            // Don't save a location if we have no Lat/Lon
            // ToDo: Allow saving a Street Address with no Lat/Lon?
            return false;
        }
        var name = $('{{=request.controller + "_" + request.function + "_name"}}').val();
        if (undefined == name || '' == name) {
            name = '{{=request.controller + "_" + request.function}}' + Math.floor(Math.random()*1001);
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
      {{try:}}
      {{oldlocation = oldlocation.id}}
        url = '{{=URL(r=request, c="gis", f="location", args=["create.url"])}}';
      {{except:}}
        url = '{{=URL(r=request, c="gis", f="location", args=["update.url"])}}';
      {{pass}}
        url = url + '?name=' + name + '&lat=' + lat + '&lon=' + lon;
      {{try:}}
      {{oldlocation = oldlocation.id}}
        url = url + '&uid=' + {{oldlocation.uuid}};
      {{except:}}
      {{pass}}
        if (undefined == parent || '' == parent){
            // Skip the parent
        } else {
            url = url + '&parent=' + parent;
        }
        $.getJSON(url, function(data) {
            // Report Success/Failure
            showStatus(data.message);
            if (data.status == 'success') {
                // Hide the button to prevent duplicate records being added
                // ToDo: Unhide if any of the selectors are changed again
                $('#gis_location_submit__row').hide();
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
   