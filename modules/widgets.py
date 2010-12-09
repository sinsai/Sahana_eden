# -*- coding: utf-8 -*-
"""
    Custom widgets to extend Web2Py

    @author: Michael Howden (michael@aidiq.com)
    @date-created: 2010-03-17

"""

import copy

from lxml import etree
from gluon.sqlhtml import *
from gluon.html import P, URL
from gluon.validators import *
from s3utils import *
from validators import *

repr_select = lambda l: len(l.name) > 48 and "%s..." % l.name[:44] or l.name

# -----------------------------------------------------------------------------
class S3DateWidget:
    """
    Standard Date widget, but with a modified yearRange to support Birth dates
    """

    def __init__(self,
                 before=10,  # How many years to show before the current one
                 after=10    # How many years to show after the current one
                ):
        self.min = before
        self.max = after
    
    def __call__(self ,field, value, **attributes):
        default = dict(
            _type = "text",
            value = (value!=None and str(value)) or "",
            )
        attr = StringWidget._attributes(field, default, **attributes)

        selector = str(field).replace(".", "_")
        
        date_options = """
    $(function() {
        $( '#%s' ).datepicker( 'option', 'yearRange', 'c-%s:c+%s' );
    });
    """ % (selector, self.min, self.max)
        
        return TAG[""](
                        INPUT(**attr),
                        SCRIPT(date_options)
                      )
                      
# -----------------------------------------------------------------------------
class S3AutocompleteWidget:
    """
    @author: Fran Boon (fran@aidiq.com)

    Renders a SELECT as an INPUT field with AJAX Autocomplete
    
    # @ToDo version for Locations
    """
    def __init__(self,
                 request,
                 prefix,
                 resourcename,
                 fieldname="name",
                 post_process = "",
                 min_length=2):

        self.request = request
        self.prefix = prefix
        self.resourcename = resourcename
        self.fieldname = fieldname
        self.post_process = post_process
        self.min_length = min_length

    def __call__(self ,field, value, **attributes):
        default = dict(
            _type = "text",
            value = (value != None and str(value)) or "",
            )
        attr = StringWidget._attributes(field, default, **attributes)

        # Hide the real field
        attr["_class"] = attr["_class"] + " hidden"
        
        real_input = str(field).replace(".", "_")
        dummy_input = "dummy_%s" % real_input
        fieldname = self.fieldname
        url = URL(r=self.request, c=self.prefix, f=self.resourcename, args="search.json", vars={"filter":"~", "field":fieldname})
        
        js_autocomplete = """
        (function()
        {
            var data = { val : $('#%s').val(), accept : false };

            $('#%s').autocomplete({
                source: '%s',
                minLength: %d,
                focus: function( event, ui ) {
                    $( '#%s' ).val( ui.item.%s );
                    return false;
                },
                select: function( event, ui ) {
                    $( '#%s' ).val( ui.item.%s );
                    $( '#%s' ).val( ui.item.id );
                    """ % (dummy_input, dummy_input, url, self.min_length, dummy_input, fieldname, dummy_input, fieldname, real_input) + self.post_process + """
                    return false;
                }
            })
            .data( 'autocomplete' )._renderItem = function( ul, item ) {
                return $( '<li></li>' )
                    .data( 'item.autocomplete', item )
                    .append( '<a>' + item.%s + '</a>' )
                    .click(function()
                    {
                        data.accept = true;
                    })
                    .appendTo( ul );
            };

            $('#%s').blur(function()
            {
                if(!data.accept) $('#%s').val(data.val);
                else data.val = $('#%s').val();

                data.accept = false;
            });
        })();
        """ % (fieldname, dummy_input, dummy_input, dummy_input)
        
        if value:
            text = str(field.represent(default["value"]))
            if "<" in text:
                # Strip Markup
                try:
                    markup = etree.XML(text)
                    text = markup.xpath(".//text()")
                    if text:
                        text = " ".join(text)
                    else:
                        text = ""
                except etree.XMLSyntaxError:
                    pass
            represent = text
        else:
            represent = ""
        
        return TAG[""](
                        INPUT(_id=dummy_input, _value=represent),
                        INPUT(**attr),
                        SCRIPT(js_autocomplete)
                      )

# -----------------------------------------------------------------------------
class S3PersonAutocompleteWidget:
    """
    @author: Fran Boon (fran@aidiq.com)

    Renders a pr_person SELECT as an INPUT field with AJAX Autocomplete
    
    Differs from the S3AutocompleteWidget in that it uses 3 name fields
    """
    def __init__(self,
                 request,
                 post_process = "",
                 min_length=2):

        self.request = request
        self.post_process = post_process
        self.min_length = min_length

    def __call__(self ,field, value, **attributes):
        default = dict(
            _type = "text",
            value = (value != None and str(value)) or "",
            )
        attr = StringWidget._attributes(field, default, **attributes)

        # Hide the real field
        attr["_class"] = attr["_class"] + " hidden"
        
        real_input = str(field).replace(".", "_")
        dummy_input = "dummy_%s" % real_input
        url = URL(r=self.request, c="pr", f="person", args="search.json", vars={"filter":"~", "field":"first_name", "field2":"middle_name", "field3":"last_name"})
        
        js_autocomplete = """
        (function()
        {
            var data = { val : $('#%s').val(), accept : false };

            $('#%s').autocomplete({
                source: '%s',
                minLength: %d,
                focus: function( event, ui ) {
                    var name = '';
                    if (ui.item.first_name != null) {
                        name += ui.item.first_name + ' ';
                    }
                    if (ui.item.middle_name != null) {
                        name += ui.item.middle_name + ' ';
                    }
                    if (ui.item.last_name != null) {
                        name += ui.item.last_name;
                    }
                    $( '#%s' ).val( name );
                    return false;
                },
                select: function( event, ui ) {
                    var name = '';
                    if (ui.item.first_name != null) {
                        name += ui.item.first_name + ' ';
                    }
                    if (ui.item.middle_name != null) {
                        name += ui.item.middle_name + ' ';
                    }
                    if (ui.item.last_name != null) {
                        name += ui.item.last_name;
                    }
                    $( '#%s' ).val( name );
                    $( '#%s' ).val( ui.item.id );
                    """ % (dummy_input, dummy_input, url, self.min_length, dummy_input, dummy_input, real_input) + self.post_process + """
                    return false;
                }
            })
            .data( 'autocomplete' )._renderItem = function( ul, item ) {
                var name = '';
                if (item.first_name != null) {
                    name += item.first_name + ' ';
                }
                if (item.middle_name != null) {
                    name += item.middle_name + ' ';
                }
                if (item.last_name != null) {
                    name += item.last_name;
                }
                return $( '<li></li>' )
                    .data( 'item.autocomplete', item )
                    .append( '<a>' + name + '</a>' )
                    .click(function()
                    {
                        data.accept = true;
                    })
                    .appendTo( ul );
            };

            $('#%s').blur(function()
            {
                if(!data.accept) $('#%s').val(data.val);
                else data.val = $('#%s').val();

                data.accept = false;
            });
        })();
        """ % (dummy_input, dummy_input, dummy_input)
        
        if value:
            # Provide the representation for the current/default Value
            text = str(field.represent(default["value"]))
            if "<" in text:
                # Strip Markup
                try:
                    markup = etree.XML(text)
                    text = markup.xpath(".//text()")
                    if text:
                        text = " ".join(text)
                    else:
                        text = ""
                except etree.XMLSyntaxError:
                    pass
            represent = text
        else:
            represent = ""
        
        return TAG[""](
                        INPUT(_id=dummy_input, _value=represent),
                        INPUT(**attr),
                        SCRIPT(js_autocomplete)
                      )

# -----------------------------------------------------------------------------
class S3LocationSelectorWidget:
    """
    @author: Fran Boon (fran@aidiq.com)

    @ToDo: This is a work-in-progress
    http://eden.sahanafoundation.org/wiki/BluePrintGISLocationSelector

    Renders a gis_location SELECT as a hierarchical dropdown with the ability to add a new location from within the main form
    - new location can be specified as:
        * a simple name (hopefully within hierarchy)
        * manual Lat/Lon entry (with optional GPS Coordinate Converter
        * Geocoder lookup
        * Select location from Map
    """
    def __init__(self,
                 request,
                 response,
                 T,
                 #hierarchy=True    # @ToDo Force selection of the hierarchy (useful when we have that data fully-populated)
                 #level=None        # @ToDo Support forcing which level of the hierarchy is expected to be entered for this instance of the field
                 ):

        self.request = request
        self.response = response
        self.T = T

    def __call__(self ,field, value, **attributes):

        db = field._db
        request = self.request
        response = self.response
        T = self.T

        # Read Options
        _gis = response.s3.gis
        # Which Levels do we have in our hierarchy & what are their Labels?
        location_hierarchy = _gis.location_hierarchy
        # Ignore the bad bulk-imported data
        del location_hierarchy["XX"]
        
        # Read current record
        if value:
            this_location = db(db.gis_location.id == value).select(db.gis_location.level,
                                                                   db.gis_location.lat,
                                                                   db.gis_location.lon,
                                                                   db.gis_location.addr_street,
                                                                   db.gis_location.parent,
                                                                   limitby=(0, 1)).first()
            level = this_location.level
            lat = this_location.lat
            lon = this_location.lon
            addr_street = this_location.addr_street
            parent = this_location.parent
            if parent:
                # & grandparent? @ToDo
                pass
        else:
            this_location = None
            lat = ""
            lon = ""
            addr_street = ""
        
        # Main Input
        default = dict(
            _type = "text",
            value = (value != None and str(value)) or "",
            )
        attr = StringWidget._attributes(field, default, **attributes)
        # Hide the real field
        attr["_class"] = attr["_class"] + " hidden"
        
        real_input = str(field).replace(".", "_")
        dummy_input = "gis_location_name"

        # Settings to insert into static/scripts/S3/s3.locationselector.widget.js
        location_id = attr["_id"]
        #def url(level):
        #    return URL(r=request, c="gis", f="location", args="search.json", vars={"filter":"=", "field":"level", "value":"%s" % level})
        url = URL(r=request, c="gis", f="location", args="search.json", vars={"filter":"=", "field":"level"})
        
        # Localised strings
        empty_set = T("No locations registered at this level")
        loading_locations = T("Loading Locations")
        select_location = T("Select a location")
        
        # Hierarchical Selector
        # @ToDo if this is an Admin Level then set the right dropdown to this level
        # @ToDo if there is parent detail, then set the parent dropdowns to the right levels
        default_dropdown = dict(
            _type = "int",
            value = 0,
            )
        attr_dropdown = OptionsWidget._attributes(field, default_dropdown, **attributes)
        def level_dropdown(level, required=False):
            # Prepare a dropdown widget
            # @ToDo convert to the hierarchical AJAX
            # IS_ONE_OF_EMPTY, etc
            requires = IS_ONE_OF(db, "gis_location.id", repr_select,
                                 filterby = "level",
                                 filter_opts = (level,),
                                 orderby = "gis_location.name",
                                 sort = True,
                                 zero = select_location + "...")
            if not required:
                requires = IS_NULL_OR(requires)
            if not isinstance(requires, (list, tuple)):
                requires = [requires]
            if level == "L0":
                if _gis.countries:
                    # Use the list of countries from deployment_settings instead of from DB
                    options = []
                    for country_code in _gis.countries:
                        country = db(db.gis_location.code == country_code).select(db.gis_location.id, db.gis_location.name, limitby=(0, 1)).first()
                        options.append((country.id, country.name))
                else:
                    if hasattr(requires[0], "options"):
                        options = requires[0].options()
                    else:
                        raise SyntaxError, "widget cannot determine options of %s" % field
            else:
                if level == "L1" and _gis.countries and len(_gis.countries) == 1:
                    if hasattr(requires[0], "options"):
                        options = requires[0].options()
                    else:
                        raise SyntaxError, "widget cannot determine options of %s" % field
                else:
                    # We don't want to pre-populate the dropdown - it will be pulled dynamically via AJAX when the parent dropdown is selected
                    options = [(0, loading_locations)]
            opts = [OPTION(v, _value=k) for (k, v) in options]

            this_attr = copy.copy(attr_dropdown)
            this_attr["_id"] = "gis_location_%s" % level
            if level == "L0" and not len(_gis.countries) == 1:
                # Don't Hide the Country selector if not hard-coded
                label = LABEL(location_hierarchy[level], ":", _id="gis_location_label_%s" % level)
            elif level == "L1" and len(_gis.countries) == 1:
                # Don't Hide the L1 selector if Country hard-coded
                label = LABEL(location_hierarchy[level], ":", _id="gis_location_label_%s" % level)
            else:
                # Hide the Dropdown & the selector
                this_attr["_class"] = this_attr["_class"] + " hidden"
                label = LABEL(location_hierarchy[level], ":", _id="gis_location_label_%s" % level, _class="hidden")

            widget = SELECT(*opts, **this_attr)
            row = DIV(TR(label), TR(widget))
            return row

        dropdowns = DIV()
        if "L0" in location_hierarchy:
            dropdowns.append(level_dropdown("L0"))
            maxlevel = "L0"
        if "L1" in location_hierarchy:
            dropdowns.append(level_dropdown("L1"))
            maxlevel = "L1"
        if "L2" in location_hierarchy:
            dropdowns.append(level_dropdown("L2"))
            maxlevel = "L2"
        if "L3" in location_hierarchy:
            dropdowns.append(level_dropdown("L3"))
            maxlevel = "L3"
        if "L4" in location_hierarchy:
            dropdowns.append(level_dropdown("L4"))
            maxlevel = "L4"
        if "L5" in location_hierarchy:
            dropdowns.append(level_dropdown("L5"))
            maxlevel = "L5"

        # Settings to be read by static/scripts/S3/s3.locationselector.widget.js
        js_location_selector = """
    var gis_location_id = '%s';
    var gis_maxlevel = '%s';
    var gis_empty_set = '<option value="">%s</option>';
    var gis_loading_locations = '<option value="">%s...</option>';
    var gis_select_location = '<option value="" selected>%s...</option>';
    var gis_url = '%s';
    $(function() {
    });
    """ % (location_id, maxlevel, empty_set, loading_locations, select_location, url)
        
        if value:
            # Provide the representation for the current/default Value
            text = str(field.represent(default["value"]))
            if "<" in text:
                # Strip Markup
                try:
                    markup = etree.XML(text)
                    text = markup.xpath(".//text()")
                    if text:
                        text = " ".join(text)
                    else:
                        text = ""
                except etree.XMLSyntaxError:
                    pass
            represent = text
        else:
            represent = ""

        add_button = A(T("Add New Location"), _id="gis_location_add-btn", _href="#",
                                              #_class="action-btn"
                                              )

        geolocate_button = A(T("Use Current Location"), _id="gis_location_geolocate-btn", _href="#",
                                                        _class="hidden"
                                                        #_class="action-btn hidden"
                                                        )

        map_button = A(T("Select using Map"), _id="gis_location_map-btn", _href="#",
                                              _class="hidden"
                                              #_class="action-btn hidden"
                                              )

        geocode_button = A(T("Lookup Address"), _id="gis_location_geocode-btn", _href="#",
                                                _class="hidden"
                                                #_class="action-btn hidden"
                                                )

        converter_button = A(T("Coordinate Converter"), _id="gis_location_converter-btn", _href="#",
                                                        _class="hidden"
                                                        #_class="action-btn hidden"
                                                        )

        return TAG[""](
                        INPUT(**attr), # Real input, which is hidden
                        dropdowns,
                        TR(add_button),
                        TR(DIV(geolocate_button, map_button)),
                        TR(DIV(LABEL(T("Name") + ":"), SPAN("*", _class="req"), _id="gis_location_name_label", _class="hidden")),
                        TR(INPUT(_id=dummy_input, _value=represent, _class="hidden")),
                        TR(LABEL(T("Street Address") + ":", _id="gis_location_addr_street_label", _class="hidden")),
                        TR(DIV(TEXTAREA(_id="gis_location_addr_street", _class="hidden", _value=addr_street), geocode_button)),
                        TR(DIV(T("Advanced") + ":", INPUT(_type="checkbox", _id="gis_location_advanced_checkbox"), _id="gis_location_advanced_div", _class="hidden")),
                        TR(LABEL(T("Latitude") + ":", _id="gis_location_lat_label", _class="hidden")),
                        TR(INPUT(_id="gis_location_lat", _value=lat), db.gis_location.lat.comment, _id="gis_location_lat_row", _class="hidden"),
                        TR(LABEL(T("Longitude") + ":", _id="gis_location_lon_label", _class="hidden")),
                        TR(INPUT(_id="gis_location_lon", _value=lon), db.gis_location.lon.comment, _id="gis_location_lon_row", _class="hidden"),
                        SCRIPT(js_location_selector)
                      )

# -----------------------------------------------------------------------------
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
                 db = None,
                 lookup_table_name = None,
                 lookup_field_name = None,
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

        if db and lookup_table_name and lookup_field_name:
            self.requires = IS_NULL_OR(IS_IN_DB(db,
                                   db[lookup_table_name].id,
                                   "%(" + lookup_field_name + ")s",
                                   multiple = multiple))

        if options:
            self.options = options
        else:
            if hasattr(self.requires, "options"):
                self.options = self.requires.options()
            else:
                raise SyntaxError, "widget cannot determine options of %s" % field


    def widget( self,
                field,
                value = None
                ):
        if self.db:
            db = self.db
        else:
            db = field._db

        values = shn_split_multi_value(value)

        attr = OptionsWidget._attributes(field, {})

        num_row  = len(self.options)/self.num_column
        # Ensure division  rounds up
        if len(self.options) % self.num_column > 0:
             num_row = num_row +1

        table = TABLE(_id = str(field).replace(".", "_"))

        for i in range(0,num_row):
            table_row = TR()
            for j in range(0, self.num_column):
                # Check that the index is still within self.options
                index = num_row*j + i
                if index < len(self.options):
                    input_options = {}
                    input_options = dict(requires = attr.get("requires", None),
                                         _value = str(self.options[index][0]),
                                         value = values,
                                         _type = "checkbox",
                                         _name = field.name,
                                         hideerror = True
                                        )
                    tip_attr = {}
                    help_text = ""
                    if self.help_lookup_field_name:
                        help_text = str( P( shn_get_db_field_value(db=db,
                                                                   table = self.lookup_table_name,
                                                                   field = self.help_lookup_field_name,
                                                                   look_up = self.options[index][0],
                                                                   look_up_field = "id")
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
                                       look_up_field = "id")
                   for id in shn_split_multi_value(value) if id]
        if list and not None in list:
            return ", ".join(list)
        else:
            return None

# -----------------------------------------------------------------------------
class JSON(INPUT):
    """
    @author: Michael Howden (michael@aidiq.com)

    Extends INPUT() from gluon/html.py

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
    * have postprocessing to convert 'id' -> '{"id":X}'
    * Why are JSON attributes being saved?
    * Use S3XRC
    """
    def _validate(self):
        # must be post-processing - because it needs the id of the added record
        name = self["_name"]
        if name == None or name == "":
            return True
        name = str(name)

        json_str = self.request_vars.get(name, None)

        if json_str == "":
            # Don't do anything with a blank field
            value =  self["existing_value"]

        elif not "link_field_name" in self.attributes:
            value = self._process_json(json_str,
                                       self["existing_value"] )
            # This will be an autocomplete (not multi select), therefore extract value from list
            if value:
                value = value[0]
        else:
            # If link_field_name exists ((S3Multiselect, _process_json will require the record id
            # therefore, it must be called from the onaccept, after the record is created.
            if self["existing_value"]:
                # ERROR - this causes errors if self["existing_value"] contains '
                value =  "'"  + self["existing_value"] + "'," + json_str
            else:
                value = json_str

        if value == "":
            value = None

        self["value"] = self.vars[name] = value

        return True

    def onaccept(self,
                 db,
                 link_field_value,
                 json_request):
        json_str = json_request.post_vars.get(self["_name"], None)
        if json_str:
            value = self._process_json(json_str,
                                       self["existing_value"],
                                       link_field_value = link_field_value,
                                       json_request = json_request )
            value = "|%s|" % "|".join(value)
            update_dict = {self["_name"]: value}
            db(db[self["table_name"]].id == link_field_value).update(**update_dict)


    def _process_json(self,
                      json_str,
                      existing_value = "",
                      link_field_value = None,
                      json_request = None
                      ):

        json_table = self.attributes["json_table"]
        db = json_table._db

        values = []

        if existing_value:
            existing_values = shn_split_multi_value(existing_value)
            for id in existing_values:
                id = str(id)
                if id not in values:
                    values.append(id)

        link_field_name = None
        if "link_field_name" in self.attributes:
            link_field_name = self.attributes["link_field_name"]

        try:
            json_data = eval(json_str)
        except:
            # TODO: This should record the error, but not hang
            raise SyntaxError, "JSON String %s is invalid" % json_str
            return None

        # If there is only one JSON object, make it iterable
        if type(json_data).__name__ != "tuple":
            json_data = [json_data]
        for json_record in json_data:
            # This is to handle the existing values - fix if the validation fails on another field
            # and there is no "on_accept" to save the JSON.
            if isinstance( json_record, (tuple, list) ):
                json_record = int(json_record[0])
            if type(json_record).__name__ == "int":
                id = str(json_record)
                if id not in values:
                    values.append(id)
                continue
            if isinstance( json_record, (str) ):
                ids = shn_split_multi_value(json_record)
                for id in ids:
                    if id not in values:
                        values.append(id)
                continue

            json_record = Storage(json_record)

            # insert value to link this record back to the record currently being saved
            if link_field_name:
                json_record[link_field_name] = link_field_value

            query = (json_table.deleted == False)
            for field, value in json_record.iteritems():
                if type(value).__name__ == "dict":
                    # recurse through this JSON data
                    # TODO - This doesn't work with nested multiselect, unless we access it's existing value.
                    # This could be done by doing the recurse AFTER the add... but then we would still need to get the variables out...
                    recurse_table_name = json_table[field].type[10:]
                    value = JSON(json_table = db[recurse_table_name])._process_json(str(value))
                    if value:
                        value = value[0]
                    json_record[field] = value

                if field == "file":
                    f = json_request.post_vars[value]

                    if hasattr(f, "file"):
                        (source_file, original_filename) = (f.file, f.filename)
                    elif isinstance(f, (str, unicode)):
                        ### do not know why this happens, it should not
                        (source_file, original_filename) = \
                            (cStringIO.StringIO(f), "file.txt")
                    filename = db.drrpp_file.file.store(source_file, original_filename)

                    json_record[field] = value = filename

                # Build query to test if this record is already in the DB
                # NB: Query & bool OK; bool & Query NOT!
                query = query & (json_table[field] == value)

            if "id" not in json_record:
                # ADD
                # Search for the value existing in the table already
                # TODO - why is query becoming a bool?
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
                # DELETE / UPDATE
                id = json_record.id
                del json_record.id
                #json_table[id] = json_record
                if len(json_record) > 0:
                    db(json_table.id == id).update(**json_record)

                id = str(id)
                if json_record.deleted == True and id in values:
                    values.remove(id)
                elif id not in values:
                    values.append(id)

        return values

# -----------------------------------------------------------------------------
class S3MultiSelectWidget(FormWidget):
    """
    @author: Michael Howden (michael@aidiq.com)

    This widget will return a table which can have rows added or deleted (not currently edited).
    This widget can be added to a table using a XXXX_dummy field. This field will only store the ID of the record and serve as a placeholder.

    :param link_table_name: - string -
    :param link_field_name: - Field -
    :param column_fields:  - list of strings - optional. The fields from the link_table which will be displayed as columns.
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
        link_table_name = self.link_table_name
        link_table = db[link_table_name]
        link_field_name = self.link_field_name
        column_fields = self.column_fields

        widget_id = str(field).replace(".", "_")

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
            header_row.append(TD(link_table[column_field].label,
                                 _class = "s3_multiselect_widget_column_label"))
            input_widget = link_table[column_field].widget
            if not input_widget:
                if link_table[column_field].type.startswith("reference"):
                    input_widget = OptionsWidget.widget
                elif OptionsWidget.has_options(link_table[column_field]):
                    if not link_table[column_field].requires.multiple:
                        input_widget = OptionsWidget.widget
                    else:
                        input_widget = MultipleOptionsWidget.widget
                else:
                    input_widget = SQLFORM.widgets[link_table[column_field].type].widget
            input_element = input_widget(link_table[column_field],
                                         None,
                                         _id = widget_id + "_" + column_field,
                                         _name = None)
            # Insert the widget id in front of the element id
            input_element.__setitem__("_id",
                                      widget_id + "_" + column_field # input_element.__getitem__("_id")
                                      )
            input_row.append(input_element)

        widget_rows = [TR(header_row)]

        if isinstance( value, ( str ) ):
            if "{" in value:
                value = eval(value)

        if isinstance( value, (tuple, list) ):
            values = value
        else:
            values = [value]

        for value in values:
            if isinstance( value, (tuple, list) ):
                value = str( value[0] )
            if isinstance( value, ( str ) ):
                ids = shn_split_multi_value(value)
                for id in ids:
                    # We should put a check here to make sure we don't double display rows
                    if id:
                        row = db(link_table.id == id).select()
                        if len(row) > 0:    # If is NOT true, it indicates that an error has occurred
                            widget_rows.append(self._generate_row(widget_id,
                                                                  id,
                                                                  column_fields = column_fields,
                                                                  column_fields_represent = self.column_fields_represent,
                                                                  row = row[0],
                                                                  is_dummy_row = False)
                                                )
            elif isinstance( value, (dict) ):
                if "deleted" not in value.keys():
                    widget_rows.append(self._generate_row(widget_id,
                                                          "New",
                                                          column_fields = column_fields,
                                                          column_fields_represent = self.column_fields_represent,
                                                          row = value,
                                                          is_dummy_row = False)
                                        )
            #else:
            #    raise SyntaxError, "multiselectwidget got %s in it's value  - ERROR" % type(value).__name__

        # Get the current value to display rows for existing data.
        ids = shn_split_multi_value(value)

        input_row.append(TD(A(DIV(_class = "s3_multiselect_widget_add_button"),

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
        js_delete_click = "$('." + widget_id + "_delete" + "').live('click', function () {" + \
                          "S3MultiselectWidgetDeleteClick(this," +  str(js_delete_click_args) + ")});"

        # When the form is submitted, click the "add button" - just in case the user forgot to
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
                # Attributes to identify row when deleting added row
                delete_attr["_" + column_field] = "DummyJSON" + str(i)
            else:
                if isinstance(row[column_field], (dict) ):
                    # Hack to get the rows to display after a failed validation
                    column_field_value = row[column_field].values()[0]
                elif column_fields_represent[column_field]:
                    column_field_value = column_fields_represent[column_field](row[column_field])
                else:
                    column_field_value = row[column_field]
            #if column_field[-3:] <> "_id":
            row_field_cells.append(TD(column_field_value))
            i= i+1

        # Delete button
        row_field_cells.append(TD(A(DIV(_class = "s3_multiselect_widget_delete_button"),
                                  _class = "s3_multiselect_widget_delete " + widget_id + "_delete",
                                  _href = "javascript: void(0)",
                                  **delete_attr),
                               _class = "s3_multiselect_widget_delete_button")
                               )

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
        return_list = []

        for id in ids:
            if id:
                row = db(link_table.id == id).select()
                if len(row) > 0:
                    for field in self.represent_fields:
                        if column_fields_represent[field]:
                            #field_value = column_fields_represent[field](row[0][field])
                            field_value = link_table[field].represent(row[0][field])
                        else:
                            field_value = row[0][field]
                        #if not isinstance(field_value, (A) ):
                        field_value = str(field_value)
                        return_list.append( field_value )
                        return_list.append( self.represent_field_delim )
                    if return_list:
                        return_list.pop() # remove the last delim
                    return_list.append( self.represent_record_delim )

        if return_list:
            return_list.pop() # remove the last delim
            # XML will not escape links in the string
            return_value = XML( "".join(return_list) )
        else:
            return_value = None

        if len(str(return_value)) > 0:
            if str(return_value)[0] != "<":
                return_value = str(return_value)
            else:
                return_value = return_value

        return return_value
