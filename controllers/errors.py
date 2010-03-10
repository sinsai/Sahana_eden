# -*- coding: utf-8 -*-

# Error controller implements nicer error pages
module = 'errors'

from gluon.http import defined_status
def index():
    ''' default generic error page '''
    try:
        description = defined_status[int(request.vars['code'])]
    except IndexError:
        description = 'unknown error'
    return dict(res=request.vars, description=description)