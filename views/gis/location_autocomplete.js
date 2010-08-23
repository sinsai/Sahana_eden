{{_gis = response.s3.gis}}
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
    widget = "<input id='gis_location_lat' />";
    comment = '{{=db.gis_location.lat.comment}}';
    row = "<tr id='gis_location_lat__row'><td><label>" + label + '</label></td><td>' + widget + '</td><td>' + comment + '</td></tr>';
    $(location_id_row).before(row);
    // Apply the tooltip which was missed 1st time round
    // Need to make it not re-apply to existing ones
    //$('.tooltip').cluetip({activation: 'click', sticky: true, closePosition: 'title',closeText: '<img src="/{{=request.application}}/static/img/cross2.png" alt="close" />',splitTitle: '|'});
    
    label = '{{=db.gis_location.lon.label}}:';
    widget = "<input id='gis_location_lon' />";
    comment = '{{=db.gis_location.lon.comment}}';
    row = "<tr id='gis_location_lon__row'><td><label>" + label + '</label></td><td>' + widget + '</td><td>' + comment + '</td></tr>';
    $(location_id_row).before(row);
    
    // Submit button
    widget = "<a href='#' class='action-btn'>Add New</a>";
    row = "<tr id='gis_location_submit__row'><td><label></label></td><td>" + widget + '</td><td></td></tr>';
    $(location_id_row).before(row);
    
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
   