function cmparr(arr1,arr2)
{
	if(arr1.length!=arr2.length)
	{
		return false;
	}
	var check=0;
	for(i=0;i<arr1.length;i++)
		if(arr1[i]===arr2[i])
			check++;
	if(check==arr1.length)
		return true;
	else
		return false;
}

function view4(header,table,numcol,grid_data)
{
    var loc="recvdata";
    var budget_kits=[
	['code','Code'],
	['description','Description'],
	['total_unit_cost','Total unit cost'],
	['total_monthly_cost','Total monthly cost'],
	['total_minute_cost','Total minute cost'],
	['total_megabyte_cost','Total megabyte cost']
	];
    var budget_item=[
    	['category_type','Budget Item'],
    	['code','Code'],
    	['description','Description'],
    	['cost_type','Cost type'],
    	['unit_cost','Unit Cost'],
    	['monthly_cost','Monthly Cost'],
    	['minute_cost','Minute Cost'],
    	['megabyte_cost','Megabyte Cost'],
    	['comments','Comments']
    	];
    var budget_kit_item=[
    	['kit_id','Kit ID'],
    	['item_id','Item ID'],
    	['quantity','Quantity']
    	];
    var or_office=[
    	['name','Name'],
	['organisation_id','ID'],
	['type','Type'],
	['admin','Admin'],
	['location_id','Location ID'],
	['parent','Parent'],
	['address','Address'],
	['postcode','Postcode'],
	['phone1','Phone 1'],
	['phone2','Phone 2'],
	['email','E-mail'],
	['fax','Fax'],
	['national_staff','National Staff'],
	['international_staff','International Staff'],
	['number_of_vehicles','Number of vehicles'],
	['vehicle_types','Vehicle types'],
	['equipment','Equipment'],
	['source_id','Source ID'],
	['comments','Comments']
	];

    var or_organisation=[
    	['name','Name'],
	['acronym','Acronym'],
	['type','Type'],
	['sector_id','Sector ID'],
	['admin','Admin'],
	['country','Country'],
	['website','Website'],
	['twitter','Twitter'],
	['donation_phone','Donation Phone'],
	['comments','Comments']
	];
    var pr_person=[
    	['pr_pe_id','ID'],
    	['pr_pe_label','Label'],
	['missing','Missing'],
	['first_name','First name'],
	['middle_name','Middle name'],
	['last_name','Last name'],
	['preferred_name','Preferred name'],
	['local_name','Local Name'],
	['opt_pr_gender','Gender'],
	['opt_pr_age_group','Age group'],
	['email','E-mail'],
	['mobile_phone','Mobile Phone'],
	['date_of_birth','Date of Birth'],
	['opt_pr_nationality','Nationality'],
	['opt_pr_country','Country'],
	['opt_pr_religion','Religion'],
	['opt_pr_marital_status','Marital Status'],
	['occupation','Occupation'],
	['comment','Comment']
	];
    var cr_shelter=[
        ['name','Name'],
	['description','Description'],
	['admin','Admin'],
	['location_id','Location ID'],
	['person_id','Person ID'],
	['address','Address'],
	['capacity','Capacity'],
	['dwellings','Dwellings'],
	['persons_per_dwelling','Persons per dwelling'],
	['area','Area']
	];
    var store;
    if(table=='or_organization')
	    store=or_organization;
    if(table=='or_office')
	    store=or_office;
    if(table=='pr_person')
	    store=pr_person;
    if(table=='cr_shelter')
	    store=cr_shelter;
    if(table='budget_kits')
	    store=budget_kits;
    if(table=='budget_item')
	    store=budget_item;
    if(table=='budget_kit_item')
	    store=budget_kit_item;
    Ext.QuickTips.init();
    var i=0;
    var colnames=new Array(numcol);
    while(i<numcol)
    {
	    colnames[i]=header.get('column'+i);
	    i++;
    }
    i=0;
    var colobjs=new Array(numcol);
    while(i<numcol)
    {
	    colobjs[i]="{fieldLabel : \'"+colnames[i]+"\'}";
	    try{
		    colobjs[i]=Ext.util.JSON.decode(colobjs[i]);
	    }
	    catch(err){
		    Ext.Msg.alert("","Object decode error");
	    }
	    colobjs[i].name=colnames[i];
	    colobjs[i].store=store;
	    colobjs[i].allowBlank=false;
	    colobjs[i].blankText='You must select a column';
	    colobjs[i].emptyText='Select a column';
	    colobjs[i].editable=true;
	    colobjs[i]=new Ext.form.ComboBox(colobjs[i]);
	    i++;
    }
    var columnmap=new Ext.form.FormPanel({
	url: loc,
	method: 'POST',
        title: 'Map spreadsheet columns to database fields',
        renderTo: 'spreadsheet',
        frame: true,
	labelAlign: 'right',
        height : 300,
        items: colobjs,
	buttons:[
		{	text: 'Next',
			handler: function(){
					//build the sheet to be imported as 2d array
       				 /*	var row=0;
					grid_data.each(function(){
						row++;
					});*/
					var importsheet={}
				//	importsheet.rows=grid_data.getCount();
					importsheet.columns=numcol;
					importsheet.data=new Array();
					grid_data.each(function()
					{
				
						var i=0;
						var temp=new Array();
						while(i<numcol)
						{
							temp.push(this.get(('column'+i)));
							i++;
						}
						importsheet.data.push(temp);
					});
 					//extract column headers from the header row object
					var i=0;map_from_ss_to_field=[];
					while(i<numcol)
					{
						map_from_ss_to_field.push([i,colobjs[i].getName(),colobjs[i].getValue()]);
						i++;
					}
					var headrow=new Array();
					while(i<numcol)
					{
						headrow.push(header.get('column'+i));
						i++;
					}
					i=0;
					var header_row=0;
					//find location of header row
				//	while(i<importsheet.rows){
 						if(cmparr(importsheet.data[i],headrow))
						{
							header_row=i;
							break;
						}		
				//	}
				//	document.write(importsheet.rows);
				    columnmap.getForm().submit({
				    success: function(form,action){
				       Ext.Msg.alert('Success', 'It worked');
					    },
				    failure: function(form,action){
				       Ext.Msg.alert('Warning', action.result.msg);
    					}
    				});
    			}
    		}],
       buttonAlign: 'center'
	});
    /*
    	//build the sheet to be imported as 2d array
        var row=0;
	grid_data.each(function(){
			row++;
		});
	var importsheet={}
	importsheet.rows=row;
	importsheet.columns=numcol;
	importsheet.data=new Array();
	grid_data.each(function()
			{
			
				var i=0;
				var temp=new Array();
				while(i<numcol)
				{
					temp.push(this.get(('column'+i)));
					i++;
				}
				importsheet.data.push(temp);
			});
	Ext.Ajax.request({
			url :'recvdata',
			method: 'POST',
			success: function()
				{
					Ext.Msg.alert("","SUCCESS!!");
					},
			failure: function(){Ext.Msg.alert("","FAILURE!!");},
			scope: this,
			params : {
					spreadsheet : importsheet.data,
					col : numcol,
					row : row
					}
	});

	//extract column headers from the header row object
	var i=0;
	var headrow=new Array();
	while(i<numcol)
	{
		headrow.push(header.get('column'+i));
		i++;
	}
	i=0;
	var header_row=0;
	//find location of header row
	while(i<row){
 		if(cmparr(importsheet.data[i],headrow))
		{
			header_row=i;
			break;
		}
	}*/
}
