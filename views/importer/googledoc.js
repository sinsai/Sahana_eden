Ext.onReady(function()
		{
			var auth_button=new Ext.Button({
					text : 'Authenticate',
					renderTo : 'authenticate',
			handler : function(button,eventobj){

			window.location="https://www.google.com/accounts/AuthSubRequest?scope=http%3A%2F%2Fspreadsheets.google.com%2Ffeeds%2F&session=1&secure=0&next=http%3A%2F%2F{{=request.env.http_host}}%2F{{=request.application}}%2Fimporter%2Fgettoken";
			}
			});
		});
