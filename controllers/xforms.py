# -*- coding: utf-8 -*-

def xforms():
    """
    Given a Table, returns an XForms to create an instance:
    http://code.javarosa.org/wiki/buildxforms
    http://www.w3schools.com/xforms/
    http://oreilly.com/catalog/9780596003692/preview.html
    """
    if len(request.args) == 0:
        session.error = T("Need to specify a table!")
        redirect(URL(r=request))
    _table = request.args[0]
    
    title = _table
    table = db[_table]
    
    instance_list = []
    bindings_list = []
    controllers_list = []
    
    for field in table.fields:
        if field in ['id','created_on','modified_on','uuid'] :
            # This will get added server-side
            pass
        else:
            # Instances
            if table[field].default:
                instance_list.append(TAG[field](table[field].default))
            else:
                instance_list.append(TAG[field]())
            
            # Bindings
            if 'IS_NOT_EMPTY' in str(table[field].requires):
                required = 'true()'
            else:
                required = 'false()'
                
            if table[field].type == 'string':
                _type = 'string'
            elif table[field].type == 'double':
                _type = 'decimal'
            elif table[field].type == 'datetime':
                _type = 'datetime'
            else:
                # Unknown type
                _type = 'string'
                
            bindings_list.append(TAG['bind'](_nodeset=field, _type=_type, _required=required))
            
            # Controllers
            if hasattr(table[field].requires, 'options'):
                items_list = []
                for option in table[field].requires.theset:
                    items_list.append(TAG['item'](TAG['label'](option), TAG['value'](option)))
                controllers_list.append(TAG['select1'](items_list, _ref=field))
            elif 'IS_IN_DB' in str(table[field].requires):
                # ToDo (similar to IS_IN_SET)
                pass
            else:
                # Normal Input field
                controllers_list.append(TAG['input'](TAG['label'](table[field].label), _ref=field))
                
    instance = TAG[title](instance_list, _xmlns='')
    bindings = bindings_list
    controllers = TAG['h:body'](controllers_list)
    
    response.headers['Content-Type'] = 'application/xml'
    response.view = 'xforms.xml'
    return dict(title=title, instance=instance, bindings=bindings, controllers=controllers)
