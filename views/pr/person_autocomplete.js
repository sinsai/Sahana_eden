    // Autocomplete-enable the Dummy Input
    $('#{{=dummy_input}}').autocomplete({
        source: '{{=URL(r=request, c="pr", f="person", args="search.json", vars={"filter":"~", "field":"first_name", "field2":"middle_name", "field3":"last_name"})}}',
        minLength: 2,
        focus: function( event, ui ) {
            var name = '';
            if (data[i].first_name != null) {
                name += ui.item.first_name + ' ';
            }
            if (data[i].middle_name != null) {
                name += ui.item.middle_name + ' ';
            }
            if (data[i].last_name != null) {
                name += ui.item.last_name;
            }
            $( '#{{=dummy_input}}' ).val( name );
            return false;
        },
        select: function( event, ui ) {
            var name = '';
            if (ui.item.first_name != null) {
                name += ui.item.first_name + ' ';
            }
            if (ui.item.middle_name != null) {
                name += ui.item.middle_name + ' ';
            }
            if (ui.item.last_name != null) {
                name += ui.item.last_name;
            }
            $( '#{{=dummy_input}}' ).val( name );
            $( '#{{=entity_id}}' ).val( ui.item.id );
            {{try:}}{{=post_process}}{{except:}}{{pass}}
            return false;
        }
    })
    .data( "autocomplete" )._renderItem = function( ul, item ) {
        var name = '';
        if (item.first_name != null) {
            name += item.first_name + ' ';
        }
        if (item.middle_name != null) {
            name += item.middle_name + ' ';
        }
        if (item.last_name != null) {
            name += item.last_name;
        }
        return $( "<li></li>" )
            .data( "item.autocomplete", item )
            .append( "<a>" + name + "</a>" )
            .appendTo( ul );
    };