import simplejson as json

module = "report"

#if deployment_settings.has_module (module):
if True:
    resource = 'scatter'
    tablename = '%s_%s' % (module, resource)
    table = db.define_table (tablename,
                             Field ('title', 'string'),
                             Field ('xlabel', 'string'),
                             Field ('ylabel', 'string'),
                             Field ('x', 'string'),
                             Field ('y', 'string'),
                             Field ('names', 'string'),
                             Field ('settings', 'string'),
                             Field ('dscript', 'string'),
    )


    def scatter_plot (data, settings):
        plot = graph.ScatterPlot (settings = settings)
        if data['title']:
            plot.setTitle (data['title'])
        if data['xlabel']:
            plot.setXLabel (data['xlabel'])
        if data['ylabel']:
            plot.setYLabel (data['ylabel'])
        map (plot.addPoint, data['x'], data['y'], data['names'])
        return plot.save ()


    def shn_report_scatter_get (r, **attr):
        id = attr['vars']['id']

        if id:

            entry = db (db.report_scatter.id == id).select ()[0]
            data = {}
            data['title'] = entry['title']
            data['xlabel'] = entry['xlabel']
            data['ylabel'] = entry['ylabel']
            if entry['names']:
                data['names'] = json.loads (entry['names'])
            else:
                data['names'] = []
            if entry['settings']:
                settings = json.loads (entry['settings'])
            else:
                settings = None
            data['x'] = json.loads (entry['x'])
            data['y'] = json.loads (entry['y'])

            if r.representation == 'svg':
                r.response.headers['Content-Type'] = 'image/svg+xml'
                return scatter_plot (data, settings)
            else:
                r.response.headers['Content-Type'] = 'text/html'
                return {'points': zip (data['x'], data['y']),
                        'settings': settings}

        else:
            rows = [TR (TD(), TD ('Title'), TD ('Description'))]
            for entry in db().select (db.report_scatter.ALL):
                rows.append (TR (TD (A ('View', _href = ('get.svg?id=' + str(entry['id'])))),
                                 TD (entry['title']),
                                 TD (entry['dscript'])))
            return {'graphs': TABLE (*rows)}

    def shn_report_scatter_view (r, **attr):
        if r.representation == 'svg':
            r.response.headers['Content-Type'] = 'image/svg+xml'

            data = attr['vars']['data']
        
            if attr['vars'].has_key ('settings'):
                settings = attr['vars']['settings']
            else:
                settings = {}

            return scatter_plot (data, settings)
        else:
            raise HTTP (501, '501')


    def shn_report_scatter_create (r, **attr):
        rep = r.representation
        r.representation = 'html'

        data = attr['vars']['data']
        
        if attr['vars'].has_key ('settings'):
            settings = json.dumps (attr['vars']['settings'])
        else:
            settings = None


        xstorage = json.dumps (data['x'])
        ystorage = json.dumps (data['y'])
        nstorage = json.dumps (data['names'])
        id = db.report_scatter.insert (x = xstorage,
                                       y = ystorage,
                                       names = nstorage,
                                       title = data['title'],
                                       xlabel = data['xlabel'],
                                       ylabel = data['ylabel'],
                                       settings = settings)

        return {'graphId': str(int(id)),
                'graphRep': rep}


    def shn_report_scatter_delete (r, **attr):
        id = attr['vars']['id']
        db (db.report_scatter.id == id).delete ()
        r.next = "/" + r.request.application


    s3xrc.model.set_method (module, resource, method="get", action=shn_report_scatter_get)
    s3xrc.model.set_method (module, resource, method="create", action=shn_report_scatter_create)
    s3xrc.model.set_method (module, resource, method="delete", action=shn_report_scatter_delete)
    s3xrc.model.set_method (module, resource, method="view", action=shn_report_scatter_view)
