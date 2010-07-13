function alertmessage3()
{
	$(document).ready(function()
	{
		$("#message2").hide();
		$("#message3").addClass("confirmation");
		$("#message3").show('slow');
	});
}

function view3(importsheet)
{
    alertmessage3();
    var msForm = new Ext.form.FormPanel({
        title: 'Edit \u2794 Select header row \u2794 <u>Select table</u> \u2794 Map columns to fields',
        width: 'auto',
        height: 300,
        bodyStyle: 'padding:10px;',
        frame : true,
        delimiter: ',',
        renderTo: 'spreadsheet',
        items:[{
            xtype: 'multiselect',
            singleSelect: true,
            fieldLabel: 'Select table',
            name: 'table_selected',
            width: 500,
            height: 300,
            allowBlank:false,
            store: [['org_organisation','Organization Registry'],	//Server call to find component tables here
                    ['org_office', 'Organization Registry-Office'], 
                    ['pr_person', 'Person Registry'], 
                    ['cr_shelter', 'Shelter Registry'],  
                    ['budget_kits', 'Budgetting-Kits'],
                    ['budget_item', 'Budgetting-Items'],
                    ['budget_kit_item','Budgetting-Kits and items']],
            tbar:[{
                text: 'Clear',
                handler: function(){
                    msForm.getForm().findField('table_selected').reset();
                }
            }],
            ddReorder: true
        }],
        buttonAlign: 'center',
        buttons: [
        {
                text: 'Back',
                handler: function(){
                        msForm.hide();
                        view2(importsheet); 
                        }
               },
               {
            text: 'Next',
            handler: function()
            {
                var table=msForm.getForm().getValues(true);
                if(table=='table_selected=Multiple+rows+selected')
                    Ext.Msg.alert("Error","Select one table only");
                else
                    if(table=='table_selected=')
                        Ext.Msg.alert("Error","You must select a table");
                    else
                        {
                            table=table.substring(15);
                            importsheet.table=table;
			    msForm.hide();
                            view4(importsheet);
                        }
                     
                        }
                    }
              ]
    });
}
