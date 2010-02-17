// user selects organization first
// the #dummy office select fills up with related offices
var load_offices = function()
  {
    theURL = '{{=URL(r=request, c='or', f='office', args='search.json', vars={'filter':'=', 'field':'organisation_id', 'value':''})}}' + 
                $("#or_contact_organisation_id").val();
    offices_ok = function(data, status){
	    if (data.length == 0)
		options = '<option value="">No offices registered for organisation</options>';
	    else {
		$("#or_contact_office_id").val(data[0].id);
		var options = '<option value="" selected>Select an office...</option>';
		for (var i = 0; i < data.length; i++) 
		    options += '<option value="' +  data[i].id + '">' + data[i].name + '</option>';
	    }
	    $('#dummy_office').html(options); 
	};	
    $.getJSONS3(theURL, offices_ok, 'offices by organisation');
  };
