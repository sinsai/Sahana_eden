// reusable module - pop-up, autocomplete and post-processing
// author:  sunneach
// created: Feb 27 2010
// Auto_input {{=entity_id}}
{{if entity_id:}}
    // Hide the real Input Field
    $('#{{=entity_id}}').hide();
    {{dummy_input = "dummy_" + entity_id}}
    {{try:}}      
        {{default_value}}
    {{except:}}   
        {{default_value = None}}
    {{pass}}
    
    {{if default_value is None:}}
        {{default_value = ""}}
    {{pass}}

    $('#{{=entity_id}}').after("<input id='{{=dummy_input}}' class='ac_input' value='{{=default_value}}' size=50 />");
    {{include "autocomplete.js"}}

    // Populate the dummy Input at start (Update forms)
    var represent = $('#{{=entity_id}} > [selected]').html();
    $('#{{=dummy_input}}').val(represent);
    
    {{entity_id = None}}
    {{default_value = None}}
{{pass}}
