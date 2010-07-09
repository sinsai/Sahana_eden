function import_spreadsheet(table,header_row,importsheet,map_from_ss_to_field)
{
	var map=map_from_ss_to_field;
	var temp=table.split("_");
	var prefix=temp[0];
	var name=temp[1];
	var str="$_";
	str+=prefix+"_"+name;
	document.write(str+"<br/>");
	var jsonss=new Array(); //the array which will have json objects of each row
	time=new Date();
	var modifydate=''+(time.getUTCFullYear()+"-"+time.getUTCMonth()+"-"+time.getUTCDate()+" "+time.getUTCHours()+":"+time.getUTCMinutes()+":"+time.getUTCSeconds());
	//making importable json object of the spreadsheet data
	for(var i=0;i<importsheet.rows;i++)
	{
		if(i==header_row)
			continue;
		var rowobj="{";
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
					rowobj+=field+":\""+importsheet.data[i][j]+"\"";
				if(j!=importsheet.columns-1) 
					rowobj+=",";
			}
			
		}
		rowobj+=",\"@modified_on\":\"";
		rowobj+=modifydate;
		rowobj+="\"}";
		//document.write("The row object is "+rowobj+"<br/>");
		try{
			rowobj=eval('('+rowobj+')');
		}
		catch(err)
		{
			document.write(rowobj+"<br/>");
		}
		jsonss.push(rowobj);
	}
	var posturl="http://localhost:8000/{{=request.application}}/"+prefix+"/"+name+"/create.json?id=None";
	document.write(rowobj);
	var sendobj="{\""+str+"\":"+jsonss+"}";
	document.write("<br/>The URL for post request->"+posturl+" and the sending status is ->");
	var send="{\""+str+"\":\"\"}";
 	send=eval('('+send+')');
	send[str]=jsonss;
	//send[str]=new Array();
	//send[str].push(rowobj);
	document.write(send[str]);	
	Ext.Ajax.request({
		url : 'http://localhost:8000/newins/importer/recvdata',
		jsonData: send,//send as body,
		method : 'POST',
		success : function(r,o)
			{
				document.write("Successfully sent "+r.status);
			},
		failure: function(r,o)
			{
				document.write("Sending failed<br/> "+r.status+'<br/>'+r.error);
			}
	});
}
