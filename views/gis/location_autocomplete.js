    // Hide the real Input Fields
    $('#gis_location_parent__row').hide();
        
    // Add Autocomplete dummy rows
    var widget, row;
    widget = "<input id='gis_location_l0' style='display: none;'/><input id='dummy_l0' class='ac_input' size=50 />";
    row = '<tr><td><label>{{=gis_location_hierarchy["L0"]}}: </label></td><td>' + widget + '</td><td></td></tr>';
    $('#gis_location_addr_street__row').before(row);
    widget = "<input id='gis_location_l1' style='display: none;'/><input id='dummy_l1' class='ac_input' size=50 />";
    row = '<tr><td><label>{{=gis_location_hierarchy["L1"]}}: </label></td><td>' + widget + '</td><td></td></tr>';
    $('#gis_location_addr_street__row').before(row);
    widget = "<input id='gis_location_l2' style='display: none;'/><input id='dummy_l2' class='ac_input' size=50 />";
    row = '<tr><td><label>{{=gis_location_hierarchy["L2"]}}: </label></td><td>' + widget + '</td><td></td></tr>';
    $('#gis_location_addr_street__row').before(row);
    widget = "<input id='gis_location_l3' style='display: none;'/><input id='dummy_l3' class='ac_input' size=50 />";
    row = '<tr><td><label>{{=gis_location_hierarchy["L3"]}}: </label></td><td>' + widget + '</td><td></td></tr>';
    $('#gis_location_addr_street__row').before(row);
    
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
        $('#gis_location_parent__row').val(newvalue);    
    });
