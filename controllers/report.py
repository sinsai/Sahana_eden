import simplejson as json
graph = local_import ('savage.graph')


module = request.controller

response.menu_options = [
    [T('Get'), False, URL (r = request, f = 'scatter', args = 'get')],
]


def scatter():
    resource = request.function
    vars = {}

    def prep (r, vars):
        print r.response.view
        if request.vars.has_key ('id'):
            vars['id'] = int (request.vars['id'])
        else:
            vars['id'] = None

        if r.request.vars.has_key ('data'):
            vars['data'] = json.loads (r.request.vars['data'])

            # You can provide data a interlaced points, or as parallel arrays
            if vars['data'].has_key ('points'):
                xlist = []
                ylist = []
                nlist = []
                for point in vars['data']['points']:
                    if len (point) == 2:
                        xlist.append (point[0])
                        ylist.append (point[1])

                    elif len(point) == 3:
                        nlist.append (point[0])
                        xlist.append (point[1])
                        ylist.append (point[2])

                    else:
                        return False

                vars['data']['x'] = xlist
                vars['data']['y'] = ylist
                if len (nlist) > 0:
                    vars['data']['names'] = nlist

            # Mismatched x and y data lengths are bad
            if len (vars['data']['x']) != len (vars['data']['y']):
                return False

            # Names are optional, but if they are provided, the data should be
            # the same length as the data
            if vars['data'].has_key ('names'):
                if len (vars['data']['x']) != len (vars['data']['names']):
                    return False
            else:
                vars['data']['names'] = []

            # Title, xlabel, and ylabel are all optional
            if not vars['data'].has_key ('title'):
                vars['data']['title'] = None

            if not vars['data'].has_key ('xlabel'):
                vars['data']['xlabel'] = None

            if not vars['data'].has_key ('ylabel'):
                vars['data']['ylabel'] = None

        if r.request.vars.has_key ('settings'):
            vars['settings'] = json.loads (r.request.vars['settings'])
        else:
            vars['settings'] = {}

        return True


    def postp (r, output):
        r.response.view = '%s/%s_%s.%s' % (module, resource, r.method, r.representation)
        return output


    response.s3.prep = lambda r, vars=vars: prep(r, vars)
    response.s3.postp = postp

    return shn_rest_controller (module, resource, vars = vars)


"""def shn_report_scatter_create(r, **attr):
    vars = attr['vars']
    data = vars['data']
    if r.representation == 'svg':
        plot = graph.ScatterPlot (settings = vars['settings'])
        if data.has_key ('title'):
            plot.setTitle (data['title'])
        if data.has_key ('xlabel'):
            plot.setXLabel (data['xlabel'])
        if data.has_key ('ylabel'):
            plot.setYLabel (data['ylabel'])

        map (plot.addPoint, data['x'], data['y'], data['names'])

        r.response.headers['Content-Type'] = 'image/svg+xml'
        return plot.save ()
    else:
        raise HTTP (501, '501')"""
