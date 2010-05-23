# -*- coding: utf-8 -*-
"""
    Utility Functions
    
    @author: Michael Howden (michael@aidiq.com)
    @date-created: 2010-05-23
    
"""

import re

# shn_get_db_field_value -----------------------------------------------------    
def shn_split_multi_value(value):
    """
    @author: Michael Howden (michael@aidiq.com)
    
    Splits a string of numbers delimitered by | into a list  
    
    If value = None, returns []  
    """
    if value:
        return re.compile('[\w\-:]+').findall(str(value))     
    else:
        return []      

# shn_get_db_field_value -----------------------------------------------------
def shn_get_db_field_value(db,
                           table, 
                           field, 
                           look_up, 
                           look_up_field = 'id', 
                           match_case = True):
    """
    @author: Michael Howden (michael@aidiq.com)
    
    @description:
        returns the value of <field> from the first record in <table_name>
        with <look_up_field> = <look_up>
        
    @arguements: 
        table - string - The name of the table         
        field - string - the field to find the value from
        look_up - string - the value to find 
        look_up_field - string - the field to find <look_up> in     
        match_case - bool         
        
    @returns:
        Field Value if there is a record
        None - if there is no matching record
        
    @example        
        shn_get_db_field_value("or_organisation", 
                               "id", 
                               look_up = "UNDP", 
                               look_up_field = "name" )
    """     
    if match_case or db[table][look_up_field].type != "string":
        row = db(db[table][look_up_field] == look_up).select(field)
    else:
       row = db(db[table][look_up_field].lower() == look_up).select(field)
        
    if len(row) > 0:
        return row[0][field]
    else:
        return None        
