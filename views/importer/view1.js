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

/*
Ext.onReady(function(){

Ext.Ajax.request({
        url : '../static/test1.json' , 
        
        method: 'GET',
            success: function ( result, request ) { 
               
                json=doJSON(result.responseText);   
                maker(json);
                
     
        },
            failure: function ( result, request) { 
                Ext.MessageBox.alert('Failed', result.responseText); 
            } 
        });
	document.write(string);
	json=doJSON({{=ss}});
	try{
		var json=doJSON({{=ss}});
	}
	catch(err)
	{
		alert("Error");
	}
	var word={{=ss}};
	maker(json);
});
*/

function maker(json){
    
    var columnlist=new Array(json.columns);
    for(var i=0;i< json.columns ; i++)
    { 
            temp="column"+i;
//	    temp=eval('('+temp+')');
	    columnlist[i]=temp;
    }
    //columnlist[0]="id";
    //columnlist[0]=eval('('+columnlist[0]+')');
    var store=new Ext.data.JsonStore({		//Don't get JSON twice
    	 root: 'data',
	 idProperty:'id',
         fields : columnlist,
	 totalProperty : json.rows
    });
   store.loadData(json);
   //column model for the grid     
   var column_model=new Array(json.columns+1);
   var edit=new Array(json.columns);
   //editor functions for each column 
   for(i=1;i< json.columns+1 ; i++)
   {
       edit[i]=new Ext.form.TextField();
   }
   //makes column model objects
   for( i=1 ; i< json.columns+1 ; i++)
   {
       obj="{header:\"Column ";
       obj+=(i);
       obj+="\",";
       obj+="sortable : true,";
       obj+="dataIndex :";
       obj+=("\""+columnlist[i-1]+"\"} ");
       try{
       	   col=Ext.util.JSON.decode(obj);
           col.editor=edit[i];
           column_model[i]=col;
       }
       catch(err){
		Ext.Msg.alert("Error","Error decoding column model");   
       }
    
   }
    var new_row_string="{";
    for(i=0; i<json.columns; i++)
    {
        new_row_string+="column"+i+" : \"Edit this\"";
        if(i!=json.columns-1)
            new_row_string+=",";
    }
    new_row_string+="}";
    try
    {
        var new_row_object=eval("("+new_row_string+")");
    }
    catch(err)
    {
    }
    var sm2 = new Ext.grid.CheckboxSelectionModel();
    column_model[0]=sm2;	//placing the checkboxes before the first column
    var sm1 = new Ext.grid.CellSelectionModel();
    //column_model.push(sm1);
    var row_model=Ext.data.Record.create(columnlist);
    var ht=(json.rows)*20;
    //Configuring the grid
    var grid=new Ext.grid.EditorGridPanel({
       title: '<div align="center"><u>Edit</u> \u2794 Select header row \u2794 Select table \u2794 Map columns to fields</div>',
       renderTo: 'spreadsheet',
       loadMask: true,
       //height: 'auto',
       autoHeight: true,
     //  width: 'auto',
       store: store,
       columnLines: true,
       sm: sm2,  
       style : 'text-align:left;', 
       frame : true,
       columns: column_model,
       buttons: [{text : 'Next',handler:
                                       function()
                                       {
				       	   //This function stores the grid
                                           var gridsave=new Array(grid.getStore().getCount());
                                           var i=0;
                                           grid.getStore().each(function(record){gridsave[i++]=record.data});
                                           grid.hide();
                                           view2(store,column_model,grid.getStore().getCount(),json.columns);
                                           
                                           
                                           }}
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
            {
                 text: 'Add row',
                 icon : 'images/table_add.png',
		 cls : 'x-btn-text-icon',
		 handler: function()
                 {
                         grid.getStore().insert(0,new row_model);
                         grid.startEditing(0,0);
                 }
            },'-',
            {
                text: 'Remove row',
                
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
}

Ext.onReady(function(){
/*
Ext.Ajax.request({
        url : '../static/test1.json' , 
        
        method: 'GET',
            success: function ( result, request ) { 
               
                json=doJSON(result.responseText);   
                maker(json);
                
     
        },
            failure: function ( result, request) { 
                Ext.MessageBox.alert('Failed', result.responseText); 
            } 
        });
	document.write(string);
	json=doJSON({{=ss}});
	try{
		var json=doJSON({{=ss}});
	}
	catch(err)
	{
		alert("Error");
	}*/
	var json={{=ss}};
	maker(json);
});
