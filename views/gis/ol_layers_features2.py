#Python port of ol_layers_features2.php

# Sample output:
#var coords = new Array(new OpenLayers.Geometry.Point((new OpenLayers.LonLat(77.50839149540242, 8.70195705696625).transform(proj4326, proj_current)).lon, (new OpenLayers.LonLat(77.50839149540242, 8.70195705696625).transform(proj4326, proj_current)).lat));
#var popupContentHTML = "<div class='gis_openlayers_popupbox' id='kylig-5'>   <div class='gis_openlayers_popupbox_header'>     <div class='gis_openlayers_popupbox_header_r'>       <div class='gis_openlayers_popupbox_author'><label for='gis_popup_author' >Author:</label> Anonymous</div>       <div class='gis_openlayers_popupbox_date'><label for='gis_popup_date' >Date:</label> 0000-00-00 00:00:00</div>     </div>     <div class='gis_openlayers_popupbox_header_l'>       <div class='gis_openlayers_popupbox_name'><span> </span> ()       </div>     </div>   </div>   <div class='gis_openlayers_popupbox_body'>     <span class='gis_openlayers_popupbox_text'>yreytjtyj</span>  </div>  <div class='gis_openlayers_popupbox_footer'>      <span><a onclick='shn_gis_popup_delete(&#39kylig-5&#39)' alt='delete'><div class='gis_openlayers_popupbox_delete' style='width: 17px; height: 17px;'></div><span>delete</span></a></span>      <span><a onclick='shn_gis_popup_edit_details(&#39kylig-5&#39)' alt='edit'><div class='gis_openlayers_popupbox_edit' style='width: 17px; height: 17px;'></div><span>edit</span></a></span>      <span class='gis_openlayers_popupbox_refreshs'><a onclick='shn_gis_popup_refresh(&#39kylig-5&#39)' alt='refresh'><div class='gis_openlayers_popupbox_refresh' style='width: 17px; height: 17px;'></div><span>refresh</span></a></span>  </div>  <div style='clear: both;'></div></div>";
#var geom = coordToGeom(coords, "point");
#add_Feature_with_popup(featuresLayer, 'outer_kylig-5', geom, popupContentHTML, '');


# Data model:
#db.define_table(table,timestamp,uuidstamp,
#                SQLField('name'),
#                feature_class_id,
#                SQLField('metadata',db.gis_feature_metadata),      # NB This can have issues with sync unless going via CSV
#                SQLField('type',default='point'),
#                SQLField('lat','double'),    # Only needed for Points
#                SQLField('lon','double'),    # Only needed for Points
#                SQLField('wkt',length=256))



# Set id in case any features do not have uuids...
id = 0
# Place each feature
foreach(features as feature):
    
    # Set Feature uuid
    if(isset(feature['f_uuid'])):
        feature_uuid = 'outer_' + feature['f_uuid']
    else:
        # :(
        uuid = 'outer_popup_' + id++
    
    # Set Feature Type
    if(isset(feature['f_type'])):
        type = feature['f_type']
    else:
        type = 'point'
    
    # Generate vars for html popup HTML content
    if(isset(feature['f_class'])):
        feature_class = shn_gis_get_feature_class_uuid(feature['f_class'])
    else:
        feature_class = shn_gis_get_feature_class_uuid(conf['gis_feature_type_default'])
    
    # Set icon
    if(isset(feature['icon'])):
        icon = feature['icon']
    else:
        icon = feature_class['c_icon']
    if(icon == ''):
        fc = shn_gis_get_feature_class_uuid(conf['gis_feature_type_default'])
        icon = fc['c_icon']
    
    # Bit of a hacky way to do it. Especially the transform...
    coordinates = shn_gis_coord_decode(feature['f_coords'])
    coords = ''
    if(count(coordinates) == 1):
         coords += "var coords = new Array(new OpenLayers.Geometry.Point((new OpenLayers.LonLat({coordinates[i][0]}, {coordinates[i][1]}).transform(proj4326, proj_current)).lon, (new OpenLayers.LonLat({coordinates[i][0]}, {coordinates[i][1]}).transform(proj4326, proj_current)).lat));\n"; 
    else:
         coords += "var coords = new Array(";
         ctot = count(coordinates) - 1;
         for(i = 1; i < ctot; i++):
             coords += "new OpenLayers.Geometry.Point((new OpenLayers.LonLat({coordinates[i][0]}, {coordinates[i][1]}).transform(proj4326, proj_current)).lon, (new OpenLayers.LonLat({coordinates[i][0]}, {coordinates[i][1]}).transform(proj4326, proj_current)).lat), ";
         if(ctot > 0):
         coords += "new OpenLayers.Geometry.Point((new OpenLayers.LonLat({coordinates[i][0]}, {coordinates[i][1]}).transform(proj4326, proj_current)).lon, (new OpenLayers.LonLat({coordinates[i][0]}, {coordinates[i][1]}).transform(proj4326, proj_current)).lat)";   
         coords += ");\n"            
        
    # Popup
    html =  "var popupContentHTML = \""
    html += shn_gis_form_popupHTML_view(feature)
    html += "\";\n"
    
    return dict(coords=coords, html=html)

    
def shn_gis_get_feature_class_uuid(fc_uuid):
    "Given a Feature Class UUID, return the other fields"

    record = db(db.gis_feature_class.uuid==fc_uuid).select(db.gis_feature_class.ALL)[0]
    feature_class = {
        'fc_name' : record.name,
        'fc_uuid' : record.uuid,
        'fc_module' : record.module,
        'fc_resource' : record.resource,
        'fc_icon' : record.marker
        }
    return feature_class
   
def shn_gis_coord_decode(coords):
    """ Takes the coord string stored in the db and decodes it into an array of:
    [0 => center of obj][0 => x, 1 => y, 2 => z]
    [1 => plot 1][0 => x, 1 => y, 2 => z]
    [2 => plot 2][0 => x, 1 => y, 2 => z]
    [3 => plot 3][0 => x, 1 => y, 2 => z]
    In the case of a single point (eg 33.54,64.32,0,wkt{POINT Z (33.54 64.32 0)} ) the call would result in:
    [0][0 => 33.54, 1 => 64.32, 2 => 0]
    [1][0 => 33.54, 1 => 64.32, 2 => 0]
    In a line or poly type (e.g. 2,3,0,wkt{POLYGON Z ((1 4 0,5 1 0,5 5 1))} )
    [0][0 => 2, 1 => 3, 2 => 0]
    [1][0 => 1, 1 => 4, 2 => 0]
    [2][0 => 5, 1 => 1, 2 => 0]
    [3][0 => 5, 1 => 5, 2 => 1]
    """
    output = array()
    subcoords = explode(",", coords, 4)
    #2,3,0,wkt{POLYGON Z ((1 4 0,5 1 0,5 5 1))}
    array_push(output, array(subcoords[0], subcoords[1], subcoords[2]))
    # [0][0 => 2, 1 => 3, 2 => 0]
    wkt = subcoords[3]
    # wkt{POLYGON Z ((1 4 0,5 1 0,5 5 1))}
    wkt = ereg_replace("(wkt{|})", "", wkt)
    # POLYGON Z ((1 4 0,5 1 0,5 5 1))
    wkt = explode('(' , wkt, 2)
    # 0 => POLYGON Z   1 => ((1 4 0,5 1 0,5 5 1))
    # if polygons start having inner circles this will need to change
    wkt = ereg_replace("(\(|\))", "", wkt[1])
    # 1 4 0,5 1 0,5 5 1
    wkt = explode(',' , wkt)
    # 0 => 1 4 0   1 => 5 1 0   2 => 5 5 1
    foreach(wkt as point):
        array_push(output, explode(' ' , point, 3) )
    return output
   
   
def shn_gis_form_popupHTML_view(feature):
    "Generate vars for popup HTML content"
        
    # Set Feature uuid
    if(isset(feature['f_uuid']) && feature['f_uuid'] != ''):
        feature_uuid = feature['f_uuid']
    else:
        # :(
        feature_uuid = 'popup_' . id++
    
    # Set Feature Class
    if(isset(feature['f_class']) && feature['f_class'] != ''):
        feature_class = shn_gis_get_feature_class_uuid(feature['f_class'])
    else:
        feature_class = shn_gis_get_feature_class_uuid(conf['gis_feature_type_default'])
    
    # Set name.
    if(isset(feature['f_name']) && feature['f_name'] != ''):
        name = feature['f_name']
    else:
        name = feature_class['c_name']
    
    # Set Description
    if(isset(feature['f_description']) && feature['f_description'] != ''):
        description = feature['f_description']
    else:
        description = feature_class['c_description']
    
    # Set Author
    if(isset(feature['f_author']) && feature['f_author'] != ''):
        author = feature['f_author']
    else:
        author = 'Anonymous'
    
    # Set Address
    if(isset(feature['f_address']) && feature['f_address'] != ''):
        address = feature['f_address']
    else:
        address = false
    
    # Set Event Date
    if(isset(feature['f_event_date'])):
        event_date = feature['f_event_date']
    else:
        event_date = 'Unknown'
    
    # Set View URL
    if(isset(feature['f_url']) && feature['f_url'] != ''):
        url = feature['f_url']
    else:
        url = false
    
    # Set View URL
    if(isset(feature['f_url_view']) && feature['f_url_view'] != ''):
        url_view = feature['f_url_view']
    else:
        url_view = false
    
    # Set Edit URL
    if (isset(feature['f_url_edit']) && feature['f_url_edit'] != ''):
        # if feature has an edit url
        url_edit = feature['f_url_edit']
    elif (isset(feature['f_module_item']) && feature['f_module_item'] != ''):
        # if is registered to a module but has no edit url, should not be editable.
        url_edit = false
    elif (!isset(feature['f_uuid']) || feature['f_uuid'] == ''):
        # if there is no uuid to tie feature being edited too...
        url_edit = false
    else:
        # if feature is not module related and has a uuid to tie changes to. (can edit)
        url_edit = true
    
    # Set Delete URL
    if (isset(feature['f_url_delete']) && feature['f_url_delete'] != ''):
        # if feature has a delete url
        url_del = feature['f_url_delete']
    elif (isset(feature['f_module_item']) && feature['f_module_item'] != ''):
        # if is registered to a module but has no del url, should not be deletable.
        url_del = false
    elif(!isset(feature['f_uuid']) || feature['f_uuid'] == ''):
        # if there is no uuid to tie feature being deleted too...
        url_del = false
    else:
        # if feature is not module related and has a uuid to tie changes to. (can del)
        url_del = true
    
    
    # Popup HTML
    html = ''
    html += "<div class='gis_openlayers_popupbox' id='feature_uuid'>"
    # Header (name, link, date, author, address)
    html += "   <div class='gis_openlayers_popupbox_header'>"
    html += "     <div class='gis_openlayers_popupbox_header_r'>"
    html += "       <div class='gis_openlayers_popupbox_author'><label for='gis_popup_author' >" + str(T("Author:")) + "</label> author</div>"
    html += "       <div class='gis_openlayers_popupbox_date'><label for='gis_popup_date' >" + str(T("Date:")) + "</label> event_date</div>"
    html += "     </div>"
    html += "     <div class='gis_openlayers_popupbox_header_l'>"
    html += "       <div class='gis_openlayers_popupbox_name'><span> name</span> ({feature_class['c_name']})"
    if(!(url === false)){
        html += "      <a href='url' target='_blank'><div class='gis_openlayers_popupbox_link' style='width: 17px; height: 17px;'></div></a>"
    }
    html += "       </div>"
    html += "     </div>"
    if(!(address === false)){
        html += "      <div class='gis_openlayers_popupbox_address'><b>" + str(T("Address:")) + "</b> address</div>"
    }
    html += "   </div>"
    # Body (desc, img, vid)
    html += "   <div class='gis_openlayers_popupbox_body'>"
    html += "     <span class='gis_openlayers_popupbox_text'>description</span>"
    #html +=  "    <span class='gis_openlayers_popupbox_img'><img src=image width=100 height=100></span>"   
    #html +=  "    <span class='gis_openlayers_popupbox_vid'></span>"   
    html += "  </div>"
    # Footer (edit, view)
    html += "  <div class='gis_openlayers_popupbox_footer'>"
    #Options will want to display these based on ACL privileges (also make sure resulting actions are ACLed)
    
    if(url_del === true):
        html += "      <span><a onclick='shn_gis_popup_delete(&#39feature_uuid&#39)' alt='" + str(T("delete")) + "'><div class='gis_openlayers_popupbox_delete' style='width: 17px; height: 17px;'></div><span>" + str(T("delete")) + "</span></a></span>"
    elif(!(url_del === false)):
        html += "      <span><a href='url_del' target='_blank' alt='" + str(T("delete")) + "'><div class='gis_openlayers_popupbox_delete' style='width: 17px; height: 17px;'></div><span>" + str(T("delete")) + "</span></a></span>"   
    else:
        html += "      <span><a onclick='shn_gis_popup_unable()' alt='" + str(T("delete")) + "'><div class='gis_openlayers_popupbox_delete' style='width: 17px; height: 17px;'></div><span>" + str(T("delete")) + "</span></a></span>"   
    
    
   if(url_edit === true):
        html += "      <span><a onclick='shn_gis_popup_edit_details(&#39feature_uuid&#39)' alt='" + str(T("edit")) + "'><div class='gis_openlayers_popupbox_edit' style='width: 17px; height: 17px;'></div><span>" + str(T("edit")) + "</span></a></span>"
    elif(!(url_edit === false)):
        html += "      <span><a href='url_edit' target='_blank' alt='" + str(T("edit")) + "'><div class='gis_openlayers_popupbox_edit' style='width: 17px; height: 17px;'></div><span>" + str(T("edit")) + "</span></a></span> "
    else:
        html += "      <span><a onclick='shn_gis_popup_unable()' alt='" + str(T("edit")) + "'><div class='gis_openlayers_popupbox_edit' style='width: 17px; height: 17px;'></div><span>" + str(T("edit")) + "</span></a></span> " 
    
    if(!(url_view === false)):
        html += "      <span><a href='url_view' target='_blank' alt='" + str(T("view")) + "'><div class='gis_openlayers_popupbox_view' style='width: 17px; height: 17px;'></div><span>" + str(T("view")) + "</span></a></span>"
    
    html += "      <span class='gis_openlayers_popupbox_refreshs'><a onclick='shn_gis_popup_refresh(&#39feature_uuid&#39)' alt='" + str(T("refresh")) + "'><div class='gis_openlayers_popupbox_refresh' style='width: 17px; height: 17px;'></div><span>" + str(T("refresh")) + "</span></a></span>"
    html += "  </div>"
    html += "  <div style='clear: both;'></div>"
    html += "</div>"
        
    return html