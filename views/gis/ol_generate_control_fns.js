// Activate Control for navigating around the maps.
function shn_gis_map_control_navigate(){
    shn_gis_map_control_deactivate_all();
    document.getElementById('gis_map_icon_select').style.backgroundImage = "url(res/OpenLayers/theme/default/img/move_feature_on.png)";
    document.getElementById('gis_map_icon_descripion').innerHTML = '<?= _t('Mode: Navigate') ?>';
}
// Activate Control for selecting features.
function shn_gis_map_control_select(){
    shn_gis_map_control_deactivate_all();
    document.getElementById('gis_map_icon_select').style.backgroundImage = "url(res/OpenLayers/theme/default/img/move_feature_on.png)";
    document.getElementById('gis_map_icon_descripion').innerHTML = '<?= _t('Mode: Select') ?>';
    selectControl.activate();
}
// Activate Control for dragging features.
function shn_gis_map_control_drag(){
    shn_gis_map_control_deactivate_all();
    document.getElementById('gis_map_icon_drag').style.backgroundImage = "url(res/OpenLayers/theme/default/img/pan_on.png)";
    document.getElementById('gis_map_icon_descripion').innerHTML = '<?= _t('Mode: Drag') ?>';
    dragControl.activate();
}
// Activate Control for modifying features.
function shn_gis_map_control_modify(){
    shn_gis_map_control_deactivate_all();
    //document.getElementById('gis_map_icon_modify').style.backgroundImage = "url()";
    //document.getElementById('gis_map_icon_descripion').innerHTML = '<?= _t('Mode: Modify') ?>';
    //modifyControl.activate();
}
// Activate Control for adding point features.
function shn_gis_map_control_add_point(){
    shn_gis_map_control_deactivate_all();
    document.getElementById('gis_map_icon_addpoint').style.backgroundImage = "url(res/OpenLayers/theme/default/img/draw_point_on.png)";
    document.getElementById('gis_map_icon_descripion').innerHTML = '<?= _t('Mode: Add Point') ?>';
    pointControl.activate();
}
// Activate Control for adding line features.
function shn_gis_map_control_add_line(){
    shn_gis_map_control_deactivate_all();
    document.getElementById('gis_map_icon_addline').style.backgroundImage = "url(res/OpenLayers/theme/default/img/draw_line_on.png)";
    document.getElementById('gis_map_icon_descripion').innerHTML = '<?= _t('Mode: Add line') ?>';
    lineControl.activate();
}
// Activate Control for adding polygon features.
function shn_gis_map_control_add_polygon(){
    shn_gis_map_control_deactivate_all();
    document.getElementById('gis_map_icon_addpolygon').style.backgroundImage = "url(res/OpenLayers/theme/default/img/draw_polygon_on.png)";
    document.getElementById('gis_map_icon_descripion').innerHTML = '<?= _t('Mode: Add Area') ?>';
    polygonControl.activate();
}
// Activate Control for drawing features freehand.
function shn_gis_map_control_freehand(){
    if(lineControl.handler.freehand){
        document.getElementById('gis_map_icon_freehand').style.backgroundImage = "url(res/OpenLayers/theme/default/img/freehand_off.png)";
        document.getElementById('gis_map_icon_descripion').innerHTML = '<?= _t('Mode: Freehand OFF') ?>';
        lineControl.handler.freehand = false;
        polygonControl.handler.freehand = false;
    } else{
        document.getElementById('gis_map_icon_freehand').style.backgroundImage = "url(res/OpenLayers/theme/default/img/freehand_on.png)";
        document.getElementById('gis_map_icon_descripion').innerHTML = '<?= _t('Mode: Freehand ON') ?>';
        lineControl.handler.freehand = true;
        polygonControl.handler.freehand = true;
    }
}
// Deactivate all other controls
function shn_gis_map_control_deactivate_all(){
    // Turn off navigate
    var nav = document.getElementById('gis_map_icon_select')
    if(nav != null){
        nav.style.backgroundImage = "url(res/OpenLayers/theme/default/img/move_feature_off.png)";
    }
    // Turn off select
    if(selectControl != null){
        selectControl.unselectAll();
        selectControl.deactivate();
        document.getElementById('gis_map_icon_select').style.backgroundImage = "url(res/OpenLayers/theme/default/img/move_feature_off.png)";
    }
    // Turn off drag
    if(dragControl != null){
        dragControl.deactivate();
        document.getElementById('gis_map_icon_drag').style.backgroundImage = "url(res/OpenLayers/theme/default/img/pan_off.png)";
    }
    // Turn off modify
    //if(modifyControl != null){
    //modifyControl.deactivate();
    //}
    // Drop features/popups in progress from a create feature.
    if(currentFeature != null && ((pointControl != null && pointControl.active) || (lineControl != null && lineControl.active) || (polygonControl != null && polygonControl.active))){
        if(currentFeature.popup != null){
            currentFeature.popup.hide();
            currentFeature.popup.destroy(currentFeature.popup);
        }
        featuresLayer.removeFeatures([currentFeature]);
        currentFeature.destroy();
        currentFeature = null;
    }
    // Hide any popup showing and deactivate current feature.
    if(currentFeature != null){
        if(currentFeature.popup != null){
            currentFeature.popup.hide();
        }
        currentFeature = null;
    }
    // Turn off point add
    if(pointControl != null){
        pointControl.deactivate();
        document.getElementById('gis_map_icon_addpoint').style.backgroundImage = "url(res/OpenLayers/theme/default/img/draw_point_off.png)";
    }
    // Turn off line add
    if(lineControl != null){
        lineControl.deactivate();
        document.getElementById('gis_map_icon_addline').style.backgroundImage = "url(res/OpenLayers/theme/default/img/draw_line_off.png)";
    }
    // Turn off polygon add
    if(polygonControl != null){
        polygonControl.deactivate();
        document.getElementById('gis_map_icon_addpolygon').style.backgroundImage = "url(res/OpenLayers/theme/default/img/draw_polygon_off.png)";
    }
}
function shn_gis_map_expand()
{
    var omap = document.getElementById("outer_map");
    var amap = document.getElementById("map");
    var tmap = document.getElementById("gis_map_toolbar");
    var fmap = document.getElementById("gis_map_toolbar_fieldset");
    var expd = document.getElementById("gis_map_icon_expand");
    // If currently small, make big
    if(omap.style.position != 'fixed'){
        expd.style.backgroundImage = "url(res/OpenLayers/theme/default/img/map_resize_in_c.png)";
        amap.style.width = '100%';
        amap.style.height = '100%';
        omap.style.position = 'fixed';
        omap.style.top = '0px';
        omap.style.left = '0px';
        omap.style.width = '100%';
        omap.style.height = '100%';
        omap.style.marginLeft = '0px';
        fmap.style.border = '0px none';
        tmap.style.margin = '0px';
    }
    // If currently big, make small
    else {
        expd.style.backgroundImage = "url(res/OpenLayers/theme/default/img/map_resize_out_c.png)";
        amap.style.width = '<?= $conf['gis_width'] ?>px';
        amap.style.height = '<?= $conf['gis_height'] ?>px';
        omap.style.position = 'relative';
        omap.style.top = 'auto';
        omap.style.left = 'auto';
        omap.style.width = 'auto';
        omap.style.height = 'auto';
        omap.style.marginLeft = '10px';
        fmap.style.border = '1px solid';
        tmap.style.margin = '10px 10px 10px 0px';
    }
}