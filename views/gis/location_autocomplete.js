    // Hide the real Input Fields
    $("#gis_location_parent__row").hide();
        
    // Add a Country dropdown selector with relevant countries
    var widget = "<select id='gis_location_l0'><option value='1'>Haiti</option><option value='2'>Santo Domingo</option></select>";
    var row = '<tr><td><label>Country: </label></td><td>' + widget + '</td><td></td></tr>';
    $("#gis_location_addr_street__row").before(row);
        
    // Add Autocomplete dummy rows
    widget = "<input id='gis_location_l1' style='display: none;'/><input id='dummy_l1' class='ac_input' size=50 />";
    row = '<tr><td><label>Region: </label></td><td>' + widget + '</td><td></td></tr>';
    $("#gis_location_addr_street__row").before(row);
    widget = "<input id='gis_location_l2' style='display: none;'/><input id='dummy_l2' class='ac_input' size=50 />";
    row = '<tr><td><label>Town: </label></td><td>' + widget + '</td><td></td></tr>';
    $("#gis_location_addr_street__row").before(row);
    widget = "<input id='gis_location_l3' style='display: none;'/><input id='dummy_l3' class='ac_input' size=50 />";
    row = '<tr><td><label>District: </label></td><td>' + widget + '</td><td></td></tr>';
    $("#gis_location_addr_street__row").before(row);
    
    // L1
    // Autocomplete-enable the Dummy Input
    $("#dummy_l1").autocomplete('{{=URL(r=request, c='gis', f='location', args='search.json', vars={'filter':'~', 'field':'name', 'extra_string':'L1'})}}', {
        extraParams: {
            // Read 'parent' field dynamically
            parent: function() { return $("#gis_location_l0").val(); }
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
            return row.name.substr(4);
		}
    });
    
    // Populate the real Input when the Dummy is selected
    $("#dummy_l1").result(function(event, data, formatted) {
        var newvalue = data.id;
        $("#gis_location_l1").val(newvalue);
    });
    
    // L2
    // Autocomplete-enable the Dummy Input
    $("#dummy_l2").autocomplete('{{=URL(r=request, c='gis', f='location', args='search.json', vars={'filter':'~', 'field':'name', 'extra_string':'L2'})}}', {
        extraParams: {
            // Read 'parent' field dynamically
            parent: function() { return $("#gis_location_l1").val(); }
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
            return row.name.substr(4);
		}
    });
    
    // Populate the real Input when the Dummy is selected
    $("#dummy_l2").result(function(event, data, formatted) {
        var newvalue = data.id;
        $("#gis_location_l2").val(newvalue);
    });

    // L3
    // Autocomplete-enable the Dummy Input
    $("#dummy_l3").autocomplete('{{=URL(r=request, c='gis', f='location', args='search.json', vars={'filter':'~', 'field':'name', 'extra_string':'L3'})}}', {
        extraParams: {
            // Read 'parent' field dynamically
            parent: function() { return $("#gis_location_l2").val(); }
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
            return row.name.substr(4);
		}
    });

    // Populate the real Input when the Dummy is selected
    $("#dummy_l3").result(function(event, data, formatted) {
        var newvalue = data.id;
        $("#gis_location_l3").val(newvalue);
        $("#gis_location_parent__row").val(newvalue);    
    });
