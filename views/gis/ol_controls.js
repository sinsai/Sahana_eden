// No need to duplicate this functionality - done nicer by GeoExt
//map.addControl(new OpenLayers.Control.LayerSwitcher());

// Small one already present & takes up less space
//map.addControl(new OpenLayers.Control.PanZoomBar());

map.addControl(new OpenLayers.Control.ScaleLine());
//map.addControl(new OpenLayers.Control.MousePosition());
map.addControl(new OpenLayers.Control.MGRSMousePosition());
map.addControl(new OpenLayers.Control.Permalink());
map.addControl(new OpenLayers.Control.OverviewMap({mapOptions: options}));
popupControl = new OpenLayers.Control.SelectFeature(allLayers);
map.addControl(popupControl);
popupControl.activate();

{{if mgrs:}}
// MGRS
var selectPdfControl = new OpenLayers.Control();
OpenLayers.Util.extend( selectPdfControl, {
    draw: function () {
        this.box = new OpenLayers.Handler.Box( this, {
                "done": this.getPdf
            });
        this.box.activate();
        },
    response: function(req) {
        this.w.destroy();
        var gml = new OpenLayers.Format.GML();
        var features = gml.read(req.responseText);
        var html = features.length + " pdfs. <br /><ul>";
        if (features.length) {
            for (var i = 0; i < features.length; i++) {
                var f = features[i];
                var text = f.attributes.utm_zone + f.attributes.grid_zone + f.attributes.grid_square + f.attributes.easting + f.attributes.northing;
                html += "<li><a href='" + features[i].attributes.url + "'>" + text + "</a></li>";
            }
        }
        html += "</ul>";
        //console.log(html);
        this.w = new Ext.Window({
            'html': html,
            width: 300,
            'title': 'Results',
            height: 200
        });
        this.w.show();
    },
    getPdf: function (bounds) {
        var ll = map.getLonLatFromPixel(new OpenLayers.Pixel(bounds.left, bounds.bottom)).transform(projection_current, proj4326);
        //console.log(ll);
        var ur = map.getLonLatFromPixel(new OpenLayers.Pixel(bounds.right, bounds.top)).transform(projection_current, proj4326);
        var boundsgeog = new OpenLayers.Bounds(ll.lon, ll.lat, ur.lon, ur.lat);
        bbox = boundsgeog.toBBOX();
        //console.log(bbox);
        OpenLayers.Request.GET({
            url: '{{=XML(mgrs.url)}}&bbox=' + bbox,
            callback: OpenLayers.Function.bind(this.response, this)
        });
        this.w = new Ext.Window({
            'html':"Searching {{=mgrs.name}}, please wait.",
            width: 200,
            'title': "Please Wait."
            });
        this.w.show();
    }
});
{{pass}}
