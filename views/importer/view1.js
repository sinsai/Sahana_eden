function doJSON(stringData) {
        try {
            var jsonData = Ext.util.JSON.decode(stringData);
            //var jsonData= eval("("+stringData+")");
            return jsonData;
            
        }
        catch (err) {
            Ext.MessageBox.alert('ERROR', 'Could not decode ' + stringData);
        }
            
    }
var json={};
var columnlist=[];

Ext.onReady(function(){
Ext.Msg.alert("Welcome","Welcome to the spreadsheet importer<br/>At this step, you can modify the values extracted from your spreadsheet<br/><b>Be sure to add a row that has column headers if its not there already</b>");

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
});

function maker(json){
        
    
    columnlist=new Array(json.columns);
    for(var i=0;i< json.columns ; i++)
    { 
          
            columnlist[i]="column"+i;
            
          
    }
    var store=new Ext.data.Store({
        url : "../static/test1.json",
        reader : new Ext.data.JsonReader({root: "data",id:"id"},
         columnlist)
        });
        
   store.load();
   //column model for the grid     
   var column_model=new Array(json.columns+1);
   var edit=new Array(json.columns);
   //editor functions for each column that can be edited
   for(i=0;i< json.columns ; i++)
   {
       edit[i]=new Ext.form.TextField();
   }
   //makes column model objects
   for( i=0 ; i< json.columns ; i++)
   {
       obj="{header:\"Column ";
       obj+=(i+1);
       obj+="\",";
       obj+="sortable : true,";
       obj+="dataIndex :";
       obj+=("\""+columnlist[i]+"\", ");
       /*obj+="editor: ";
       obj+=edit[i];*/       
       obj+=" }";
       
       try{
       
       col=Ext.util.JSON.decode(obj);
       col.editor=edit[i];
       column_model[i]=col;
       //document.write('<br/>'+obj.editor);
       
       }
       catch(err){
           Ext.Msg.alert("Error","Input string cannot be parsed");
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
    column_model[json.columns]=sm2;
    var row_model=Ext.data.Record.create(columnlist);
    var grid=new Ext.grid.EditorGridPanel({
       title: 'Spreadsheet',
       renderTo: 'spreadsheet',
       height: 300,
       width: 'auto',
       store: store,
       columnLines: true,
       sm: sm2,   
       frame : true,
       columns: column_model,
       buttons: [{text : 'Next',handler:
                                       function()
                                       {
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
                 
                 e.record.commit();
                 var temp=e.column;
                 json.data[e.row].temp=e.value;
                 //Ext.Msg.alert("",json.data[e.row].temp);
              }
           
        },
        clicksToEdit: 2,
        stripeRows: true,
        tbar: [
            {
                 text: 'Add row',
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
