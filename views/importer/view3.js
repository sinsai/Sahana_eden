function view3(header,numcol,prevgrid)
{
    Ext.Msg.alert("Step 3","Please select a single table to which the spreadsheet has to be imported ");
    var msForm = new Ext.form.FormPanel({
        title: 'Select table',
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
            store: [['or_organisation','Organization Registry'],
                    ['or_office', 'Organization Registry-Office'], 
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
                        msForm.hide();prevgrid.show();
                        
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
                            msForm.hide();
                            view4(header,table,numcol,prevgrid);
                        }
                     
                        }
                    }
              ]
    });
}
