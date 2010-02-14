# -*- coding: utf-8 -*-

import StringIO
import xml.dom.minidom

def create():
    """
    Given a Table, returns an XForms to create an instance:
    http://code.javarosa.org/wiki/buildxforms
    http://www.w3schools.com/xforms/
    http://oreilly.com/catalog/9780596003692/preview.html
    """
    if len(request.args) == 0:
        session.error = T("Need to specify a table!")
        redirect(URL(r=request))
    _table = request.args(0)

    title = _table
    table = db[_table]

    instance_list = []
    bindings_list = []
    controllers_list = []

    for field in table.fields:
        if field in ['id', 'created_on', 'modified_on', 'uuid'] :
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
            elif table[field].type == 'integer':
                _type = 'integer'
            else:
                # Unknown type
                _type = 'string'

            bindings_list.append(TAG['bind'](_nodeset=field, _type=_type, _required=required))

            # Controllers
            if hasattr(table[field].requires, 'option'):
                items_list = []
                for option in table[field].requires.theset:
                    items_list.append(TAG['item'](TAG['label'](option), TAG['value'](option)))
                controllers_list.append(TAG['select1'](items_list, _ref=field))
            elif 'IS_IN_DB' in str(table[field].requires):
                # ToDo (similar to IS_IN_SET)
                pass
            elif 'IS_IN_SET' in str(table[field].requires):
                pass
#                items_list=[] 
#               for option in table[field].requires.theset:
#                    items_list.append(TAG['item'](TAG['label'](option), TAG['value'](option)))
#                controllers_list.append(TAG['select1'](items_list, _ref=field))
            else:
                # Normal Input field
                controllers_list.append(TAG['input'](TAG['label'](table[field].label), _ref=field))

    instance = TAG[title](instance_list, _xmlns='')
    bindings = bindings_list
    controllers = TAG['h:body'](controllers_list)

    response.headers['Content-Type'] = 'application/xml'
    response.view = 'xforms.xml'
    return dict(title=title, instance=instance, bindings=bindings, controllers=controllers)



def csvdata(nodelist):
    """Returns the data in the given node as a comma seperated string"""
    data = ""
    for subnode in nodelist:
        if (subnode.nodeType == subnode.ELEMENT_NODE):
            try:
                data = data + "," + subnode.childNodes[0].data
            except:
                data = data+ ","
    return data[1:] + "\n"

def csvheader(parent,nodelist):
    """Gives the header for the csv"""
    header = ""
    for subnode in nodelist:
        if (subnode.nodeType == subnode.ELEMENT_NODE):
            header = header + "," + parent + "." + subnode.tagName
    return header[1:] + "\n"



def importxml(db,xmlinput):
    """Converts the XML to a CSV compatible with the import_from_csv_file of
    web2py"""
    doc = xml.dom.minidom.parseString(xmlinput)
    parent = doc.childNodes[0].tagName
    csvout = csvheader(parent, doc.childNodes[0].childNodes)
    for subnode in doc.childNodes:
        csvout = csvout + csvdata(subnode.childNodes)
    fh = StringIO.StringIO()
    fh.write(csvout)
    fh.seek(0, 0)
    try:
        db[parent].import_from_csv_file(fh)
        return 1
    except:
        return 0

@auth.requires_membership('Administrator')
def post():
    data = importxml(db, request.body.read())
    return data
