    // This file is to be included for Single-Field autocompletes
    // (not suitable for pr_person which requires 3: first, middle & last)
    // Autocomplete-enable the Dummy Input
    $('#{{=dummy_input}}').autocomplete({
        source: '{{=URL(r=request, c=urlpath_c, f=urlpath_f, args="search.json", vars={"filter":"~", "field":urlvar_field})}}',
        minLength: 2,
        focus: function( event, ui ) {
            $( '#{{=dummy_input}}' ).val( ui.item.{{=urlvar_field}} );
            return false;
        },
        select: function( event, ui ) {
            $( '#{{=dummy_input}}' ).val( ui.item.{{=urlvar_field}} );
            $( '#{{=entity_id}}' ).val( ui.item.id );
            {{try:}}{{=post_process}}{{except:}}{{pass}}
            return false;
        }
    })
    .data( 'autocomplete' )._renderItem = function( ul, item ) {
        return $( '<li></li>' )
            .data( 'item.autocomplete', item )
            .append( '<a>' + item.{{=urlvar_field}} + '</a>' )
            .appendTo( ul );
    };
