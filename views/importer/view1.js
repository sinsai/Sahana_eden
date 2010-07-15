function doJSON(stringData) {
        try {
            var jsonData = Ext.util.JSON.decode(stringData);
            return jsonData;
            
        }
        catch (err) {
            Ext.MessageBox.alert('ERROR', 'Could not decode ' + stringData);
        }
            
    }
var json={};
var columnlist=[];



function view1(importsheet){
	Ext.BLANK_IMAGE_URL = '../../static/scripts/ext/resources/images/default/s.gif';
    
    var columnlist=new Array(importsheet.columns);
    for(var i=0;i< importsheet.columns ; i++)
    { 
            temp="column"+i;
//	    temp=eval('('+temp+')');
	    columnlist[i]=temp;
    }
    //columnlist[0]="id";
    //columnlist[0]=eval('('+columnlist[0]+')');
    /*var store=new Ext.data.JsonStore({		
    	 root: 'data',
	 idProperty:'id',
         fields : columnlist,
	 totalProperty : json.rows
    });
   store.loadData(json);*/
   //column model for the grid     
   var columns=(importsheet.columns);
   var column_model=new Array(columns);
   var action = new Ext.ux.grid.RowActions({
			 header:'Click to delete',
			keepSelection:true,
			actions:[{
				 
				 iconCls:'action-delete',
				 tooltip : 'delete'
			}]
		});

		// dummy action event handler - just outputs some arguments to console
		action.on({
			action:function(grid, record, action, row, col) {
				Ext.Msg.alert("Event:action","You wanna delete");
			}
		});

   var edit=new Array(importsheet.columns);
   //editor functions for each column 
   for(i=1;i< importsheet.columns+1 ; i++)
   {
       edit[i]=new Ext.form.TextField();
   }
   //makes column model objects
   for( i=1 ; i< importsheet.columns + 1; i++)
   {
       var obj={};
       obj.header="Column "+(i);
       obj.sortable=true;
       obj.dataIndex=columnlist[i-1];
       obj.editor=edit[i];
       column_model[i]=obj;
   }
    var new_row_string="{";
    //Add row numbers --> RowNumbers plugin in the beginning of col model
    var sm2 = new Ext.grid.CheckboxSelectionModel();
    column_model[0]=sm2;	//placing the checkboxes before the first column
    //column_model[0]=new Ext.grid.RowNumberer();
    column_model.push(action);
    importsheet.column_model=column_model;
    var sm1 = new Ext.grid.CellSelectionModel();
    //column_model.push(sm1);
    var row_model=Ext.data.Record.create(columnlist);
    //Configuring the grid
    var grid=new Ext.grid.EditorGridPanel({
       title: '<div align="center"><u>Edit</u> \u2794 Select header row \u2794 Select table \u2794 Map columns to fields<p>Edit the spreadsheet, make sure a row with column titles exists</p></div>',
       renderTo: 'spreadsheet',
       loadMask: true,
       //iconCls : 'icon-grid',
       viewConfig:
       {	
       		forceFit : true
	},
       height: 300,
       store: importsheet.datastore,
       columnLines: true,
       sm: sm2,  
       style : 'text-align:left;', 
       frame : true,
       columns: column_model,
       buttons: [ 			
       		  {text : 'Next',
       		  handler:
                            function()
                            {
			       	   importsheet.rows=grid.getStore().getCount();
			     	   //This function stores the grid
                                   var gridsave=new Array(grid.getStore().getCount());
                                   var i=0;
				  //importsheet.columns=json.columns;
                                    grid.getStore().each(function(record)						{
						   	gridsave[i++]=record.data}
							);
                                    grid.hide();
				   view2(importsheet);
                            }
                   }
                 ],
       buttonAlign: 'center',
       listeners: {
               afteredit: function(e){
                 //saves the value in a cell after edit
                 e.record.commit();
                 var temp=e.column;
                 json.data[e.row].temp=e.value;
              }
           
        },
        clicksToEdit: 2,
        stripeRows: true,
        tbar: [
			{text: 'Search',
       	         	   handler:
		   	     function()
				{
					Ext.Msg.prompt("Search","Enter search text",function(btn,text){
						if(btn=='ok')
						{
							var k=-1;
							for(var i=0;i<importsheet.columns;i++)
							{
								k=importsheet.datastore.find('column'+i,text,0,true,false);
								if(k!=-1)
									break;
							}
							if(k==(-1))
							{
								Ext.Msg.alert("Not found","Search string not in spreadsheet "+k);
							}
							else
							{
								Ext.Msg.alert("Found","First matching record is at "+(k+1));
								sm2.selectRow(k);								
							}
						}
					});
				}
			},'-',
							
			
            {
                 text: 'Add row',
		 iconCls : 'action-delete',
		 handler: function()
                 {
                         grid.getStore().insert(0,new row_model);
                         grid.startEditing(0,0);
                 }
            },'-',
            {
                text: 'Remove row',
                iconCls : 'remove', 
                handler: function() {
                    try{
                                  var selmod = grid.getSelectionModel();
                                  if (selmod.hasSelection()){
                                         Ext.Msg.show({
                                                   title: 'Remove',
                                                   buttons: Ext.MessageBox.YESNOCANCEL,
                                                   msg: 'Remove ?',
                                                   fn: function(btn){
                                                           if (btn == 'yes'){
                                                               grid.getStore().remove(grid.getSelectionModel().getSelections());
                                                               
                                                             }
                                                       }
                                             });
                                      }
                                 }
                      catch(err){
                              Ext.Msg.alert("Error","Cannot remove row!");
                              }
                      }
            },'-'
              
        ]
        });
    grid.show();
}

var importsheet={};
importsheet.datastore={};
var json={{=ss}};
Ext.onReady(function(){
        
	var columnlist=new Array(json.columns);
   	for(var i=0;i< json.columns ; i++)
    	{ 
       	    temp="column"+i;
//	    temp=eval('('+temp+')');
	    columnlist[i]=temp;
 	}
    	//columnlist[0]="id";
    	//columnlist[0]=eval('('+columnlist[0]+')');
    	var store=new Ext.data.JsonStore({		
    		 root: 'data',
		 idProperty:'id',
    		 fields : columnlist,
		 totalProperty : json.rows
	    });
   	store.loadData(json);
	importsheet.datastore=store;
	importsheet.columns=json.columns;
	view1(importsheet);//.datastore,importsheet.columns);
});
