# -*- coding: utf-8 -*-
"""
    Custom widgets to extend Web2Py

    @author: Michael Howden (michael@aidiq.com)
    @date-created: 2010-03-17

"""

import copy

from lxml import etree
from gluon.sqlhtml import *
from gluon.html import B, P, URL
from gluon.validators import *
from s3utils import *
from validators import *

repr_select = lambda l: len(l.name) > 48 and "%s..." % l.name[:44] or l.name

# -----------------------------------------------------------------------------
class S3DateWidget:
    """
        @author: Fran Boon (fran@aidiq.com)

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
class S3UploadWidget(UploadWidget):
    """
        Subclassed to not show the delete checkbox when field is mandatory
        - subclass doesn't currently work as download_url not passed in.
        - Patch submitted to Web2Py.
    """

    @staticmethod
    def widget(field, value, download_url=None, **attributes):
        """
        generates a INPUT file tag.

        Optionally provides an A link to the file, including a checkbox so
        the file can be deleted.
        All is wrapped in a DIV.

        see also: :meth:`FormWidget.widget`

        :param download_url: Optional URL to link to the file (default = None)
        """

        default=dict(
            _type='file',
            )
        attr = UploadWidget._attributes(field, default, **attributes)

        inp = INPUT(**attr)

        if download_url and value:
            url = download_url + '/' + value
            (br, image) = ('', '')
            if UploadWidget.is_image(value):
                br = BR()
                image = IMG(_src = url, _width = UploadWidget.DEFAULT_WIDTH)
            
            requires = attr["requires"]
            if requires == [] or isinstance(requires, IS_EMPTY_OR):
                inp = DIV(inp, '[',
                          A(UploadWidget.GENERIC_DESCRIPTION, _href = url),
                          '|',
                          INPUT(_type='checkbox',
                                _name=field.name + UploadWidget.ID_DELETE_SUFFIX),
                          UploadWidget.DELETE_FILE,
                          ']', br, image)
            else:
                inp = DIV(inp, '[',
                          A(UploadWidget.GENERIC_DESCRIPTION, _href = url),
                          ']', br, image)
        return inp

# -----------------------------------------------------------------------------
class S3AutocompleteWidget:
    """
        @author: Fran Boon (fran@aidiq.com)

        Renders a SELECT as an INPUT field with AJAX Autocomplete
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
        (function() {
            var data = { val:$('#%s').val(), accept:false };

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
                    data.accept = true;
                    return false;
                }
            })
            .data( 'autocomplete' )._renderItem = function( ul, item ) {
                return $( '<li></li>' )
                    .data( 'item.autocomplete', item )
                    .append( '<a>' + item.%s + '</a>' )
                    .appendTo( ul );
            };

            $('#%s').blur(function() {
                if (!$('#%s').val()) {
                    $('#%s').val('');
                    data.accept = true;
                }

                if (!data.accept) {
                    $('#%s').val(data.val);
                } else {
                    data.val = $('#%s').val();
                }

                data.accept = false;
            });
        })();
        """ % (fieldname, dummy_input, dummy_input, real_input, dummy_input, dummy_input)

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
class S3LocationAutocompleteWidget:
    """
        @author: Fran Boon (fran@aidiq.com)

        Renders a gis_location SELECT as an INPUT field with AJAX Autocomplete

        Differs from the S3AutocompleteWidget:
        - needs to have deployment_settings passed-in
        - excludes unreliable imported records (Level 'XX')
        - @ToDo: .represent for the returned data
        - @ToDo: Refreshes any dropdowns as-necessary (post_process)

        NB Currently not used. The LocationSelector widget include this functionality & more.
    """
    def __init__(self,
                 request,
                 deployment_settings,
                 prefix="gis",
                 resourcename="location",
                 fieldname="name",
                 post_process = "",
                 min_length=2):

        self.request = request
        self.deployment_settings = deployment_settings
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
        url = URL(r=self.request, c=self.prefix, f=self.resourcename, args="search.json", vars={"filter":"~", "field":fieldname, "exclude_field":"level", "exclude_value":"XX"})

        # Which Levels do we have in our hierarchy & what are their Labels?
        deployment_settings = self.deployment_settings
        location_hierarchy = deployment_settings.get_gis_locations_hierarchy()
        try:
            # Ignore the bad bulk-imported data
            del location_hierarchy["XX"]
        except KeyError:
            pass
        # What is the maximum level of hierarchy?
        #max_hierarchy = deployment_settings.get_gis_max_hierarchy()
        # Is full hierarchy mandatory?
        #strict = deployment_settings.get_gis_strict_hierarchy()

        post_process = self.post_process
        if not post_process:
            # @ToDo: Refreshes all dropdowns as-necessary
            post_process = ""

        js_autocomplete = """
        (function() {
            var data = { val:$('#%s').val(), accept:false };

            $('#%s').autocomplete({
                source: '%s',
                minLength: %d,
                focus: function( event, ui ) {
                    $( '#%s' ).val( ui.item.name );
                    return false;
                },
                select: function( event, ui ) {
                    $( '#%s' ).val( ui.item.name );
                    $( '#%s' ).val( ui.item.id );
                    """ % (dummy_input, dummy_input, url, self.min_length, dummy_input, dummy_input, real_input) + post_process + """
                    data.accept = true;
                    return false;
                }
            })
            .data( 'autocomplete' )._renderItem = function( ul, item ) {
                // @ToDo: .represent for returned data
                return $( '<li></li>' )
                    .data( 'item.autocomplete', item )
                    .append( '<a>' + item.name + '</a>' )
                    .appendTo( ul );
            };

            $('#%s').blur(function() {
                if (!$('#%s').val()) {
                    $('#%s').val('');
                    data.accept = true;
                }

                if (!data.accept) {
                    $('#%s').val(data.val);
                } else {
                    data.val = $('#%s').val();
                }

                data.accept = false;
            });
        })();
        """ % (dummy_input, dummy_input, real_input, dummy_input, dummy_input)

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
        url = URL(r=self.request, c="pr", f="person", args="search.json", vars={"filter":"~"})

        js_autocomplete = """
        (function() {
            var data = { val:$('#%s').val(), accept:false };

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
                    data.accept = true;
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
                    .appendTo( ul );
            };

            $('#%s').blur(function() {
                if (!$('#%s').val()) {
                    $('#%s').val('');
                    data.accept = true;
                }

                if (!data.accept) {
                    $('#%s').val(data.val);
                } else {
                    data.val = $('#%s').val();
                }

                data.accept = false;
            });
        })();
        """ % (dummy_input, dummy_input, real_input, dummy_input, dummy_input)

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
            * manual Lat/Lon entry (with optional GPS Coordinate Converter)
            * Geocoder lookup
            * Select location from Map
    """
    def __init__(self,
                 db,
                 gis,
                 deployment_settings,
                 request,
                 response,
                 T,
                 #hierarchy=True    # @ToDo: Force selection of the hierarchy (useful when we have that data fully-populated)
                 #level=None        # @ToDo: Support forcing which level of the hierarchy is expected to be entered for this instance of the field
                 ):

        self.db = db
        self.gis = gis
        self.deployment_settings = deployment_settings
        self.request = request
        self.response = response
        self.T = T

    def __call__(self, field, value, **attributes):

        #db = field._db  # old DAL
        #db = field.db   # new DAL
        db = self.db
        gis = self.gis
        deployment_settings = self.deployment_settings
        request = self.request
        response = self.response
        T = self.T

        # shortcut
        locations = db.gis_location

        # Read Options
        countries = response.s3.gis.countries  # Also needed by location_represent hence want to keep in model, so useful not to repeat
        # Should we use a Map-based selector?
        map_selector = deployment_settings.get_gis_map_selector()
        # Which Levels do we have in our hierarchy & what are their Labels?
        location_hierarchy = deployment_settings.get_gis_locations_hierarchy()
        try:
            # Ignore the bad bulk-imported data
            del location_hierarchy["XX"]
        except KeyError:
            pass
        # What is the maximum level of hierarchy?
        max_hierarchy = deployment_settings.get_gis_max_hierarchy()
        # Is full hierarchy mandatory?
        strict = deployment_settings.get_gis_strict_hierarchy()

        # Main Input
        default = dict(
                        _type = "text",
                        value = (value != None and str(value)) or "",
                        L0 = None,
                        L1 = None,
                        L2 = None,
                        L3 = None,
                        L4 = None,
                        L5 = None
                    )
        attr = StringWidget._attributes(field, default, **attributes)
        # Hide the real field
        attr["_class"] = "hidden"

        map_popup = ""

        if value:
            # Read current record
            this_location = db(locations.id == value).select(locations.uuid,
                                                             locations.name,
                                                             locations.level,
                                                             locations.lat,
                                                             locations.lon,
                                                             locations.addr_street,
                                                             locations.parent,
                                                             locations.path,
                                                             limitby=(0, 1)).first()
            uuid = this_location.uuid
            level = this_location.level
            default[level] = value
            lat = this_location.lat
            lon = this_location.lon
            addr_street = this_location.addr_street
            parent = this_location.parent
            path = this_location.path
            if path:
                # Lookup Ancestors
                ancestors = path.split("/")
                numberAncestors = len(ancestors)
                if numberAncestors > 1:
                    del ancestors[numberAncestors - 1]  # Remove self
                    if strict:
                        # No need to do a DAL query
                        for i in range(numberAncestors - 1):
                            default["L%i" % i] = ancestors[i]
                    else:
                        # Do a single SQL query for all ancestors to look up their levels
                        _ancestors = db(locations.id.belongs(ancestors)).select(locations.id,
                                                                                locations.level,
                                                                                limitby=(0, numberAncestors - 1))
                        for ancestor in _ancestors:
                            default[ancestor.level] = ancestor.id
            elif parent:
                # Path not populated, so need to do lookups manually :/
                _parent = db(locations.id == parent).select(locations.level, locations.parent, limitby=(0, 1)).first()
                if _parent.level:
                    default[_parent.level] = parent
                if _parent.parent:
                    _grandparent = db(locations.id == _parent.parent).select(locations.level, locations.parent, limitby=(0, 1)).first()
                    if _grandparent.level:
                        default[_grandparentparent.level] = _parent.parent
                    if _grandparent.parent:
                        _greatgrandparent = db(locations.id == _grandparent.parent).select(locations.level, locations.parent, limitby=(0, 1)).first()
                        if _greatgrandparent.level:
                            default[_greatgrandparent.level] = _grandparent.parent
                        if _greatgrandparent.parent:
                            _greatgreatgrandparent = db(locations.id == _greatgrandparent.parent).select(locations.level, locations.parent, limitby=(0, 1)).first()
                            if _greatgreatgrandparent.level:
                                default[_greatgreatgrandparent.level] = _greatgrandparent.parent

            # Provide the representation for the current/default Value
            #text = str(field.represent(default["value"]))
            #if "<" in text:
            #    # Strip Markup
            #    try:
            #        markup = etree.XML(text)
            #        text = markup.xpath(".//text()")
            #        if text:
            #            text = " ".join(text)
            #        else:
            #            text = ""
            #    except etree.XMLSyntaxError:
            #        pass
            #represent = text
            if level:
                # If within the locations hierarchy then don't populate the visible name box
                represent = ""
            else:
                represent = this_location.name

            if map_selector:
                config = gis.get_config()
                zoom = config.zoom
                if lat is None or lon is None:
                    lat = config.lat
                    lon = config.lon

                layername = T("Location")
                popup_label = ""
                filter = Storage(tablename = "gis_location", id = value)
                layer = gis.get_feature_layer("gis", "location", layername, popup_label, filter=filter)
                if layer:
                    feature_queries = [layer]
                else:
                    feature_queries = []
                map_popup = gis.show_map(lat = lat,
                                         lon = lon,
                                         # Same as a single zoom on a cluster
                                         zoom = zoom + 2,
                                         feature_queries = feature_queries,
                                         add_feature = True,
                                         add_feature_active = False,
                                         toolbar = True,
                                         collapsed = True,
                                         search = True,
                                         window = True,
                                         window_hide = True)

        else:
            # No default value
            uuid = ""
            represent = ""
            level = None
            lat = ""
            lon = ""
            addr_street = ""
            if map_selector:
                map_popup = gis.show_map(add_feature = True,
                                         add_feature_active = True,
                                         toolbar = True,
                                         collapsed = True,
                                         search = True,
                                         window = True,
                                         window_hide = True)

        #real_input = str(field).replace(".", "_")
        #dummy_input = "gis_location_name"

        # Settings to insert into static/scripts/S3/s3.locationselector.widget.js
        location_id = attr["_id"]
        url = URL(r=request, c="gis", f="location")

        # Localised strings
        empty_set = T("No locations registered at this level")
        loading_locations = T("Loading Locations")
        select_location = T("Select a location")
        degrees_validation_error = T("Degrees must be a number between -180 and 180")
        minutes_validation_error = T("Minutes must be a number greater than 0 and less than 60")
        seconds_validation_error = T("Seconds must be a number greater than 0 and less than 60")
        no_calculations_error = T("No calculations made")
        fill_lat = T("Fill in Latitude")
        fill_lon = T("Fill in Longitude")

        # Hierarchical Selector
        def level_dropdown(level, visible=False, current=None, required=False, button=None):

            """
                Prepare a dropdown select widget:
                - level: the level in the Location Hierarchy
                - visible: whether this dropdown is initially displayed or not
                - current: whether there is a current value for this dropdown
                - required: whether a selection at this level is mandatory
                - button: an optional button to place to the right of the dropdown
            """

            default_dropdown = dict(
                _type = "int",
                value =  current,
                )
            attr_dropdown = OptionsWidget._attributes(field, default_dropdown, **attributes)
            requires = IS_ONE_OF(db, "gis_location.id", repr_select,
                                 filterby = "level",
                                 filter_opts = (level,),
                                 orderby = "gis_location.name",
                                 sort = True,
                                 zero = "%s..." % select_location)
            if not required:
                requires = IS_NULL_OR(requires)
            if not isinstance(requires, (list, tuple)):
                requires = [requires]

            deleted = (locations.deleted == False)

            if level == "L0":
                if countries:
                    # Use the list of countries from deployment_settings instead of from db
                    options = []
                    for country in countries:
                        options.append((countries[country].id, countries[country].name))
                else:
                    # Prepopulate top-level dropdown from db
                    if hasattr(requires[0], "options"):
                        options = requires[0].options()
                    else:
                        raise SyntaxError, "widget cannot determine options of %s" % field

            else:
                if level:
                    _parent = default["L%i" % (int(_level[1:]) - 1)]
                else:
                    _parent = default[max_hierarchy]

                if level == "L1" and countries and len(countries) == 1:
                    # Prepopulate top-level dropdown from db
                    if hasattr(requires[0], "options"):
                        options = requires[0].options()
                    else:
                        raise SyntaxError, "widget cannot determine options of %s" % field

                elif current or _parent:
                    # Dropdown or one above this one contains a current value
                    # Read values from db
                    options = [("", "Select a location...")]
                    if level:
                        query = (locations.level == level) & deleted
                    else:
                        query = (locations.level == None) & deleted

                    if _parent:
                        query = query & (locations.parent == _parent)

                    records = db(query).select(locations.id, locations.name)
                    for record in records:
                        options.append((record.id, record.name))

                else:
                    # We don't want to pre-populate the dropdown - it will be pulled dynamically via AJAX when the parent dropdown is selected
                    options = [("", loading_locations)]

            opts = [OPTION(v, _value=k) for (k, v) in options]

            attr_dropdown["_id"] = "gis_location_%s" % level
            # Need to blank the name to prevent it from appearing in form.vars & requiring validation
            attr_dropdown["_name"] = ""
            if visible:
                if level:
                    label = LABEL(location_hierarchy[level], ":", _id="gis_location_label_%s" % level)
                else:
                    label = LABEL(T("Specific Location"), ":", _id="gis_location_label_%s" % level)
            else:
                # Hide the Dropdown & the Label
                attr_dropdown["_class"] = "hidden"
                if level:
                    label = LABEL(location_hierarchy[level], ":", _id="gis_location_label_%s" % level, _class="hidden")
                else:
                    label = LABEL(T("Specific Location"), ":", _id="gis_location_label_%s" % level, _class="hidden")

            widget = SELECT(*opts, **attr_dropdown)
            if button:
                row = DIV(TR(label, _id="gis_location_%s_label__row" % level), TR(TD(widget, _id="gis_location_%s__row" % level), TD(button)))
            else:
                row = DIV(TR(label, _id="gis_location_%s_label__row" % level), TR(widget, _id="gis_location_%s__row" % level))
            return row

        dropdowns = DIV()
        _level = "L0"
        if _level in location_hierarchy:
            if countries and len(countries) == 1:
                # Country hard-coded
                visible = False
            else:
                visible = True
            # @ToDo: Add button, if have rights
            button = ""
            dropdowns.append(level_dropdown(_level, visible=visible, current=default[_level], button=button))
        _level = "L1"
        if _level in location_hierarchy:
            if countries and len(countries) == 1:
                # Country is hard-coded, so display L1s by default
                visible = True
            elif default[_level] or default["L%i" % (int(_level[1:]) - 1)]:
                # We have an existing value to display (or need to be open because higher-level is selected)
                visible = True
            else:
                visible = False
            # @ToDo: Add button, if have rights
            button = ""
            dropdowns.append(level_dropdown(_level, visible=visible, current=default[_level], button=button))
        _level = "L2"
        if _level in location_hierarchy:
            if default[_level] or default["L%i" % (int(_level[1:]) - 1)]:
                # We have an existing value to display (or need to be open because higher-level is selected)
                visible = True
            else:
                visible = False
            # @ToDo: Add button, if have rights
            button = ""
            dropdowns.append(level_dropdown(_level, visible=visible, current=default[_level], button=button))
        _level = "L3"
        if _level in location_hierarchy:
            if default[_level] or default["L%i" % (int(_level[1:]) - 1)]:
                # We have an existing value to display (or need to be open because higher-level is selected)
                visible = True
            else:
                visible = False
            # @ToDo: Add button, if have rights
            button = ""
            dropdowns.append(level_dropdown(_level, visible=visible, current=default[_level], button=button))
        _level = "L4"
        if _level in location_hierarchy:
            if default[_level] or default["L%i" % (int(_level[1:]) - 1)]:
                # We have an existing value to display (or need to be open because higher-level is selected)
                visible = True
            else:
                visible = False
            # @ToDo: Add button, if have rights
            button = ""
            dropdowns.append(level_dropdown(_level, visible=visible, current=default[_level], button=button))
        # L5 not supported by testSuite
        _level = "L5"
        if _level in location_hierarchy:
            if default[_level] or default["L%i" % (int(_level[1:]) - 1)]:
                # We have an existing value to display (or need to be open because higher-level is selected)
                visible = True
            else:
                visible = False
            # @ToDo: Add button, if have rights
            button = ""
            dropdowns.append(level_dropdown(_level, visible=visible, current=default[_level], button=button))
        # Finally the level for specific locations
        _level = ""
        if not level and value:
            # We have an existing value to display
            visible = True
        elif default[max_hierarchy]:
            # max_hierarchy has a value, so we need to be open
            visible = True
        else:
            visible = False
        if visible:
            button = A(T("Location Details"), _href="#",
                       _id="gis_location_details-btn")
        else:
            button = A(T("Location Details"), _href="#",
                       _id="gis_location_details-btn",
                       _class="hidden")
        dropdowns.append(level_dropdown(_level, visible=visible, current=value, button=button))



        # Settings to be read by static/scripts/S3/s3.locationselector.widget.js
        js_location_selector = """
    var s3_gis_location_id = '%s';
    var s3_gis_maxlevel = '%s';
    var s3_gis_empty_set = '<option value="">%s</option>';
    var s3_gis_loading_locations = '<option value="">%s...</option>';
    var s3_gis_select_location = '<option value="" selected>%s...</option>';
    var s3_gis_url = '%s';
    S3.gis.uuid = '%s';
    var s3_gis_degrees_validation_error = '%s';
    var s3_gis_minutes_validation_error = '%s';
    var s3_gis_seconds_validation_error = '%s';
    var s3_gis_no_calculations_error = '%s';
    var s3_gis_fill_lat = '%s';
    var s3_gis_fill_lon = '%s';
    """ % (location_id,
           max_hierarchy[1:],
           empty_set,
           loading_locations,
           select_location,
           url,
           uuid,
           degrees_validation_error,
           minutes_validation_error,
           seconds_validation_error,
           no_calculations_error,
           fill_lat,
           fill_lon,
          )

        # Labels
        name_label = DIV(LABEL(T("Name") + ":"), SPAN("*", _class="req"), _id="gis_location_name_label", _class="hidden")
        street_label = LABEL(T("Street Address") + ":", _id="gis_location_addr_street_label", _class="hidden")
        lat_label = LABEL(T("Latitude") + ":", _id="gis_location_lat_label", _class="hidden")
        lon_label = LABEL(T("Longitude") + ":", _id="gis_location_lon_label", _class="hidden")

        # Form Fields
        street_widget = TEXTAREA(addr_street, _id="gis_location_addr_street")
        lat_widget = INPUT(_id="gis_location_lat", _value=lat)
        lon_widget = INPUT(_id="gis_location_lon", _value=lon)

        autocomplete = DIV(LABEL(T("Search") + ":"), BR(), INPUT(_id="gis_location_autocomplete"), _id="gis_location_autocomplete_div", _class="hidden")

        # Buttons
        search_button = A(T("Search Locations"), _href="#",
                          _id="gis_location_search-btn")

        add_button = A(T("Add New Location"), _href="#",
                       _id="gis_location_add-btn")

        cancel_button = A(T("Cancel Add"), _href="#",
                          _id="gis_location_cancel-btn",
                          _class="hidden")

        geolocate_button = A(T("Use Current Location"), _href="#",
                             _id="gis_location_geolocate-btn",
                             _class="hidden")

        if map_selector:
            map_button = A(T("Show Map"), _href="#",
                           _id="gis_location_map-btn",
                           _class="hidden")
        else:
            map_button = ""

        geocoder_button = A(T("Lookup Address"), _href="#",
                            _id="gis_location_geocoder-btn")

        latlon_help = locations.lat.comment
        converter_button = locations.lon.comment

        advanced_checkbox = DIV(T("Advanced") + ":", INPUT(_type="checkbox", _id="gis_location_advanced_checkbox", value=""), _id="gis_location_advanced_div", _class="hidden")

        # @ToDo: Replace with simple alternate input forms: Radio button defaults to decimal degrees (real inputs), but can select GPS or DDMMSS
        gps_converter_popup = DIV(
            DIV(T("Coordinate Conversion"), _class="x-window-header"),
            DIV(
                DIV(
                    P(
                        TABLE(
                            TR(
                                TD(
                                    B(T("Enter a GPS Coordinate") + ":"),
                                    INPUT(_type="text", _size="3", _id="gps_deg"), "deg",
                                    INPUT(_type="text", _size="6", _id="gps_min"), "min",
                                ),
                            ),
                            TR(
                                TD(
                                    B(T("Decimal Degrees") + ":"),
                                    INPUT(_type="text", _size="8", _id="gps_dec"),
                                ),
                            ),
                            TR(
                                TD(
                                    INPUT(_type="button", _value=T("Calculate"), _onclick="s3_gis_convertGps()"),
                                    INPUT(_type="reset", _value=T("Reset"), _onclick="s3_gis_convertGps()"),
                                ),
                            ),
                        _border="0", _cellpadding="2", _width="400"
                        ),
                    ),
                _class="x-tab", _title=T("in GPS format")
                ),

                DIV(
                    P(
                        TABLE(
                            TR(
                                TD(
                                    B(T("Enter Coordinates") + ":"),
                                    INPUT(_type="text", _size="3", _id="DDMMSS_deg"), "Deg",
                                    INPUT(_type="text", _size="2", _id="DDMMSS_min"), "Min",
                                    INPUT(_type="text", _size="2", _id="DDMMSS_sec"), "Sec",
                                ),
                            ),
                            TR(
                                TD(
                                    B(T("Decimal Degrees") + ":"),
                                    INPUT(_type="text", _size="8", _id="DDMMSS_dec"),
                                ),
                            ),
                            TR(
                                TD(
                                    INPUT(_type="button", _value=T("Calculate"), _onclick="s3_gis_convertDD()"),
                                    INPUT(_type="reset", _value=T("Reset")),
                                ),
                            ),
                        _border="0", _cellpadding="2", _width="400"
                        ),
                    ),
                _class="x-tab", _title=T("in Deg Min Sec format")
                ),
            _id="gis-convert-tabs"),
        _id="gis-convert-win", _class="x-hidden")

        # Rows
        #if represent:
        #    # We have a specific location to show
        #    name_rows = DIV(TR(name_label),
        #                    TR(INPUT(_id="gis_location_name", _value=represent)))
        #else:
        name_rows = DIV(TR(name_label),
                        TR(INPUT(_id="gis_location_name", _class="hidden")))
        street_rows = DIV(TR(street_label),
                          # @ToDo: Enable Geocoder here when ready
                          #TR(street_widget, geocoder_button, _id="gis_location_addr_street_row", _class="hidden"))
                          TR(street_widget, _id="gis_location_addr_street_row", _class="hidden"))
        lat_rows = DIV(TR(lat_label),
                       TR(lat_widget, latlon_help, _id="gis_location_lat_row", _class="hidden"))
        lon_rows = DIV(TR(lon_label),
                       TR(lon_widget, converter_button, _id="gis_location_lon_row", _class="hidden"))
        divider = TR("------------------------------------------------------------------")

        # The overall layout of the components
        return TAG[""](
                        #divider,           # This is in the widget, so underneath the label :/ Add in JS? 'Sections'?
                        TR(INPUT(**attr)),  # Real input, which is hidden
                        dropdowns,
                        TR(TD(search_button, autocomplete)),
                        TR(TD(add_button, cancel_button)),
                        TR(gps_converter_popup),
                        TR(map_popup),
                        name_rows,
                        street_rows,
                        # @ToDo: Enable GeoLocate here when ready
                        #TR(geolocate_button),
                        TR(map_button),
                        TR(advanced_checkbox),
                        lat_rows,
                        lon_rows,
                        divider,
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
