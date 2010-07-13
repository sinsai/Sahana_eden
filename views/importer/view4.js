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

function alertmessage4()
{
	$(document).ready(function()
	{
		$("#message3").hide();
		$("#message4").addClass('confirmation');
		$("#message4").show('slow');
	});
}

function view4(importsheet)//header,table,numcol,grid_data)
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
    var org_office=[
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

    var org_organisation=[
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
    var store='';
    if(importsheet.table=='org_organisation')
	    store=org_organisation;
    if(importsheet.table=='org_office')
	    	store=org_office;
    if(importsheet.table=='pr_person')
	    store=pr_person;
    if(importsheet.table=='cr_shelter')
	    store=cr_shelter;
    if(importsheet.table=='budget_kits')
	    store=budget_kits;
    if(importsheet.table=='budget_item')
	    store=budget_item;
    if(importsheet.table=='budget_kit_item')
	    store=budget_kit_item;
    Ext.QuickTips.init();
    var i=0;
    var colnames=new Array(importsheet.columns);
    while(i<importsheet.columns)
    {
	    //colnames[i]=header.get('column'+i);
	    colnames[i]=importsheet.headerobject.get('column'+i);
	    i++;
    }
    i=0;
    var colobjs=new Array(importsheet.columns);
    while(i<importsheet.columns)
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
	    colobjs[i].blankText='You must select a field';
	    colobjs[i].emptyText='Select a field';
	    colobjs[i].editable=false;
	    colobjs[i].triggerAction='all';
	    colobjs[i].typeAhead=true;
	    colobjs[i]=new Ext.form.ComboBox(colobjs[i]);
	    i++;
    }
    //document.write(importsheet.datastore.json);
    var columnmap=new Ext.form.FormPanel({
	url: loc,
	method: 'POST',
	title: 'Edit spreadsheet \u2794 Select header row \u2794 Select table \u2794 <u>Map columns to fields</u>',
        renderTo: 'spreadsheet',
        frame: true,
	labelAlign: 'right',
        height : 'auto',
        items: colobjs,
	buttons:[
		{
			text: 'Back',
			handler:
				function(){
						columnmap.hide();
						view3(importsheet);
					}
		},
		{	text: 'Import',
			handler: function(){
					importsheet.rows=importsheet.datastore.getCount();
					importsheet.data=new Array();
					//Function which converts the spreadsheet to a list of lists
					importsheet.datastore.each(function()
					{
				
						var i=0;
						var temp=new Array();
						while(i<importsheet.columns)
						{
							temp.push(this.get(('column'+i)));
							i++;
						}
						importsheet.data.push(temp);
					});

 					//extract column headers from the header row object
					var i=0;
					map_from_ss_to_field=[];
					while(i<importsheet.columns)
					{
						if(colobjs[i].getValue()=='')
						{
							Ext.Msg.alert("Error","Map all columns");
							break;
						}
						map_from_ss_to_field.push([i,colobjs[i].getName(),colobjs[i].getValue()]);
						i++;
					}
					importsheet.map=map_from_ss_to_field;
					var headrow=new Array();
					i=0;
					while(i<importsheet.columns)
					{
						headrow.push(importsheet.headerobject.get('column'+i));
						i++;
					}
					importsheet.header_row_labels=headrow;
					i=0;
					/*var jsonObj=[];
					for (var i=0;i<store.getCount().i++) {
						jsonObj.push(store.getAt(i).data);
					}*/
					var header_row=0;
					//find location of header row
					while(i<importsheet.rows){
 						if(cmparr(importsheet.data[i],importsheet.header_row_labels))
						{
							header_row=i;
							importsheet.header_row_index=i;
							break;
						}	
						i++;	
					}
					     var lm = new Ext.LoadMask(Ext.getBody(),{msg : 'Importing...'});
				     	 lm.enable();	     
					 lm.show();
					
					//Import function
					(function()
					      {
					      	var temp=importsheet.table.split("_");
						var prefix=temp[0];
						var name=temp[1];
						var str="$_";
						str+=prefix+"_"+name;
						var jsonss=new Array(); //the array which will have json objects of each row
						time=new Date();
						var modifydate=''+(time.getUTCFullYear()+"-"+time.getUTCMonth()+"-"+time.getUTCDate()+" "+time.getUTCHours()+":"+time.getUTCMinutes()+":"+time.getUTCSeconds());
	//making importable json object of the spreadsheet data
						for(var i=0;i<importsheet.rows;i++)
						{
							if(i==importsheet.header_row_index)
								continue;
							var rowobj="{";
							for(var j=0;j<importsheet.columns;j++)
							{
								var field="\""+importsheet.map[j][2]+"\"";
								//Ext.Msg.alert("",field);
								if(field!=''){
								if(importsheet.map[j][2].substring(0,3)=="opt")
								{
									rowobj+=field+":";
									rowobj+="{\"@value\":\"1\"";
									rowobj+=",\"$\":\""+importsheet.data[i][j]+"\"}";
								}
								else
									rowobj+=field+":\""+importsheet.data[i][j]+"\"";
								if(j!=importsheet.columns-1) 
									rowobj+=",";
								}		
			
							}
							rowobj+=",\"@modified_on\":\"";
							rowobj+=modifydate;
							rowobj+="\"}";
							//rowobj=eval('('+rowobj+')');
							rowobj=Ext.util.JSON.decode(rowobj);
							jsonss.push(rowobj);
						}
						var posturl="http://{{=request.env.http_host}}/{{=request.application}}/"+prefix+"/"+name+"/create.json?p_l="+jsonss.length;
						var send="{\""+str+"\":\"\"}";
					 	send=eval('('+send+')');
						send[str]=jsonss;
						Ext.Ajax.request({
							scope: this,
							url : posturl,
							jsonData: send,//send as body,
							method : 'POST',
							success : function(r,o)
							{
								lm.hide();
								Ext.Msg.alert("Success","Import successful!");
							},
							failure: function(r,o)
							{
								lm.hide();
								Ext.Msg.alert("Failure","Import Failed");
									document.write(r.responseText+"<br/>");
							}
							});}.defer(50,this));
	
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
