// user selects organization first
// the #dummy office select fills up with related offices
var load_offices = function()
  {
       theURL = '{{=URL(r=request, c='or', f='office', args='search.json', vars={'filter':'=', 'field':'organisation_id', 'value':''})}}' + 
                $("#or_contact_organisation_id").val();
       $.ajax({
	    url: theURL,
	    success: function(data, status, req) {
                    var options = ''; //'<option value="">select an office</option>'; 
                    var j = data; 
                    for (var i = 0; i < j.length; i++) {
                        options += '<option value="' +  j[i].id + '">' + 
                                  j[i].name + '</option>';
                        if (i == 0) {
                            $("#or_contact_office_id").val(j[i].id);
                        }
                    }; 
            $('#dummy_office').html(options); 

            },
	    dataType: 'json'});
  };
