Ext.onReady(function()
		{
			var string="https://www.google.com/accounts/AuthSubRequest?scope=http%3A%2F%2Fspreadsheets.google.com%2Ffeeds%2F&session=1&secure=0&next=http%3A%2F%2F"+loc+"%3A8000%2F"+app+"%2Fimporter%2Fspreadsheet.html";
			Ext.Msg.write(string);
			window.location=string;
			
			//URL for AuthSub authentication
			/*var authurl="https://www.google.com/accounts/AuthSubRequest?scope=http%3A%2F%2Fspreadsheets.google.com%2Ffeeds%2F&session=1&secure=0&next=http%3A%2F%2Flocalhost:8000/newins%2F"
;
		//var authurl="www.google.com";	
		Ext.Ajax.request({
			url : authurl,
			method : 'GET',
			success : function(response,o)
				 {
				 	var temp=response.status;//("Content-Type");
				 	for(k in response)
				 		//document.write(k+"<br/>");
				 	Ext.Msg.alert("",temp+" request was a success");
				 },
			failure : function(response,o)
				{
					document.write(response+" was a failure");
				}
			});*/
		});
