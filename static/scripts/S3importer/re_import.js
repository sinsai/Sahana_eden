function error_color(val,metadata,record,row,col,store)
{
	var error = val.substring(0,9);
	console.log("",error);
	if( error == "*_error_*")
	{
		//record.set(col,val.substring(9));
		//record.commit();
		return '<font color="red">'+val.substring(9)+'</font>';
	}
	return val;
}

if(success)
{
	Ext.onReady(function(){
	Ext.Msg.alert("Success!","All records were successfully imported ");
	});
}

else
{

	Ext.onReady(function(){
	Ext.Msg.alert("","These records could not be imported. Please edit and import again.");
	var column_model = new Array(number_column);
	var store = new Ext.data.JsonStore({
		fields : fields,
		root : 'rows',
	});
	var data={};
	data['rows'] = invalid_rows;
	console.log(data);
	store.loadData(data);
	store.each(function(record)
		{
			console.log(record.get('occupation'));
		});
	for( i=0 ; i < number_column ; i++)
	{
		column_model[i] = {};
		column_model[i].header = fields[i];
		column_model[i].dataIndex = fields[i];
		column_model[i].editor = new Ext.form.TextField();
		column_model[i].renderer = error_color;
	}
	var re_import_grid = new Ext.grid.EditorGridPanel({
		title : "Edit invalid rows ",
		renderTo: 'spreadsheet',
		width : 'auto',
		height : 300,
		viewConfig:{
			forceFit : true
		},
		store : store,
		frame : true,
		columns : column_model,
		hidden : true,
		buttonAlign : 'center',
		listeners:
				{
					afteredit: function(e){
						e.record.commit();
					}
				},
		buttons :[
			{
				text : 'Import',
				handler: function()
				{
					var lm = new Ext.LoadMask(Ext.getBody(),{msg : 'Importing...'});
					lm.enable();
					lm.show();
					var send = {};
					send.spreadsheet = new Array();
					store.each(function()
					{
						var temp = new Array();
						var i = 0;
						while(i < number_column)
						{
							temp.push(this.get((map[i][2])));
							i++;
						}

						send.spreadsheet.push(temp);
						send.map = map;
						send.rows = rows
					});
					send.map = map;
					send.rows = rows;
					send.columns = number_column;
					send.resource = resource;
					var time= new Date();
					var modifydate = ''+(time.getUTCFullYear()+"-"+time.getUTCMonth()+"-"+time.getUTCDate()+" "+time.getUTCHours()+":"+time.getUTCMinutes()+":"+time.getUTCSeconds());
					send.modtime = modifydate;
					var posturl = "http://"+url+"/"+application+"/importer/import_spreadsheet";
					Ext.Ajax.request({
						url : posturl,
						method : 'POST',
						jsonData : send,
						success : function(r,o){
							lm.hide();
							Ext.Msg.Alert("","Import successful "+location.href);},
						failure : function(r,o){
							lm.hide();
							Ext.Msg.alert("","Import failed "+r.responseText);
							}
						});
					console.log(send);
					lm.hide();
				}
				}]

		});
	re_import_grid.show();
	//document.write(data);
	});
}
