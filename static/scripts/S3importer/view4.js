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

function view4(importsheet)
{
    
    //Use Ext.Ajax.request here to fetch data about tables and resources from the server here, use callback config to process it, must put a mask here
    //This view must be refactored keeping in mind the import of multiple resources and multiple tables, it will have a multiselect of tables and a dropdown or resource
    //Remove hardcoded table data
    /*var budget_kits=[
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
    */
    var field_store = {};
    var num_resources = importsheet.final_resources.length;
    var i=0;
    while(i < num_resources)
    {
	    var resource = eval('('+importsheet.resource_fields[i]+')');
	    field_store[resource['@resource']] = [];
	    for(k in resource.field)
	    {
		    //console.log(resource.field[k]['@name']);
		    if(resource.field[k]['@writable'] == "True" && resource.field[k]['@name'] != "id")
			    field_store[resource['@resource']].push(resource.field[k]['@name']);
	    }
	    //console.log('Resource');
	    //console.log(field_store);
	    i++;
    }
    var store = importsheet.final_resources;
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
    var resource_combo=new Array(importsheet.columns);
    while(i < importsheet.columns)
    {
	    resource_combo[i] = {};
	    resource_combo[i].fieldLabel = colnames[i];
	    resource_combo[i].name=colnames[i]+'_resource';
	    resource_combo[i].id=colnames[i]+'_resource';
	    resource_combo[i].store=importsheet.final_resources;
	    resource_combo[i].allowBlank=false;
	    resource_combo[i].blankText='You must select a resource';
	    resource_combo[i].emptyText='Select a resource';
	    resource_combo[i].editable=false;
	    resource_combo[i].triggerAction='all';
	    resource_combo[i].typeAhead=true;
	    resource_combo[i]= new Ext.form.ComboBox(resource_combo[i]);
	    i++;
    }
    i = 0;
    var fields_combo = new Array(importsheet.columns);
    while( i < importsheet.columns)
    {
	    fields_combo[i] = {};
	    fields_combo[i].fieldLabel = resource_combo[i];
	    fields_combo[i].name = colnames[i]+'_field';
	    fields_combo[i].id = colnames[i]+'_field';
	    fields_combo[i].store = ['Select resources'];
	    fields_combo[i].allowBlank = false;
	    fields_combo[i].blankText = 'You must select a field';
	    fields_combo[i].emptyText = 'Select field';
	    fields_combo[i].triggerAction = 'all';
	    fields_combo[i].typeAhead = true;
	    fields_combo[i] = new Ext.form.ComboBox(fields_combo[i]);
	    resource_combo.push(fields_combo[i]);
	    i++;
    }
    i = 0;
    console.log('Adding listener');
    while(i < importsheet.columns)
    {
	    resource_combo[i].on({ 'select' : {
			    			fn : function(combo,record,index)
			    		   	{
					   		Ext.Msg.alert("",combo.getValue());
							var name = "cool";
							var name = this.getId().replace('_resource','_field');
							console.log("in listener "+name);
							Ext.getCmp(name).getStore().removeAll(true);
							Ext.getCmp(name).getStore().loadData(field_store[combo.getValue()]);
						}
					    }
					});
	    i++;
    }
    var columnmap=new Ext.form.FormPanel({
	title: 'Edit spreadsheet \u2794 Select table \u2794 <u>Map columns to fields</u><br/>Select which columns go to which table fields',
        renderTo: 'spreadsheet',
        frame: true,
	labelAlign: 'right',
        height : 'auto',
        items: resource_combo,
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
					//Function which converts the spreadsheet to a list of lists, make a separate function
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
						if(resource_combo[i].getValue()=='')
						{
							Ext.Msg.alert("Error","Map all columns");
							break;
						}
						map_from_ss_to_field.push([i,resource_combo[i].getName(),resource_combo[i].getValue()]);
						i++;
					}
					importsheet.map=map_from_ss_to_field;
					var headrow=new Array();
					i=0;
					while(i < importsheet.columns)
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
				         var send={};
				 	 send.spreadsheet = importsheet.data;
					 send.map = importsheet.map;
					 send.header_row = importsheet.header_row_index;
					 send.rows=importsheet.rows;
					 send.columns=importsheet.columns;
					 var temp=importsheet.table.split("_");
					 var prefix=temp[0];
					 var name=temp[1];
					 var str="$_";
					 str+=prefix+"_"+name;
					 send.resource=str;
					 var time=new Date();
				         var modifydate=''+(time.getUTCFullYear()+"-"+time.getUTCMonth()+"-"+time.getUTCDate()+" "+time.getUTCHours()+":"+time.getUTCMinutes()+":"+time.getUTCSeconds());
	
					 send.modtime=modifydate;
					 var posturl = "http://"+url+"/"+application+"/importer/import_spreadsheet";
					 Ext.Ajax.request({
						url : posturl,
						method : 'POST',
						jsonData : send,
						callback : function(options,success,response)
							   {
							        lm.hide();
								var redirect = new Ext.LoadMask(Ext.getBody(),{msg : 'Redirecting to spreadsheet importer report...'});
								redirect.enable();
								redirect.show();
								var delay = new Ext.util.DelayedTask(function(){});
								delay.delay(2000);
								redirect.hide();

							   	/*if(success)
									Ext.Msg.alert("Success","All records have been imported to database");
								else
								{
								
									 Ext.Msg.show({title : "Re-import?",
											 msg : "Some records could not be imported, would you like to edit?",
											 buttons : Ext.Msg.YESNO,
											 fn : function(btn,text)		
							 				 {
							 					if(btn=="yes")
							 					window.location = "http://"+url+"/"+application+"/importer/re_import";		
							 	*/			 }
										});
							       	}
					 		

    			
    		}],
       buttonAlign: 'center',
       autoShow : true
	});
	
	columnmap.show(); 












				 //Import function
					      	/*var temp=importsheet.table.split("_");
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
						//	var rowobj={};
							for(var j=0;j<importsheet.columns;j++)
							{
								
								var field="\""+importsheet.map[j][2]+"\"";
								//Ext.Msg.alert("",field);
								if(field!=''){
								if(importsheet.map[j][2].substring(0,4)=="\"opt")
								{
									console.log(importsheet.map[j][2],"_");
									rowobj+=field+":";
									//rowobj[field]["@value"]=
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
							jsonss.push(rowobj);
						}
						//document.write(jsonss);
						/*
						var posturl="http://"+url+"/"+application+"/"+prefix+"/"+name+"/create.json?p_l="+jsonss.length;
						//var send="{\""+str+"\":\"\"}";
						var send={};
					 	//send=eval('('+send+')');
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
								importsheet.error_rows=new Array();
							 	try{
									var re_import = eval('('+r.responseText+')');
									re_import=re_import.tree
									var i=0;
									var j=0;
									var jlim=importsheet.datastore.getCount();
									importsheet.incorrect_rows=[];
									importsheet.correct_rows=[];
									while(j < jlim-1 )
									{
										if( j == importsheet.header_row_index)
											continue;
										i=0;
										while(i < importsheet.columns)
										{
											if(re_import[str][j][importsheet.map[i][2]].hasOwnProperty('@error'))
											{
												console.log("Error detected in row ",j+1,re_import[str][j]);
												importsheet.incorrect_rows.push(j);
												break;																				}
											i++;
										}
										j++;
									}
									//console.log("The erroneous records are ",importsheet.error_rows);
									//console.log("and the incorrect rows are ",importsheet.incorrect_rows);
									var num_errors=importsheet.incorrect_rows.length;
									var i=0;
									while(i < importsheet.incorrect_rows.length)
									{
										rowloc = importsheet.incorrect_rows[i];
										importsheet.incorrect_rows[i]=re_import[importsheet.incorrect_rows[i]];
										i++;
									}
									console.log(importsheet.incorrect_rows);
								}
								catch(err)
								{
									Ext.Msg.alert("","Error processing returned tree in row "+j+" column"+i);
									console.log("The erroneous records are ",importsheet.error_rows);
								}
								var field='\"'+importsheet.map[j][2]+'\"';
								while(i < importsheet.rows)
								{
									var record = re_import["tree"][str];
									document.write(record+'<br/>');
									i++;
								}
						
					*/
								/*			
								Ext.Msg.show({
										title : "Import failed",
										msg   : "Some records could not be imported. Would you like to edit the records which could not be imported?",
										buttons: Ext.Msg.YESNO,
										fn : function(btn)
											{
												if(btn=="no")
													return;
												else
												//call post import function
												{}
											}
										});
							}
							});
							}.defer(50,this));*/
	
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
