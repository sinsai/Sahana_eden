function import_spreadsheet(table,header_row,importsheet,map_from_ss_to_field)
{
	var map=map_from_ss_to_field;
	var temp=table.split("_");
	var prefix=temp[0];
	var name=temp[1];
	var records={};
	var str="$_";
	str+=prefix+"_"+name;
	for(k in importsheet)
		document.write(k+'<br/>');
	document.write('<br/>'+importsheet.columns+'<br/>');
	var jsonss=new Array(); //the array which will have json objects of each row
	time=new Date();
	var modifydate=''+(time.getUTCFullYear()+"-"+time.getUTCMonth()+"-"+time.getUTCDate()+" "+time.getUTCHours()+":"+time.getUTCMinutes()+":"+time.getUTCSeconds());
	//making importable json object of the spreadsheet data
	for(var i=0;i<importsheet.rows;i++)
	{
		var rowobj="{ ";
		for(var j=0;j<importsheet.columns;j++)
		{
			var field="\""+map[j][2]+"\"";
			if(field!=''){
				if(map[j][2].substring(0,3)=="opt")
				{
					rowobj+=field+":";
					rowobj+="{\"@value\":\"1\"";
					rowobj+=",\"$\":\""+importsheet.data[i][j]+"\"}";
				}
				else
					rowobj+=field+" : \""+importsheet.data[i][j]+"\"";
				if(j!=importsheet.columns-1) 
					rowobj+=",";
			}
			
		}
		rowobj+=",\"@modified_on\":\"";
		rowobj+=modifydate;
		rowobj+=" \"}";
		try{
			rowobj=eval('('+rowobj+')');
		}
		catch(err)
		{
			alert("Error");
		}
		jsonss.push(rowobj);
	}
	var posturl="http://localhost:8000/newins/"+prefix+"/"+name+"/create.json";
	document.write(posturl);
	var send="{\""+str+"\":\"\"}";
 	send=eval('('+send+')');
	send.str=jsonss;	
	jQuery.post({
		type : 'POST',
		url : posturl,
		data : rowobj,
		success: function(data,textStatus,XmlHttpRequest)
			{
				document.write('<b>'+data.status+'</b>');
			}
		});
}
