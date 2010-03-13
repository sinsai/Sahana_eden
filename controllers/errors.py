# -*- coding: utf-8 -*-
# HTTP Error handler -- implements nicer error pages
# 

# TODO: add/replace the following to your routes.py in web2py directory
#   routes_onerror = [
#       ('sahana/401', '/sahana/default/user/login'),
#       ('sahana/400', '/sahana/errors/e400'),
#       ('sahana/403', '/sahana/errors/e403'),
#       ('sahana/404', '/sahana/errors/e404'),
#       ('sahana/500', '/sahana/errors/e500'),
#       ('sahana/502', '/sahana/errors/e502'),
#       ('sahana/503', '/sahana/errors/e503'),
#       ('sahana/504', '/sahana/errors/e504'),
#       ('sahana/*', '/sahana/errors/index'),
#   ]
# NOTE: if sahana is installed elsewhere or exists under different name in applications folder,
#       just rename it in above list.

module = 'errors'

from gluon.http import defined_status
response.extra_styles = ['S3/errorpages.css']

def index():
    ''' default generic error page '''
    print foo
    try:
        code = request.vars['code']
        description = defined_status[int(code)]
    except KeyError:
        description = 'unknown error'
        code='NA'
        
    details = " %s, %s " % (code, description)
    message = "Oops! Something went wrong..."   
    suggestions = []
    app=request.application
    
    return dict(res=request.vars, message=message, details=details, suggestions=suggestions, app=app)


def e400():
    ''' 400 Bad Request error page '''
    message = "Sorry, I could not understand your request"
    details = "400 BAD REQUEST"
    suggestions = ['Check for errors in the URL, maybe the address was mistyped.']
    app=request.application
    return dict(res=request.vars, message=message, details=details, suggestions=suggestions, app=app)
    
def e403():
    ''' 403 Forbidden '''
    message = "Sorry, that page is forbidden for some reason."
    details = "403 FORBIDDEN"
    suggestions = [
                    'Check if the URL is pointing to a directory instead of a webpage.',
                    'Check for errors in the URL, maybe the address was mistyped.'
                    ]
    app=request.application
    return dict(res=request.vars, message=message, details=details, suggestions=suggestions, app=app)

def e404():
    ''' 404 Not Found '''
    message = "Sorry, we couldn't find that page."
    details = "404 NOT FOUND"
    suggestions = [
                    'Try checking the URL for errors, maybe it was mistyped.',
                    'Try refreshing the page or hitting the back button on your browser.',
                    ]
    app=request.application
    return dict(res=request.vars, message=message, details=details, suggestions=suggestions, app=app)

def e500():
    ''' 500 Internal Server Error '''
    message = "Oops! something went wrong on our side."
    details = "500 INTERNAL SERVER ERROR"
    suggestions = [
                    'Try hitting refresh/reload button or trying the URL from the address bar again.',
                    'Please come back after sometime if that doesn\'t help.',
                    ]
    app=request.application
    return dict(res=request.vars, message=message, details=details, suggestions=suggestions, app=app)

def e502():
    ''' 502 Bad Gateway '''
    message = "Sorry, something went wrong."
    details = "502 BAD GATEWAY"
    suggestions = [
                    'The server received an incorrect response from another server that it was accessing to fill the request by the browser.',
                    'Hit the back button on your browser to try again.',
                    'Come back later.'
                    ]
    app=request.application
    return dict(res=request.vars, message=message, details=details, suggestions=suggestions, app=app)
    
def e503():
    ''' 503 Service Unavailable '''
    message = "Sorry, that service is temporary unavailable."
    details = "503 SERVICE UNAVAILABLE"
    suggestions = [
                    'This might be due to a temporary overloading or maintenance of the server.',
                    'Hit the back button on your browser to try again.',
                    'Come back later.'
                    ]
    app=request.application
    return dict(res=request.vars, message=message, details=details, suggestions=suggestions, app=app)

def e504():
    ''' 504 Gateway Timeout '''
    message = "Sorry, things didn't get done on time."
    details = "503 SERVICE UNAVAILABLE"
    suggestions = [
                    'The server did not receive a timely response from another server that it was accessing to fill the request by the browser.',
                    'Hit the back button on your browser to try again.',
                    'Come back later. Everyone visiting this site is probably experiencing the same problem as you.'
                    ]
    app=request.application
    return dict(res=request.vars, message=message, details=details, suggestions=suggestions, app=app)
