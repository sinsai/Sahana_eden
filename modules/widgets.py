# -*- coding: utf-8 -*-
"""
    Custom widgets to extend Web2Py

    @author: Michael Howden (michael@aidiq.com)
    @date-created: 2010-03-17

"""

from gluon.sqlhtml import *
from shn_utils import *

# Custom widgets
# shnCheckboxesWidget --------------------------------------------------------    
class S3CheckboxesWidget(OptionsWidget):
    """
    @author: Michael Howden (michael@aidiq.com)

    generates a TABLE tag with <num_column> columns of INPUT checkboxes (multiple allowed)        

    help_lookup_table_name_field will display tooltip help

    :param db: int - 
    :param lookup_table_name: int - 
    :param lookup_field_name: int - 
    :param multple: int - 

    :param options: list - optional - 
    value,text pairs for the Checkboxs - 
    If options = None,  use options from self.requires.options(). 
    This arguement is useful for displaying a sub-set of the self.requires.options()    

    :param num_column: int - 

    :param help_lookup_field_name: string - optional - 

    :param help_footer: string - 

    """

    def __init__(self,
                 db,
                 lookup_table_name, 
                 lookup_field_name,
                 multiple = False,
                 options = None,
                 num_column = 1,                                         
                 help_lookup_field_name = None,
                 help_footer = None                 
                 ):

        self.db = db    
        self.lookup_table_name = lookup_table_name
        self.lookup_field_name =  lookup_field_name
        self.multiple = multiple

        self.num_column = num_column      

        self.help_lookup_field_name = help_lookup_field_name
        self.help_footer = help_footer
        self.requires = IS_NULL_OR(IS_IN_DB(db, 
                                   db[lookup_table_name].id, 
                                   "%(" + lookup_field_name + ")s", 
                                   multiple = multiple))

        if options:
            self.options = options
        else:
            if hasattr(self.requires, 'options'):
                self.options = self.requires.options()
            else:
                raise SyntaxError, 'widget cannot determine options of %s' % field  


    def widget( self,
                field, 
                value = None
                ):

        db = self.db

        values = shn_split_multi_value(value)

        attr = OptionsWidget._attributes(field, {})

        num_row  = len(self.options)/self.num_column
        # Ensure division  rounds up
        if len(self.options) % self.num_column > 0:
             num_row = num_row +1 

        table = TABLE(_id = str(field).replace('.',"_"))

        for i in range(0,num_row):
            table_row = TR()
            for j in range(0, self.num_column):
                #check that the index is still within self.options
                index = num_row*j + i
                if index < len(self.options):
                    input_options = {}
                    input_options = dict(requires = attr.get('requires',None),
                                         _value = self.options[index][0], 
                                         _type = "checkbox",
                                         _name = field.name,
                                         hideerror = True
                                        )
                    if self.options[index][0] in values:
                        input_options["value"] = "on"
                    #table_row.append(TD(INPUT(**input_options)))\

                    tip_attr = {}
                    help_text = ""
                    if self.help_lookup_field_name: 
                        help_text = str( P( shn_get_db_field_value(db=db,
                                                                   table = self.lookup_table_name,
                                                                   field = self.help_lookup_field_name, 
                                                                   look_up = self.options[index][0], 
                                                                   look_up_field = 'id')
                                          )
                                        )
                    if self.help_footer:
                        help_text = help_text + str(self.help_footer)
                    if help_text:
                        tip_attr = dict(_class = "s3_checkbox_label",
                                        #_title = self.options[index][1] + "|" + help_text
                                        _rel =  help_text 
                                        )

                    #table_row.append(TD(A(self.options[index][1],**option_attr )))
                    table_row.append(TD(INPUT(**input_options),
                                        SPAN(self.options[index][1], **tip_attr)
                                        )
                                    )
            table.append (table_row)
        if self.multiple:
            table.append(TR(I("(Multiple selections allowed)")))
        return table   

    def represent(self,
                  value):
        list = [shn_get_db_field_value(db = self.db,
                                       table = self.lookup_table_name,
                                       field = self.lookup_field_name, 
                                       look_up = id, 
                                       look_up_field = 'id')
                   for id in shn_split_multi_value(value) if id]
        if list and not None in list:
            return ", ".join(list)
        else:
            return None

class JSON(INPUT):
    """
    @author: Michael Howden (michael@aidiq.com)   

    :param json_table: Table - The table where the data in the JSON will be saved to

    Required for S3MultiSelectWidget JSON input
    :param link_field_name: A field in the json_table which will will be automatically po
    :param table_name: The table in which the Element appears
    existing_value: The existing values for 

    _name - If JSON inside S3MultiSelectWidget _name = None

    TODO:
    * Better error handling
    * Make this compatible with the Multi Rows widget -> this would include a command to delete AND have to set the record of the field at the end
    * Save multiple ids as X|X|X|X
    * have postprocessing to convert "id" -> "{'id':X}"
    * Why are JSON attributes being saved?
    * Use S3XRC
    """    
    def _validate(self):
        #must be post-processing - because it needs the id of the added record 
        name = self['_name']
        if name == None or name == '':
            return True
        name = str(name)

        json_str = self.request_vars.get(name, None)

        if json_str == "":
            #Don't do anything with a blank field
            value =  self["existing_value"]

        elif not "link_field_name" in self.attributes:
            value = self._process_json(json_str,
                                       self["existing_value"] )
        else:
            #If link_feild_name exists ((S3Multiselect, _process_json will require the record id
            #therefore, it must be called from the onaccept, after the record is created 
            value =  self["existing_value"]    

        if value == "":
            value = None

        self['value'] = self.vars[name] = value    

        return True

    def onaccept(self,
                 db,
                 link_field_value,
                 json_request):
        json_str = json_request.post_vars.get(self['_name'], None)
        if json_str:
            value = self._process_json(json_str,
                                       self["existing_value"],
                                       link_field_value = link_field_value,
                                       json_request = json_request )    
            update_dict = {self['_name']: value}
            db(db[self["table_name"]].id == link_field_value).update(**update_dict)


    def _process_json(self,
                      json_str,
                      existing_value = "",
                      link_field_value = None,
                      json_request = None
                      ):        

        json_table = self.attributes["json_table"]        
        db = json_table._db

        if existing_value:
            values = existing_value.split("|")
        else:
            values = []

        link_field_name = None
        if "link_field_name" in self.attributes:  
            link_field_name = self.attributes["link_field_name"]

        try:
            json_data = eval(json_str)
        except:
            self.errors[name] = "Autocomplete Data Error. Please Contact Administrator"
            return False

        #if there is only one JSON object, make it iterable
        if type(json_data).__name__ != "tuple":
            json_data = [json_data]
        for json_record in json_data:
            json_record = Storage(json_record)

            #insert value to link this record back to the record currently being saved
            if link_field_name:
                json_record[link_field_name] = link_field_value

            query = (json_table.deleted==False) 
            for field, value in json_record.iteritems():
                if type(value).__name__ == "dict":
                    #recurse through this JSON data
                    #TODO - This doesn't work with nested multiselect, unless we access it's existing value. 
                    #This could be done by doing the recurse AFTER the add... but then we would still need to get the variables out...
                    recurse_table_name = json_table[field].type[10:]
                    json_record[field] = value = JSON(json_table = db[recurse_table_name])._process_json(str(value))

                if field == "file":
                    f = json_request.post_vars[value] 

                    if hasattr(f,'file'):
                        (source_file, original_filename) = (f.file, f.filename)
                    elif isinstance(f, (str, unicode)):
                        ### do not know why this happens, it should not
                        (source_file, original_filename) = \
                            (cStringIO.StringIO(f), 'file.txt')
                    filename = db.drrpp_file.file.store(source_file, original_filename)

                    json_record[field] = value = filename

                #build query to test if this record is already in the DB
                #Weird: Query & bool OK; bool & Query NOT! 
                #if type(query).__name__ == "bool":
                #    query = (json_table[field] == value) & query
                #else:
                query = query & (json_table[field] == value)

            if "id" not in json_record:
                #ADD
                #Search for the value existing in the table already
                #TODO - why is query becoming a bool?!?!
                #if query:
                matching_row = db(query).select()
                #else:
                #    matching_row = []
                if len(matching_row) == 0:
                    # TODO - This should be done in S3XRC, or add some sort of validation
                    id  = json_table.insert(**json_record)
                else:
                    id = matching_row[0].id
                id = str(id)
                if id not in values:
                    values.append(id)

            else:
                #DELETE / UPDATE  
                id = json_record.id
                del json_record.id
                #json_table[id] = json_record
                if len(json_record) > 0:
                    db(json_table.id == id).update(**json_record)

                id = str(id)                
                if json_record.deleted == True and id in values:
                    values.remove(id)
                elif json_record.deleted == False:
                    values.append(id)

        return "|".join(values)

# -----------------------------------------------------------------------------
class S3MultiSelectWidget(FormWidget):
    """
    @author: Michael Howden (michael@aidiq.com)

    This widget will return a table which can have rows added or deleted (not currently editted).
    This widget can be added to a table using a XXXX_dummy field. This field will only store the ID of the record and serve as a placeholder.

    :param link_table_name: - string - the 
    :param link_field_name: - Field - 
    :param column_fields:  - list of strings - optional. The fields from the link_table whcih will be display as columns. 
    Default = All fields.    

    """
    def __init__ (self,
                  db,
                  link_table_name,                  
                  link_field_name, 
                  column_fields = None,
                  represent_fields = None,
                  represent_field_delim = "-",
                  represent_record_delim = ", "
                  ):
        """

        """
        self.db = db
        self.link_table_name = link_table_name
        self.link_field_name = link_field_name
        self.represent_field_delim = represent_field_delim
        self.represent_record_delim = represent_record_delim

        if column_fields:
             self.column_fields = column_fields 
        else:
            self.column_fields = [link_table_field.name for link_table_field in db[link_table_name] 
                                  if link_table_field.name != link_field_name and 
                                     link_table_field.name != "id" and 
                                     link_table_field.writable == True]  
        if represent_fields:
            self.represent_fields = represent_fields
        else:
            self.represent_fields = [self.column_fields[0]]

        column_fields_represent = {}
        for field in self.column_fields:
            column_fields_represent[field] = db[link_table_name][field].represent  
        self.column_fields_represent = column_fields_represent

    def widget(self,
               field, 
               value):
        """

        """

        db = self.db       
        link_field_name = self.link_field_name
        link_table_name = self.link_table_name
        link_table = db[link_table_name]
        column_fields = self.column_fields

        widget_id = str(field).replace(".","_")

        if type(value).__name__ == "str":
            if len(value) > 0:
                if value[0] == "{":
                    #This means that it didn't save properly - clear value to avoid error
                    value = ""

        input_json = JSON(_name = field.name,
                          _id = widget_id + "_json",
                          json_table = link_table,
                          table_name = str(field).split(".")[0],
                          link_field_name = link_field_name,
                          existing_value = value,                          
                          _style = "display:none;"
                          )

        self.onaccept = input_json.onaccept

        header_row = []
        input_row = []
        for column_field in column_fields:
            header_row.append(TD(B(link_table[column_field].label)))
            input_widget = link_table[column_field].widget 
            if not input_widget:
                if link_table[column_field].type.startswith("reference"):
                    input_widget = OptionsWidget.widget
                else:
                    input_widget = SQLFORM.widgets[link_table[column_field].type].widget
            input_element = input_widget(link_table[column_field],
                                         None, 
                                         _id = widget_id + "_" + column_field,
                                         _name = None)
            #insert the widget id in front of the element id
            input_element.__setitem__("_id", 
                                      widget_id + "_" + column_field # input_element.__getitem__("_id")
                                      )
            input_row.append(input_element)

        widget_rows = [TR(header_row)]

        #Get the current value to display rows for existing data.
        ids = shn_split_multi_value(value)

        #if  value and value <> "":
        #    if linked_table:
                #ids = [ row.id for row in db((link_field==value)&(link_table.deleted == False)).select()]
        #        ids =
        #    else:    
        #        if "|" in str(value):
        #            #multiple rows
        #            ids = value.split('|')
        #        else:
        #            #1 row
        #            ids = [int(value)]

        for id in ids:
            if id:
                row = db(link_table.id == id).select()
                if len(row) > 0:    #If is NOT true, it indicates that a error has occured
                    widget_rows.append(self._generate_row(widget_id, 
                                                           id, 
                                                           column_fields = column_fields, 
                                                           column_fields_represent = self.column_fields_represent,
                                                           row = row[0],
                                                           is_dummy_row = False)
                                        )



        input_row.append(TD(A("+", 
                              _id = widget_id + "_add", 
                              _class = "s3_multiselect_widget_add", 
                              _href = "javascript: void(0)"), 
                            _class = "s3_multiselect_widget_add_cell"))

        widget_rows += [ TR( _id = widget_id + "_input_row" ,
                         _class = "s3_multiselect_widget_input_row",  
                         *input_row)
                        ]

        dummy_row = self._generate_row(widget_id = widget_id, 
                                           id = "New", 
                                           column_fields = column_fields, 
                                           is_dummy_row = True)

        js_add_click_args = dict(NewRow = str(dummy_row),
                                 ColumnFields = column_fields,
                                 WidgetID = widget_id,
                                 )
        js_add_click = "$('#" + widget_id + "_add" + "').click(function () {" + \
                       "S3MultiselectWidgetAddClick(" +  str(js_add_click_args) + ")});"

        js_delete_click_args = dict(WidgetID = widget_id,
                                    ColumnFields = column_fields
                                    )     
        js_delete_click = "$('." + widget_id + "_delete" + "').live('click',function () {" + \
                       "S3MultiselectWidgetDeleteClick(this," +  str(js_delete_click_args) + ")});"

        #when the form is submitted, click the "add button" - just in case the user forgot to
        js_submit =  "$('form').submit( function() {" + \
                     "$('#" + widget_id + "_add" + "').click();" + "});"

        #if widget_id != "drrpp_project_country_ids":
        widget = TAG[""](input_json,
                         TABLE(_id = widget_id + "_rows", _class = "s3_multiselect_widget_rows", *widget_rows ),
                         SCRIPT(js_add_click),
                         SCRIPT(js_delete_click),
                         SCRIPT(js_submit)
                         )
        return widget

    # shn_multiselect_row_widget functions
    @staticmethod
    def _generate_row(widget_id, 
                      id, 
                      column_fields,
                      column_fields_represent = None, 
                      row = None,
                      is_dummy_row = False):
        """
            This widget is not yet complete!

            id - int - for the row
            fields - list of string - provides the order
            field_represents -  dict - the functions to find the values of the fields in the row 
        """   

        row_field_cells = []
        delete_attr = {"_row_id":id}
        #for row_field, row_width in zip(row_fields,row_widths):
        i = 0;
        for column_field in column_fields:
            if is_dummy_row:
                column_field_value = "DummyDisplay" + str(i)
                #attributes to identify row when deleting added row
                delete_attr['_' + column_field] = "DummyJSON" + str(i)             
            else:
                if column_fields_represent[column_field]:
                    column_field_value = column_fields_represent[column_field](row[column_field])
                else:
                    column_field_value = row[column_field]      
            #if column_field[-3:] <> "_id":
            row_field_cells.append(TD(column_field_value))     
            i= i+1

        #Delete button
        row_field_cells.append(TD(A("x", 
                                    _class = "s3_multiselect_widget_delete " + widget_id + "_delete", 
                                    _href = "javascript: void(0)", 
                                    **delete_attr)))    

        return TR(*row_field_cells)

    def represent(self,
                  value):

        db = self.db
        link_field_name = self.link_field_name
        link_table_name = self.link_table_name
        link_table = db[link_table_name]
        column_fields_represent = self.column_fields_represent

        ids = shn_split_multi_value(value)

        record_value_list = []

        for id in ids:
            field_value_list = []
            if id:
                row = db(link_table.id == id).select() 
                if len(row) > 0:
                    for field in self.represent_fields:
                        if column_fields_represent[field]:
                            field_value = column_fields_represent[field](row[0][field])
                        else:
                            field_value = row[0][field]
                        field_value_list.append( str( field_value) )
            record_value_list.append(self.represent_field_delim.join(field_value_list) )

        if record_value_list:
            return self.represent_record_delim.join(record_value_list)
        else:
            return None
