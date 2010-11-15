    // Autocomplete-enable the Dummy Input
    $('#{{=dummy_input}}').autocomplete({
        source: '{{=URL(r=request, c="cr", f="shelter", args="search.json", vars={"filter":"~", "field":"name"})}}',
        minLength: 2,
        focus: function( event, ui ) {
            $( '#{{=dummy_input}}' ).val( ui.item.name );
            return false;
        },
        select: function( event, ui ) {
            $( '#{{=dummy_input}}' ).val( ui.item.name );
            $( '#{{=entity_id}}' ).val( ui.item.id );
            return false;
        }
    })
    .data( "autocomplete" )._renderItem = function( ul, item ) {
        return $( "<li></li>" )
            .data( "item.autocomplete", item )
            .append( "<a>" + item.name + "</a>" )
            .appendTo( ul );
    };