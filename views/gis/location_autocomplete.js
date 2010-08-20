    // Hide the real Input field
    $('#{{=location_id}}').hide();
    // Add a dummy field
    $('#{{=location_id}}').after("<input id='dummy_{{=location_id}}' class='ac_input' size=50 />");

    // Add Autocomplete dummy rows
    var widget, row;
    
  {{if len(response.s3.gis.countries) == 1:}}
    widget = "<input id='gis_location_l0' style='display: none;'/><input id='dummy_l0' class='ac_input' size=50 />";
    row = "<tr id='gis_location_l0__row'><td><label>{{=response.s3.gis.location_hierarchy["L0"]}}: </label></td><td>" + widget + '</td><td></td></tr>';
    $('#{{=location_id}}__row').before(row);
    // Country is hardcoded
    $('#gis_location_l0').val({{=response.s3.gis.countries[response.s3.countries[0]].id}});
    // Hide
    $('#gis_location_l0__row').hide();
  {{elif len(response.s3.gis.countries) > 1:}}
    // Country is limited, so dropdown
    widget = "<input id='gis_location_l0' style='display: none;'/><select id='dummy_l0'>";
    {{for country in response.s3.gis.countries:}}
    widget += "<option value='{{=response.s3.gis.countries[country].id}}'>{{=response.s3.gis.countries[country].name}}</option>";
    {{pass}}
    widget += '</select>';
    row = "<tr id='gis_location_l0__row'><td><label>{{=response.s3.gis.location_hierarchy["L0"]}}: </label></td><td>" + widget + '</td><td></td></tr>';
    $('#{{=location_id}}__row').before(row);
    // Set initial value
    $('#gis_location_l0').val({{=response.s3.gis.countries[response.s3.countries[0]].id}});
  {{else:}}
    // Country is autocomplete
    widget = "<input id='gis_location_l0' style='display: none;'/><input id='dummy_l0' class='ac_input' size=50 />";
    row = "<tr id='gis_location_l0__row'><td><label>{{=response.s3.gis.location_hierarchy["L0"]}}: </label></td><td>" + widget + '</td><td></td></tr>';
    $('#{{=location_id}}__row').before(row);
  {{pass}}
    widget = "<input id='gis_location_l1' style='display: none;'/><input id='dummy_l1' class='ac_input' size=50 />";
    row = '<tr><td><label>{{=response.s3.gis.location_hierarchy["L1"]}}: </label></td><td>' + widget + '</td><td></td></tr>';
    $('#{{=location_id}}__row').before(row);
    widget = "<input id='gis_location_l2' style='display: none;'/><input id='dummy_l2' class='ac_input' size=50 />";
    row = '<tr><td><label>{{=response.s3.gis.location_hierarchy["L2"]}}: </label></td><td>' + widget + '</td><td></td></tr>';
    $('#{{=location_id}}__row').before(row);
    widget = "<input id='gis_location_l3' style='display: none;'/><input id='dummy_l3' class='ac_input' size=50 />";
    row = '<tr><td><label>{{=response.s3.gis.location_hierarchy["L3"]}}: </label></td><td>' + widget + '</td><td></td></tr>';
    $('#{{=location_id}}__row').before(row);
    widget = "<input id='gis_location_l4' style='display: none;'/><input id='dummy_l4' class='ac_input' size=50 />";
    row = '<tr><td><label>{{=response.s3.gis.location_hierarchy["L4"]}}: </label></td><td>' + widget + '</td><td></td></tr>';
    $('#{{=location_id}}__row').before(row);
    
  {{if len(response.s3.gis.countries) == 1:}}
  {{elif len(response.s3.gis.countries) > 1:}}
    // L0
    // Populate the real Input when the Dummy is selected
    $('#dummy_l0').result(function(event, data, formatted) {
        var newvalue = data.id;
        $('#gis_location_l0').val(newvalue);
    });
  {{else:}}
    // L0
    // Autocomplete-enable the Dummy Input
    $('#dummy_l0').autocomplete('{{=URL(r=request, c="gis", f="location", args="search.json", vars={"filter":"~", "field":"name"})}}', {
        extraParams: {
            level: 'L0'
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
            return row.name;
		}
    });
    
    // Populate the real Input when the Dummy is selected
    $('#dummy_l0').result(function(event, data, formatted) {
        var newvalue = data.id;
        $('#gis_location_l0').val(newvalue);
    });
    {{pass}}

    // L1
    // Autocomplete-enable the Dummy Input
    $('#dummy_l1').autocomplete('{{=URL(r=request, c="gis", f="location", args="search.json", vars={"filter":"~", "field":"name"})}}', {
        extraParams: {
            level: 'L1',
            // Read 'parent' field dynamically
            parent: function() { return $('#gis_location_l0').val(); }
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
            return row.name;
		}
    });
    
    // Populate the real Input when the Dummy is selected
    $('#dummy_l1').result(function(event, data, formatted) {
        var newvalue = data.id;
        $('#gis_location_l1').val(newvalue);
    });
    
    // L2
    // Autocomplete-enable the Dummy Input
    $('#dummy_l2').autocomplete('{{=URL(r=request, c="gis", f="location", args="search.json", vars={"filter":"~", "field":"name"})}}', {
        extraParams: {
            level: 'L2',
            // Read 'parent' field dynamically
            parent: function() { return $('#gis_location_l1').val(); }
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
            return row.name;
		}
    });
    
    // Populate the real Input when the Dummy is selected
    $('#dummy_l2').result(function(event, data, formatted) {
        var newvalue = data.id;
        $('#gis_location_l2').val(newvalue);
    });

    // L3
    // Autocomplete-enable the Dummy Input
    $('#dummy_l3').autocomplete('{{=URL(r=request, c="gis", f="location", args="search.json", vars={"filter":"~", "field":"name"})}}', {
        extraParams: {
            level: 'L3',
            // Read 'parent' field dynamically
            parent: function() { return $('#gis_location_l2').val(); }
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
            return row.name;
		}
    });

    // Populate the real Input when the Dummy is selected
    $('#dummy_l3').result(function(event, data, formatted) {
        var newvalue = data.id;
        $('#gis_location_l3').val(newvalue);
    });

    // L4
    // Autocomplete-enable the Dummy Input
    $('#dummy_l4').autocomplete('{{=URL(r=request, c="gis", f="location", args="search.json", vars={"filter":"~", "field":"name"})}}', {
        extraParams: {
            level: 'L4',
            // Read 'parent' field dynamically
            parent: function() { return $('#gis_location_l3').val(); }
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
            return row.name;
		}
    });
    
    // Location
    // Autocomplete-enable the Dummy Input
    $('#dummy_{{=location_id}}').autocomplete('{{=URL(r=request, c="gis", f="location", args="search.json", vars={"filter":"~", "field":"name"})}}', {
        extraParams: {
            // Read 'parent' field dynamically
            // Allow Location to search freely as we don't want to restrict to a specific level
            //parent: function() { return $('#gis_location_l4').val(); }
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
            return row.name;
		}
    });

    // Populate the real Input when the Dummy is selected
    $('#dummy_{{=location_id}}').result(function(event, data, formatted) {
        var newvalue = data.id;
        $('#{{=location_id}}').val(newvalue);
    });
