{{_gis = response.s3.gis}}
{{if not _gis.location_id:}}
{{else:}}
<script type="text/javascript">//<![CDATA[
$(function() {
    var empty_set = '<option value="">' + '{{=T("No locations registered at this level")}}</option>';
    var loading_locations = '<option value="">' + '{{=T("Loading Locations...")}}</option>';
    var select_location = '<option value="" selected>' + '{{=T("Select a location")}}' + '...</option>';
    var row1, row2, label, widget, comment, _parent, url;
    // Flags to tell us whether the widgets are displayed
    var l1, l2, l3, l4, l5;

  {{try:}}
  {{uuid = oldlocation.uuid}}
    // Values from the existing record
    S3.gis.uuid = '{{=uuid}}';
    S3.gis.level = '{{=oldlocation.level}}';
    var old_id = '{{=oldlocation.id}}';
    var old_parent = '{{=oldlocation.parent}}';
    var old_name = '{{=oldlocation.name}}';
    {{if oldlocation.lat:}}
    var old_lat = '{{=oldlocation.lat}}';
    {{else:}}
    var old_lat = '';
    {{pass}}
    {{if oldlocation.lon:}}
    var old_lon = '{{=oldlocation.lon}}';
    {{else:}}
    var old_lon = '';
    {{pass}}
    {{if oldlocation.addr_street:}}
    var old_addr_street = '{{=oldlocation.addr_street}}';
    {{else:}}
    var old_addr_street = '';
    {{pass}}
  {{except:}}
    S3.gis.uuid = '';
    S3.gis.level = '';
    var old_id = '';
    var old_parent = '';
    var old_name = '';
    var old_lat = '';
    var old_lon = '';
    var old_addr_street = '';
  {{pass}}

  {{if response.s3.gis.location_id == True:}}
  // If the calling view hasn't provided a value then use the default
  var location_id = '{{=request.controller + "_" + request.function + "_location_id"}}';   
  {{else:}}
  //For custom Non-CRUD forms
  var location_id = '{{=response.s3.gis.location_id}}';   
  {{pass}}
    var location_id_row1 = '#' + location_id + '__row1';
    var location_id_row = '#' + location_id + '__row';

    // Hide the real Input row
    $(location_id_row1).hide();
    $(location_id_row).hide();
    
    // Section delimiter
    widget = '------------------------------------------------------------------------------------------------------------------------'
    row1 = "<tr id='gis_location_start__row'><td colspan='2' align='left'>" + widget + '</td></tr>';
    $(location_id_row).before(row1);

    // Section header
    label = '{{=B(T("Location"))}}';
    row1 = "<tr id='gis_location_header__row'><td colspan='2'><label>" + label + '</label></td></tr>';
    $(location_id_row).before(row1);

    // Help section
    //label = '{{=T("Select an existing Location")}}:'
    //row1 = "<tr id='gis_location_help__row'><td colspan='2'><label>" + label + '</label></td></tr>';
    //$(location_id_row).before(row1);

  {{level = "0"}}
  S3.gis.locations_l{{=level}} = function(){
  {{try:}}
  {{label = _gis.location_hierarchy["L" + level]}}
    // L{{=level}}
    label = '{{=label}}';
  {{if len(_gis.countries) == 1:}}
    // Country is hardcoded
    var country_id = {{=_gis.countries[response.s3.countries[0]].id}};
    widget = "<input id='gis_location_l{{=level}}' />";
    row1 = "<tr id='gis_location_l{{=level}}__row1'><td colspan='2'><label>" + label + ':' + '</label></td></tr>';
    row2 = "<tr id='gis_location_l{{=level}}__row'><td>" + widget + '</td><td></td></tr>';
    $(location_id_row).before(row1);
    $(location_id_row).before(row2);
    $('#gis_location_l{{=level}}').val(country_id);
    // Hide
    $('#gis_location_l{{=level}}__row1').hide();
    $('#gis_location_l{{=level}}__row').hide();
    // Show the next level of hierarchy
    // (called after it has been defined)
  {{else:}}
    // Dropdown
    widget = "<select id='gis_location_l{{=level}}'>" + loading_locations + '</select>';
  {{if _gis.edit_L0:}}
    comment = "<div><a href='{{=URL(r=request, c="gis", f="location", args="create", vars=dict(format="popup", level="L" + level))}}' id='gis_l{{=level}}_colorbox' class='colorbox' target='_top' title='{{=T("Add")}}" + ' ' + label + "'>{{=T("Add")}}" + ' ' + label + "</a><div title='" + label + '|' + '{{=T("Select to see a list of subdivisions.")}}' + "' id='gis_location_l{{=level}}_tooltip' class='tooltip'></div></div>";
  {{else:}}
    comment = "<div title='" + label + '|' + '{{=T("Select to see a list of subdivisions.")}}' + "' id='gis_location_l{{=level}}_tooltip' class='tooltip'></div>";
  {{pass}}
    row1 = "<tr id='gis_location_l{{=level}}__row1'><td colspan='2'><label>" + label + ':' + '</label></td></tr>';
    row2 = "<tr id='gis_location_l{{=level}}__row'><td>" + widget + '</td><td>' + comment + '</td></tr>';
    $('#gis_location_header__row').after(row2);
    $('#gis_location_header__row').after(row1);
    // Apply the tooltip which was missed 1st time round
    $('#gis_location_l{{=level}}_tooltip').cluetip({activation: 'hover', sticky: false, splitTitle: '|'});
    // Apply the colorbox which was missed 1st time round
    $('#gis_l{{=level}}_colorbox').click(function(){
        $.fn.colorbox({iframe:true, width:'99%', height:'99%', href:this.href, title:this.title});
        return false;
    });

    // Load locations
    url = '{{=URL(r=request, c="gis", f="location", args="search.json", vars={"filter":"=", "field":"level", "value":"L" + level})}}';
    load_locations = function(data, status){
        var options;
        var v = '';
        if (data.length == 0) {
            options = empty_set;
        } else {
            options = select_location;
            for (var i = 0; i < data.length; i++){
                v = data[i].id;
                options += '<option value="' +  data[i].id + '">' + data[i].name + '</option>';
            }
        }
        $('#gis_location_l{{=level}}').html(options);
        if (S3.gis.level == 'L0') {
            // Set the Country to this location
            $('#gis_location_l{{=level}}').val(old_id);
        } else if (S3.gis.level == 'L1') {
            // Set the Country to the parent 
            $('#gis_location_l{{=level}}').val(old_parent);
            // Show the next level of hierarchy
            S3.gis.locations_l{{=int(level) + 1}}(false);
        } else if (old_parent) {
            // Get the details for the parents
            // Calling old_id is an extra level of hierarchy to lookup, however
            // we don't assume that an L2 is parented to L1 - might skip a level!
            url = '{{=URL(r=request, c="gis", f="location")}}' + '/' + old_id + '/parents.json';
            $.getJSON(url, function(data) {
                //showStatus('{{=T("Looking up Parents")}}');
                // Parse the new location
                S3.gis.old_l0 = data['L0'];
                S3.gis.old_l1 = data['L1'];
                S3.gis.old_l2 = data['L2'];
                S3.gis.old_l3 = data['L3'];
                S3.gis.old_l4 = data['L4'];
                S3.gis.old_l5 = data['L5'];
                // Set to this value
                $('#gis_location_l{{=level}}').val(S3.gis.old_l0);
                // Show the next level of hierarchy
                S3.gis.locations_l{{=int(level) + 1}}(false);
            });
        };
    };	
    $.getJSONS3(url, load_locations, false);
    // When dropdown is selected
    $('#gis_location_l{{=level}}').change(function() {
        if (('' == $('#gis_location_lat').val() || '' == $('#gis_location_lon').val()) && ('' == $('#gis_location_addr_street').val()) ) {
            // Populate the real location_id field (unless a lat/lon/addr_street are present)
            var new_id = $(this).val();
            if ('' != new_id) {
                $('#' + location_id).val(new_id);
            }
            // Set the name box to this value
            $('#gis_location_name').val($('#gis_location_l{{=level}} :selected').text());
        }
        // Show the next level of hierarchy
        S3.gis.locations_l{{=int(level) + 1}}(false);
    });
  {{pass}}
  {{except:}}
  {{pass}}
    }

  {{level = "1"}}
    S3.gis.locations_l{{=level}} = function(preloaded){
  {{try:}}
  {{label = _gis.location_hierarchy["L" + level]}}
    // L{{=level}}
    label = '{{=label}}';
    // Dropdown
    if (null == l{{=level}}) {
        widget = "<select id='gis_location_l{{=level}}'>" + loading_locations + '</select>';
      {{if _gis.edit_L1:}}
        comment = "<div><a href='{{=URL(r=request, c="gis", f="location", args="create", vars=dict(format="popup", level="L" + level))}}' id='gis_l{{=level}}_colorbox' class='colorbox' target='_top' title='{{=T("Add")}}" + ' ' + label + "'>{{=T("Add")}}" + ' ' + label + "</a><div title='" + label + '|' + '{{=T("Select to see a list of subdivisions.")}}' + "' id='gis_location_l{{=level}}_tooltip' class='tooltip'></div></div>";
      {{else:}}
        comment = "<div title='" + label + '|' + '{{=T("Select to see a list of subdivisions.")}}' + "' id='gis_location_l{{=level}}_tooltip' class='tooltip'></div>";
      {{pass}}
        row1 = "<tr id='gis_location_l{{=level}}__row1'><td colspan='2'><label>" + label + ':' + '</label></td></tr>';
        row2 = "<tr id='gis_location_l{{=level}}__row'><td>" + widget + '</td><td>' + comment + '</td></tr>';
        $('#gis_location_name__row1').before(row1);
        $('#gis_location_name__row1').before(row2);
        l{{=level}} = true;
        // Apply the tooltip which was missed 1st time round
        $('#gis_location_l{{=level}}_tooltip').cluetip({activation: 'hover', sticky: false, splitTitle: '|'});
        // Apply the colorbox which was missed 1st time round
        $('#gis_l{{=level}}_colorbox').click(function(){
            _parent = $('#gis_location_l{{=int(level) - 1}}').val();
            url = this.href + '&parent=' + _parent;
            $.fn.colorbox({iframe:true, width:'99%', height:'99%', href:url, title:this.title});
            return false;
        });
    }
    if (preloaded) {
        options = empty_set;
        $('#gis_location_l{{=level}}').html(options);
    } else {
        // Load locations
        _parent = $('#gis_location_l{{=int(level) - 1}}').val();
        url = '{{=URL(r=request, c="gis", f="location", args="search.json", vars={"filter":"=", "field":"level", "value":"L" + level})}}&parent=' + _parent;
        load_locations = function(data, status){
            var options;
            var v = '';
            if (data.length == 0) {
                options = empty_set;
            } else {
                options = select_location;
                for (var i = 0; i < data.length; i++){
                    v = data[i].id;
                    options += '<option value="' +  data[i].id + '">' + data[i].name + '</option>';
                }
            }
            $('#gis_location_l{{=level}}').html(options);
            if (S3.gis.level == 'L1') {
                // Set to this location
                $('#gis_location_l{{=level}}').val(old_id);
            } else if (S3.gis.old_l1) {
                // Set to the value we pulled earlier
                $('#gis_location_l{{=level}}').val(S3.gis.old_l1);
                // Show the next level of hierarchy
                S3.gis.locations_l{{=int(level) + 1}}(false);
            };
        };
        // @ToDo Test
        //var sync = true;
        //$.getJSONS3(url, load_locations, '{{=T("locations")}}', sync);
        $.getJSONS3(url, load_locations, false);
    }
    // When dropdown is selected
    $('#gis_location_l{{=level}}').change(function() {
        if (('' == $('#gis_location_lat').val() || '' == $('#gis_location_lon').val()) && ('' == $('#gis_location_addr_street').val()) ) {
            // Populate the real location_id field (unless a lat/lon/addr_street are present)
            var new_id = $(this).val();
            if ('' != new_id) {
                $('#' + location_id).val(new_id);
            }
            // Set the name box to this value
            $('#gis_location_name').val($('#gis_location_l{{=level}} :selected').text());
        }
        // Show the next level of hierarchy
        S3.gis.locations_l{{=int(level) + 1}}(false);
    });
  {{except:}}
  {{pass}}
    }

  {{level = "2"}}
    S3.gis.locations_l{{=level}} = function(preloaded){
  {{try:}}
  {{label = _gis.location_hierarchy["L" + level]}}
    // L{{=level}}
    label = '{{=label}}:';
    // Dropdown
    if (null == l{{=level}}) {
        widget = "<select id='gis_location_l{{=level}}'>" + loading_locations + '</select>';
      {{if _gis.edit_L2:}}
        comment = "<div><a href='{{=URL(r=request, c="gis", f="location", args="create", vars=dict(format="popup", level="L" + level))}}' id='gis_l{{=level}}_colorbox' class='colorbox' target='_top' title='{{=T("Add")}}" + ' ' + label + "'>{{=T("Add")}}" + ' ' + label + "</a><div title='" + label + '|' + '{{=T("Select to see a list of subdivisions.")}}' + "' id='gis_location_l{{=level}}_tooltip' class='tooltip'></div></div>";
      {{else:}}
        comment = "<div title='" + label + '|' + '{{=T("Select to see a list of subdivisions.")}}' + "' id='gis_location_l{{=level}}_tooltip' class='tooltip'></div>";
      {{pass}}
        row1 = "<tr id='gis_location_l{{=level}}__row1'><td colspan='2'><label>" + label + '</label></td></tr>';
        row2 = "<tr id='gis_location_l{{=level}}__row'><td>" + widget + '</td><td>' + comment + '</td></tr>';
        $('#gis_location_name__row1').before(row1);
        $('#gis_location_name__row1').before(row2);
        l{{=level}} = true;
        // Apply the tooltip which was missed 1st time round
        $('#gis_location_l{{=level}}_tooltip').cluetip({activation: 'hover', sticky: false, splitTitle: '|'});
        // Apply the colorbox which was missed 1st time round
        $('#gis_l{{=level}}_colorbox').click(function(){
            _parent = $('#gis_location_l{{=int(level) - 1}}').val();
            url = this.href + '&parent=' + _parent;
            $.fn.colorbox({iframe:true, width:'99%', height:'99%', href:url, title:this.title});
            return false;
        });
    }
    if (preloaded) {
        options = empty_set;
        $('#gis_location_l{{=level}}').html(options);
    } else {
        // Load locations
        _parent = $('#gis_location_l{{=int(level) - 1}}').val();
        url = '{{=URL(r=request, c="gis", f="location", args="search.json", vars={"filter":"=", "field":"level", "value":"L" + level})}}&parent=' + _parent;
        load_locations = function(data, status){
            var options;
            var v = '';
            if (data.length == 0) {
                options = empty_set;
            } else {
                options = select_location;
                for (var i = 0; i < data.length; i++){
                    v = data[i].id;
                    options += '<option value="' +  data[i].id + '">' + data[i].name + '</option>';
                }
            }
            $('#gis_location_l{{=level}}').html(options);
            if (S3.gis.level == 'L2') {
                // Set to this location
                $('#gis_location_l{{=level}}').val(old_id);
            } else if (S3.gis.old_l2) {
                // Set to the value we pulled earlier
                $('#gis_location_l{{=level}}').val(S3.gis.old_l2);
                // Show the next level of hierarchy
                S3.gis.locations_l{{=int(level) + 1}}(false);
            };
        };	
        $.getJSONS3(url, load_locations, false);
    }
    // When dropdown is selected
    $('#gis_location_l{{=level}}').change(function() {
        if (('' == $('#gis_location_lat').val() || '' == $('#gis_location_lon').val()) && ('' == $('#gis_location_addr_street').val()) ) {
            // Populate the real location_id field (unless a lat/lon/addr_street are present)
            var new_id = $(this).val();
            if ('' != new_id) {
                $('#' + location_id).val(new_id);
            }
            // Set the name box to this value
            $('#gis_location_name').val($('#gis_location_l{{=level}} :selected').text());
        }
        // Show the next level of hierarchy
        S3.gis.locations_l{{=int(level) + 1}}(false);
    });
  {{except:}}
  {{pass}}
    }

  {{level = "3"}}
    S3.gis.locations_l{{=level}} = function(preloaded){
  {{try:}}
  {{label = _gis.location_hierarchy["L" + level]}}
    // L{{=level}}
    label = '{{=label}}:';
    // Dropdown
    if (null == l{{=level}}) {
        widget = "<select id='gis_location_l{{=level}}'>" + loading_locations + '</select>';
      {{if _gis.edit_L3:}}
        comment = "<div><a href='{{=URL(r=request, c="gis", f="location", args="create", vars=dict(format="popup", level="L" + level))}}' id='gis_l{{=level}}_colorbox' class='colorbox' target='_top' title='{{=T("Add")}}" + ' ' + label + "'>{{=T("Add")}}" + ' ' + label + "</a><div title='" + label + '|' + '{{=T("Select to see a list of subdivisions.")}}' + "' id='gis_location_l{{=level}}_tooltip' class='tooltip'></div></div>";
      {{else:}}
        comment = "<div title='" + label + '|' + '{{=T("Select to see a list of subdivisions.")}}' + "' id='gis_location_l{{=level}}_tooltip' class='tooltip'></div>";
      {{pass}}
        row1 = "<tr id='gis_location_l{{=level}}__row1'><td colspan='2'><label>" + label + '</label></td></tr>';
        row2 = "<tr id='gis_location_l{{=level}}__row'><td>" + widget + '</td><td>' + comment + '</td></tr>';
        $('#gis_location_name__row1').before(row1);
        $('#gis_location_name__row1').before(row2);
        l{{=level}} = true;
        // Apply the tooltip which was missed 1st time round
        $('#gis_location_l{{=level}}_tooltip').cluetip({activation: 'hover', sticky: false, splitTitle: '|'});
        // Apply the colorbox which was missed 1st time round
        $('#gis_l{{=level}}_colorbox').click(function(){
            _parent = $('#gis_location_l{{=int(level) - 1}}').val();
            url = this.href + '&parent=' + _parent;
            $.fn.colorbox({iframe:true, width:'99%', height:'99%', href:url, title:this.title});
            return false;
        });
    }
    if (preloaded) {
        options = empty_set;
        $('#gis_location_l{{=level}}').html(options);
    } else {
        // Load locations
        _parent = $('#gis_location_l{{=int(level) - 1}}').val();
        url = '{{=URL(r=request, c="gis", f="location", args="search.json", vars={"filter":"=", "field":"level", "value":"L" + level})}}&parent=' + _parent;
        load_locations = function(data, status){
            var options;
            var v = '';
            if (data.length == 0) {
                options = empty_set;
            } else {
                options = select_location;
                for (var i = 0; i < data.length; i++){
                    v = data[i].id;
                    options += '<option value="' +  data[i].id + '">' + data[i].name + '</option>';
                }
            }
            $('#gis_location_l{{=level}}').html(options);
            if (S3.gis.level == 'L3') {
                // Set to this location
                $('#gis_location_l{{=level}}').val(old_id);
            } else if (S3.gis.old_l3) {
                // Set to the value we pulled earlier
                $('#gis_location_l{{=level}}').val(S3.gis.old_l3);
                // Show the next level of hierarchy
                S3.gis.locations_l{{=int(level) + 1}}(false);
            };
        };	
        $.getJSONS3(url, load_locations, false);
    }
    // When dropdown is selected
    $('#gis_location_l{{=level}}').change(function() {
        if (('' == $('#gis_location_lat').val() || '' == $('#gis_location_lon').val()) && ('' == $('#gis_location_addr_street').val()) ) {
            // Populate the real location_id field (unless a lat/lon/addr_street are present)
            var new_id = $(this).val();
            if ('' != new_id) {
                $('#' + location_id).val(new_id);
            }
            // Set the name box to this value
            $('#gis_location_name').val($('#gis_location_l{{=level}} :selected').text());
        }
        // Show the next level of hierarchy
        S3.gis.locations_l{{=int(level) + 1}}(false);
    });
  {{except:}}
  {{pass}}
    }

  {{level = "4"}}
    S3.gis.locations_l{{=level}} = function(preloaded){
  {{try:}}
  {{label = _gis.location_hierarchy["L" + level]}}
    // L{{=level}}
    label = '{{=label}}:';
    // Dropdown
    if (null == l{{=level}}) {
        widget = "<select id='gis_location_l{{=level}}'>" + loading_locations + '</select>';
      {{if _gis.edit_L4:}}
        comment = "<div><a href='{{=URL(r=request, c="gis", f="location", args="create", vars=dict(format="popup", level="L" + level))}}' id='gis_l{{=level}}_colorbox' class='colorbox' target='_top' title='{{=T("Add")}}" + ' ' + label + "'>{{=T("Add")}}" + ' ' + label + "</a><div title='" + label + '|' + '{{=T("Select to see a list of subdivisions.")}}' + "' id='gis_location_l{{=level}}_tooltip' class='tooltip'></div></div>";
      {{else:}}
        comment = "<div title='" + label + '|' + '{{=T("Select to see a list of subdivisions.")}}' + "' id='gis_location_l{{=level}}_tooltip' class='tooltip'></div>";
      {{pass}}
        row1 = "<tr id='gis_location_l{{=level}}__row1'><td colspan='2'><label>" + label + '</label></td></tr>';
        row2 = "<tr id='gis_location_l{{=level}}__row'><td>" + widget + '</td><td>' + comment + '</td></tr>';
        $('#gis_location_name__row1').before(row1);
        $('#gis_location_name__row1').before(row2);
        l{{=level}} = true;
        // Apply the tooltip which was missed 1st time round
        $('#gis_location_l{{=level}}_tooltip').cluetip({activation: 'hover', sticky: false, splitTitle: '|'});
        // Apply the colorbox which was missed 1st time round
        $('#gis_l{{=level}}_colorbox').click(function(){
            _parent = $('#gis_location_l{{=int(level) - 1}}').val();
            url = this.href + '&parent=' + _parent;
            $.fn.colorbox({iframe:true, width:'99%', height:'99%', href:url, title:this.title});
            return false;
        });
    }
    if (preloaded) {
        options = empty_set;
        $('#gis_location_l{{=level}}').html(options);
    } else {
        // Load locations
        _parent = $('#gis_location_l{{=int(level) - 1}}').val();
        url = '{{=URL(r=request, c="gis", f="location", args="search.json", vars={"filter":"=", "field":"level", "value":"L" + level})}}&parent=' + _parent;
        load_locations = function(data, status){
            var options;
            var v = '';
            if (data.length == 0) {
                options = empty_set;
            } else {
                options = select_location;
                for (var i = 0; i < data.length; i++){
                    v = data[i].id;
                    options += '<option value="' +  data[i].id + '">' + data[i].name + '</option>';
                }
            }
            $('#gis_location_l{{=level}}').html(options);
            if (S3.gis.level == 'L4') {
                // Set to this location
                $('#gis_location_l{{=level}}').val(old_id);
            } else if (S3.gis.old_l4) {
                // Set to the value we pulled earlier
                $('#gis_location_l{{=level}}').val(S3.gis.old_l4);
                // Show the next level of hierarchy
                S3.gis.locations_l{{=int(level) + 1}}(false);
            };
        };	
        $.getJSONS3(url, load_locations, false);
    }
    // When dropdown is selected
    $('#gis_location_l{{=level}}').change(function() {
        if (('' == $('#gis_location_lat').val() || '' == $('#gis_location_lon').val()) && ('' == $('#gis_location_addr_street').val()) ) {
            // Populate the real location_id field (unless a lat/lon/addr_street are present)
            var new_id = $(this).val();
            if ('' != new_id) {
                $('#' + location_id).val(new_id);
            }
            // Set the name box to this value
            $('#gis_location_name').val($('#gis_location_l{{=level}} :selected').text());
        }
        // Show the next level of hierarchy
        S3.gis.locations_l{{=int(level) + 1}}(false);
    });
  {{except:}}
  {{pass}}
    }

  {{level = "5"}}
    S3.gis.locations_l{{=level}} = function(preloaded){
  {{try:}}
  {{label = _gis.location_hierarchy["L" + level]}}
    // L{{=level}}
    label = '{{=label}}:';
    // Dropdown
    if (null == l{{=level}}) {
        widget = "<select id='gis_location_l{{=level}}'>" + loading_locations + '</select>';
      {{if _gis.edit_L5:}}
        comment = "<div><a href='{{=URL(r=request, c="gis", f="location", args="create", vars=dict(format="popup", level="L" + level))}}' id='gis_l{{=level}}_colorbox' class='colorbox' target='_top' title='{{=T("Add")}}" + ' ' + label + "'>{{=T("Add")}}" + ' ' + label + "</a><div title='" + label + '|' + '{{=T("Select to see a list of subdivisions.")}}' + "' id='gis_location_l{{=level}}_tooltip' class='tooltip'></div></div>";
      {{else:}}
        comment = "<div title='" + label + '|' + '{{=T("Select to see a list of subdivisions.")}}' + "' id='gis_location_l{{=level}}_tooltip' class='tooltip'></div>";
      {{pass}}
        row1 = "<tr id='gis_location_l{{=level}}__row1'><td colspan='2'><label>" + label + '</label></td></tr>';
        row2 = "<tr id='gis_location_l{{=level}}__row'><td>" + widget + '</td><td>' + comment + '</td></tr>';
        $('#gis_location_name__row1').before(row1);
        $('#gis_location_name__row1').before(row2);
        l{{=level}} = true;
        // Apply the tooltip which was missed 1st time round
        $('#gis_location_l{{=level}}_tooltip').cluetip({activation: 'hover', sticky: false, splitTitle: '|'});
        // Apply the colorbox which was missed 1st time round
        $('#gis_l{{=level}}_colorbox').click(function(){
            _parent = $('#gis_location_l{{=int(level) - 1}}').val();
            url = this.href + '&parent=' + _parent;
            $.fn.colorbox({iframe:true, width:'99%', height:'99%', href:url, title:this.title});
            return false;
        });
    }
    if (preloaded) {
        options = empty_set;
        $('#gis_location_l{{=level}}').html(options);
    } else {
        // Load locations
        _parent = $('#gis_location_l{{=int(level) - 1}}').val();
        url = '{{=URL(r=request, c="gis", f="location", args="search.json", vars={"filter":"=", "field":"level", "value":"L" + level})}}&parent=' + _parent;
        load_locations = function(data, status){
            var options;
            var v = '';
            if (data.length == 0) {
                options = empty_set;
            } else {
                options = select_location;
                for (var i = 0; i < data.length; i++){
                    v = data[i].id;
                    options += '<option value="' +  data[i].id + '">' + data[i].name + '</option>';
                }
            }
            $('#gis_location_l{{=level}}').html(options);
            if (S3.gis.level == 'L5') {
                // Set to this location
                $('#gis_location_l{{=level}}').val(old_id);
            } else if (S3.gis.old_l5) {
                // Set to the value we pulled earlier
                $('#gis_location_l{{=level}}').val(S3.gis.old_l5);
            };
        };	
        $.getJSONS3(url, load_locations, false);
    }
    // When dropdown is selected
    $('#gis_location_l{{=level}}').change(function() {
        if (('' == $('#gis_location_lat').val() || '' == $('#gis_location_lon').val()) && ('' == $('#gis_location_addr_street').val()) ) {
            // Populate the real location_id field (unless a lat/lon/addr_street are present)
            var new_id = $(this).val();
            if ('' != new_id) {
                $('#' + location_id).val(new_id);
            }
            // Set the name box to this value
            $('#gis_location_name').val($('#gis_location_l{{=level}} :selected').text());
        }
        // Show the next level of hierarchy
        S3.gis.locations_l{{=int(level) + 1}}(false);
    });
  {{except:}}
  {{pass}}
    }

    // Name
    // @ToDo: Localise according to current user's preference
    label = '{{=T("Name")}}:<span class="req"> *</span>';
    widget = "<input id='gis_location_name' class='ac_input string' size='50' value='" + old_name + "' />";
    comment = "<div title='" + label + '|' + '{{=T("Enter a few characters of the name to select an existing Location or else simply type the name of the new Location.")}}' + "' id='gis_location_name_tooltip' class='tooltip'></div>";
    row1 = "<tr id='gis_location_name__row1'><td colspan='2'><label>" + label + '</label></td></tr>';
    row2 = "<tr id='gis_location_name__row'><td>" + widget + '</td><td>' + comment + '</td></tr>';
    $(location_id_row).before(row1);
    $(location_id_row).before(row2);
    // Apply the tooltip which was missed 1st time round
    $('#gis_location_name_tooltip').cluetip({activation: 'hover', sticky: false, splitTitle: '|'});

    // Autocomplete-enable the Name Input
    $('#gis_location_name').autocomplete({
        source: '{{=URL(r=request, c="gis", f="location", args="search.json", vars={"filter":"~", "field":"name", "exclude_field":"level", "exclude_value":"XX"})}}',
        minLength: 2,
        focus: function( event, ui ) {
            $( '#gis_location_name' ).val( ui.item.name );
            return false;
        },
        select: function( event, ui ) {
            $( '#gis_location_name' ).val( ui.item.name );
            $( '#{{=request.controller + "_" + request.function + "_location_id"}}' ).val( ui.item.id );
            
            // Also populate the Street Address & Lat/Lon
            S3.gis.uuid = ui.item.uuid;
            $('#gis_location_lat').val(ui.item.lat);
            $('#gis_location_lon').val(ui.item.lon);
            if (ui.item.addr_street != 'None') {
                $('#gis_location_addr_street').val(ui.item.addr_street);
            }
            // If a location in the admin hierarchy has been selected
            if ((ui.item.level != 'None') && (ui.item.level != '')){
                if (ui.item.level == 'L0') {
                    // Set the location (whether visible or not)
                    $('#gis_location_l0').val(ui.item.id);
                    // @ToDo Refresh other dropdowns
                    // (Not needed for PK)
                } else if (ui.item.level == 'L1') {
                    // Check if that dropdown is visible
                    if ($('#gis_location_l1__row').length == 0) {
                        // Open the dropdown
                        // @ToDo Check for bad side-effects of reusing these!
                        // Better to use arguments than flags!
                        S3.gis.level = 'L1';
                        old_id = ui.item.id;
                        S3.gis.locations_l1(false);
                        // Set the right entry
                        //s3_debug('opened dropdown', ui.item.id)
                        // Not working - async issue?
                        //$('#gis_location_l1').val(ui.item.id);
                        // @ToDo If we know country has changed, then reset that dropdown too
                        // (Not needed for PK)
                    } else {
                        // @ToDo Check that our location is in this dropdown!
                        // (Not needed for PK)
                        // Set the right entry
                        $('#gis_location_l1').val(ui.item.id);
                        // @ToDo If we know country has changed, then reset that dropdown too
                        // (Not needed for PK)
                        // Refresh L2-L5 dropdowns
                        $('#gis_location_l2').val('');
                        $('#gis_location_l3').val('');
                        $('#gis_location_l4').val('');
                        $('#gis_location_l5').val('');
                    }
                } else if (ui.item.level == 'L2') {
                    // Check if that dropdown is visible
                    if ($('#gis_location_l2__row').length == 0) {
                        // Open the dropdown
                        S3.gis.level = 'L2';
                        old_id = ui.item.id;
                        S3.gis.locations_l2(false);
                        // Set the right entry
                        //$('#gis_location_l2').val(ui.item.id);
                        if (ui.item.parent) {
                            var exists = $('#gis_location_l1').itemExists(ui.item.parent.toString());
                            if (exists) {
                                // Set the L1 to the Parent
                                $('#gis_location_l1').val(ui.item.parent);
                            } else {
                                // Reset the L1 dropdown
                                $('#gis_location_l1').val('');
                            }
                            // @ToDo Check the L0
                            // (Not needed for PK)
                        }
                    } else {
                        // Check that our location is in this dropdown!
                        var exists = $('#gis_location_l2').itemExists(ui.item.id.toString());
                        if (exists) {
                            // Set the right entry
                            $('#gis_location_l2').val(ui.item.id);
                            if (ui.item.parent) {
                                var exists = $('#gis_location_l1').itemExists(ui.item.parent.toString());
                                if (exists) {
                                    // Set the L1 to the Parent
                                    $('#gis_location_l1').val(ui.item.parent);
                                } else {
                                    // Reset the L1 dropdown
                                    $('#gis_location_l1').val('');
                                }
                                // @ToDo Check the L0
                                // (Not needed for PK)
                            }
                            // Refresh L3-L5 dropdowns
                            $('#gis_location_l3').val('');
                            $('#gis_location_l4').val('');
                            $('#gis_location_l5').val('');
                        } else {
                            // @ToDo Reload this Dropdown
                        }
                    }
                } else if (ui.item.level == 'L3') {
                    // Check if that dropdown is visible
                    if ($('#gis_location_l3__row').length == 0) {
                        // Open the dropdown
                        S3.gis.level = 'L3';
                        old_id = ui.item.id;
                        S3.gis.locations_l3(false);
                        // Set the right entry
                        //$('#gis_location_l3').val(ui.item.id);
                        if (ui.item.parent) {
                            var exists = $('#gis_location_l2').itemExists(ui.item.parent.toString());
                            if (exists) {
                                // Set the L2 to the Parent
                                $('#gis_location_l2').val(ui.item.parent);
                            } else {
                                // Reset the L2 dropdown
                                $('#gis_location_l2').val('');
                            }
                            // @ToDo Check the L1
                            // @ToDo Check the L0 (not needed for PK)
                        }
                    } else {
                        // Check that our location is in this dropdown!
                        var exists = $('#gis_location_l3').itemExists(ui.item.id.toString());
                        if (exists) {
                            // Set the right entry
                            $('#gis_location_l3').val(ui.item.id);
                            if (ui.item.parent) {
                                var exists = $('#gis_location_l2').itemExists(ui.item.parent.toString());
                                if (exists) {
                                    // Set the L2 to the Parent
                                    $('#gis_location_l2').val(ui.item.parent);
                                } else {
                                    // Reset the L2 dropdown
                                    $('#gis_location_l2').val('');
                                }
                                // @ToDo Check the L1
                                // @ToDo Check the L0 (not needed for PK)
                            }
                            // Refresh L4-L5 dropdowns
                            $('#gis_location_l4').val('');
                            $('#gis_location_l5').val('');
                        } else {
                            // @ToDo Reload this Dropdown
                        }
                    }
                } else if (ui.item.level == 'L4') {
                    // Check if that dropdown is visible
                    if ($('#gis_location_l4__row').length == 0) {
                        // Open the dropdown
                        S3.gis.level = 'L4';
                        old_id = ui.item.id;
                        S3.gis.locations_l4(false);
                        // Set the right entry
                        //$('#gis_location_l4').val(ui.item.id);
                        if (ui.item.parent) {
                            var exists = $('#gis_location_l3').itemExists(ui.item.parent.toString());
                            if (exists) {
                                // Set the L3 to the Parent
                                $('#gis_location_l3').val(ui.item.parent);
                            } else {
                                // Reset the L3 dropdown
                                $('#gis_location_l3').val('');
                            }
                            // @ToDo Check the L2
                            // @ToDo Check the L1
                            // @ToDo Check the L0 (not needed for PK)
                        }
                    } else {
                        // Check that our location is in this dropdown!
                        var exists = $('#gis_location_l4').itemExists(ui.item.id.toString());
                        if (exists) {
                            // Set the right entry
                            $('#gis_location_l4').val(ui.item.id);
                            if (ui.item.parent) {
                                var exists = $('#gis_location_l3').itemExists(ui.item.parent.toString());
                                if (exists) {
                                    // Set the L3 to the Parent
                                    $('#gis_location_l3').val(ui.item.parent);
                                } else {
                                    // Reset the L3 dropdown
                                    $('#gis_location_l3').val('');
                                }
                                // @ToDo Check the L2
                                // @ToDo Check the L1
                                // @ToDo Check the L0 (not needed for PK)
                            }
                            // Refresh L5 dropdown
                            $('#gis_location_l5').val('');
                        } else {
                            // @ToDo Reload this Dropdown
                        }
                    }
                } else if (ui.item.level == 'L5') {
                    // Check if that dropdown is visible
                    if ($('#gis_location_l5__row').length == 0) {
                        // Open the dropdown
                        S3.gis.level = 'L5';
                        old_id = ui.item.id;
                        S3.gis.locations_l5(false);
                        // Set the right entry
                        //$('#gis_location_l5').val(ui.item.id);
                        // @ToDo Ensure that all dropdowns above it are now visible
                        // @ToDo If we have parent ui.item, set those too
                    } else {
                        // Check that our location is in this dropdown!
                        var exists = $('#gis_location_l5').itemExists(ui.item.id.toString());
                        if (exists) {
                            // Set the right entry
                            $('#gis_location_l5').val(ui.item.id);
                            if (ui.item.parent) {
                                var exists = $('#gis_location_l4').itemExists(ui.item.parent.toString());
                                if (exists) {
                                    // Set the L4 to the Parent
                                    $('#gis_location_l4').val(ui.item.parent);
                                } else {
                                    // Reset the L4 dropdown
                                    $('#gis_location_l4').val('');
                                }
                                // @ToDo Check the L3
                                // @ToDo Check the L2
                                // @ToDo Check the L1
                                // @ToDo Check the L0 (not needed for PK)
                            }
                        } else {
                            // @ToDo Reload this Dropdown
                        }
                    }
                }
                // Clear the Name box, so that it's obviously free for a future sub-location
                $('#gis_location_name').val('');
            }
            
            return false;
        }
    })
    .data( 'autocomplete' )._renderItem = function( ul, item ) {
        var name = item.name;
        {{try:}}
        {{test = _gis.location_hierarchy["L1"]}}
        if (item.level == 'L1') {
            name += ' ({{=_gis.location_hierarchy["L1"]}})';
        {{try:}}
        {{test = _gis.location_hierarchy["L2"]}}
        } else if (item.level == 'L2') {
            name += ' ({{=_gis.location_hierarchy["L2"]}})';
        {{except:}}
        {{pass}}
        {{try:}}
        {{test = _gis.location_hierarchy["L3"]}}
        } else if (item.level == 'L3') {
            name += ' ({{=_gis.location_hierarchy["L3"]}})';
        {{except:}}
        {{pass}}
        {{try:}}
        {{test = _gis.location_hierarchy["L4"]}}
        } else if (item.level == 'L4') {
            name += ' ({{=_gis.location_hierarchy["L4"]}})';
        {{except:}}
        {{pass}}
        {{try:}}
        {{test = _gis.location_hierarchy["L5"]}}
        } else if (item.level == 'L5') {
            name += ' ({{=_gis.location_hierarchy["L5"]}})';
        {{except:}}
        {{pass}}
        }
        {{except:}}
        {{pass}}
        return $( '<li></li>' )
            .data( 'item.autocomplete', item )
            .append( '<a>' + name + '</a>' )
            .appendTo( ul );
    };
    $('#gis_location_name').change(function() {
        // If a new name is typed into the field, then we want to create a new Location, not update an existing one.
        $('#' + location_id).val('');
        S3.gis.uuid = '';
    });
    
    // Street Address
    label = '{{=db.gis_location.addr_street.label}}:';
    widget = "<textarea id='gis_location_addr_street' class='text' rows='5' cols='46'>" + old_addr_street + '</textarea>';
    comment = "<div title='" + label + '|' + "{{=T("This can either be the postal address or a simpler description (such as `Next to the Fuel Station`).")}}" + "' id='gis_location_add_street_tooltip' class='tooltip'></div>";
    row1 = "<tr id='gis_location_addr_street__row1'><td colspan='2'><label>" + label + '</label></td></tr>';
    row2 = "<tr id='gis_location_addr_street__row'><td>" + widget + '</td><td>' + comment + '</td></tr>';
    $(location_id_row).before(row1);
    $(location_id_row).before(row2);
    // Apply the tooltip which was missed 1st time round
    $('#gis_location_add_street_tooltip').cluetip({activation: 'hover', sticky: false, splitTitle: '|'});
    
    // GeoCoder widget
    widget = "<a id='geocoder-results-button' href='#'>{{=T("Geocoder Search")}}</a> ({{=T("Type an address above and use the geocoder to complete it.")}})";
    row2 = "<tr id='gis_location_geocoder__row'><td>" + widget + '</td><td></td></tr>';
    // Enable when ready
    $(location_id_row).before(row2);

    function geoCoderResultsHandler(selectedAddress) {
        //s3_debug('Selected place: ', selectedAddress);
        var street_addr = selectedAddress.AddressDetails.Country.
            AdministrativeArea.SubAdministrativeArea.Locality.
            Thoroughfare.ThoroughfareName;
        var zipcode = selectedAddress.AddressDetails.Country.
            AdministrativeArea.SubAdministrativeArea.Locality.
            PostalCode.PostalCodeNumber;
        var country = selectedAddress.AddressDetails.Country.CountryName;
        if (zipcode) {
            street_addr += ' ' + zipcode;
        }
        //s3_debug('Geocoder selected country:', country);
        //s3_debug('Geocoder selected addr:', street_addr);
        $('#gis_location_lat').val(selectedAddress.Point.coordinates[0]);
        $('#gis_location_lon').val(selectedAddress.Point.coordinates[1]);
        $('#gis_location_addr_street').val(street_addr);
        $('#gis_location_l0').val(country);
    }

    var geoCodeButton = Ext.get('geocoder-results-button');
    geoCodeButton.on('click', function(){
        var addr_street = $('#gis_location_addr_street').val();
        var country = '';
        var province = '';
        // Unfortunately, adding in the country sometimes seems to pare down results too much.
        // Needs more work...
        if ($('#gis_location_l0').val()) {
            country = $('#gis_location_l0 :selected').text();
        }
        if ($('#gis_location_l1').val()) {
            province = $('#gis_location_l1 :selected').text();
        }
        var search_term = addr_street + ' ' + province + ' ' + country;
        //s3_debug('Searching geocoder with: ', search_term);
        if (!addr_street) {
            return;
        }
        $.getJSONS3(
            '{{=URL(r=request, c="gis", f="geocode")}}' + '?location=' + search_term,
            function(data) {
                //s3_debug('Geocoder results:', data);
                geocode_results_picker(data, geoCoderResultsHandler);
            },
            'false'
        );
    });


    // Call L0 after definition of L1-L5 (since it may need to recurse through them)
    S3.gis.locations_l0();
  {{if len(_gis.countries) == 1:}}
    // Country hard-coded, so display L1
    // (needs to be called after definition of both the function & the addr_street)
    S3.gis.locations_l1(false);
    if (S3.gis.level == 'L1') {
        // Set L1 to this value
        $('#gis_location_l1').val(old_id);
        // Show the next level of hierarchy
        S3.gis.locations_l2(false);
    } else if (old_parent) {
        // Get the details for the parents
        // Calling old_id is an extra level of hierarchy to lookup, however
        // we don't assume that an L2 is parented to L1 - might skip a level!
        url = '{{=URL(r=request, c="gis", f="location")}}' + '/' + old_id + '/parents.json';
        $.getJSON(url, function(data) {
            //showStatus('{{=T("Looking up Parents")}}');
            // Parse the new location
            S3.gis.old_l0 = data['L0'];
            S3.gis.old_l1 = data['L1'];
            S3.gis.old_l2 = data['L2'];
            S3.gis.old_l3 = data['L3'];
            S3.gis.old_l4 = data['L4'];
            S3.gis.old_l5 = data['L5'];
            // Set to this value
            $('#gis_location_l1').val(S3.gis.old_l1);
            // Show the next level of hierarchy
            S3.gis.locations_l2(false);
        });
    }
  {{else:}}
  {{pass}}

  {{if _gis.map_selector:}}
    // Map-based selector
    label = '';
    widget = "<a id='openMap' href='#'>{{=T("Open Map")}}</a> ({{=T("can use this to identify the Location")}})";
    row1 = "<tr id='gis_location_map__row1'><td colspan='2'><label>" + label + '</label></td></tr>';
    row2 = "<tr id='gis_location_map__row'><td>" + widget + '</td><td></td></tr>';
    $(location_id_row).before(row1);
    $(location_id_row).before(row2);
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
    row1 = "<tr id='gis_location_lat__row'><td colspan='2'><label>" + label + '</label></td></tr>';
    row2 = "<tr id='gis_location_lat__row'><td>" + widget + '</td><td>' + comment + '</td></tr>';
    $(location_id_row).before(row1);
    $(location_id_row).before(row2);
    // Apply the tooltip which was missed 1st time round
    $('#gis_location_lat_tooltip').cluetip({activation: 'hover', sticky: false, splitTitle: '|'});
    
    label = '{{=db.gis_location.lon.label}}:';
    widget = "<input id='gis_location_lon' value='" + old_lon + "' />";
    comment = '{{=db.gis_location.lon.comment}}';
    row1 = "<tr id='gis_location_lon__row'><td colspan='2'><label>" + label + '</label></td></tr>';
    row2 = "<tr id='gis_location_lon__row'><td>" + widget + '</td><td>' + comment + '</td></tr>';
    $(location_id_row).before(row1);
    $(location_id_row).before(row2);
    
    // Section delimiter
    widget = '------------------------------------------------------------------------------------------------------------------------'
    row1 = "<tr id='gis_location_end__row'><td colspan='2' align='left'>" + widget + '</td></tr>';
    $(location_id_row).after(row1);

        
    // Over-ride the Form's Save Button
    $('form').submit(function() {
        // Save the Location
        // Read the values
        var lat = $('#gis_location_lat').val();
        var lon = $('#gis_location_lon').val();
        var addr_street = $('#gis_location_addr_street').val();
        // Use the Location name, if-defined
        var name = $('#gis_location_name').val();
        // Only save the Location if we have data, otherwise assume that we should just point to an existing record in Lx hierarchy
        if (('' == lat || '' == lon) && ('' == addr_street) && ('' == name)) {
            return true;
        }
        if (undefined == name || '' == name) {
            // Use the Resource name, if-defined
            name = $('#{{=request.controller + "_" + request.function + "_name"}}').val();
            if (undefined == name || '' == name) {
                // Define our own name
                name = '{{=request.controller + "_" + request.function}}' + Math.floor(Math.random()*1001);
            }
        }
        _parent = $('#gis_location_l5').val();
        if (undefined == _parent || '' == _parent){
            _parent = $('#gis_location_l4').val();
            if (undefined == _parent || '' == _parent){
                _parent = $('#gis_location_l3').val();
                if (undefined == _parent || '' == _parent){
                    _parent = $('#gis_location_l2').val();
                    if (undefined == _parent || '' == _parent){
                        _parent = $('#gis_location_l1').val();
                        if (undefined == _parent || '' == _parent){
                            _parent = $('#gis_location_l0').val();
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
        // Allow the Form's save to continue
        return true;
    });
});
s3_tb_cleanup = function(level){
    // A new location has been created in a Thickbox Popup
    // Which Level?
    var selector = $('#gis_location_' + level.toLowerCase());
    // Need to repeat here as the previous definition isn't in-scope
    var select_location = '<option value="" selected>' + '{{=T("Select a location")}}' + '...</option>';
    // Refresh this dropdown so that the new entry is visible
    url = '{{=URL(r=request, c="gis", f="location", args="search.json", vars={"filter":"=", "field":"level"})}}' + '&value=' + level;
    load_locations = function(data, status){
        var options;
        var v = '';
        if (data.length == 0) {
            options = empty_set;
        } else {
            options = select_location;
            for (var i = 0; i < data.length; i++){
                v = data[i].id;
                options += '<option value="' +  data[i].id + '">' + data[i].name + '</option>';
            }
        }
        selector.html(options);
        // Set the dropdown to the newly-created value (one with highest value)
        selector.val(v);
        // Show the next level of hierarchy
        var new_level = (level.substr(1) * 1) + 1
        // We know that there won't be any child locations since we just created this location!
        S3.gis['locations_l' + new_level](true);
    };	
    $.getJSONS3(url, load_locations, false);
}
//]]></script>

{{try:}}
{{=XML(_map)}}
{{except:}}
{{pass}}

{{include "gis/convert_gps.html"}}
{{include "gis/geocoder_results_popup.html"}}

{{pass}}
