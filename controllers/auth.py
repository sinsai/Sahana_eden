# -*- coding: utf-8 -*-

def user():
    "Defined in admin module, so redirect there"
    args=request.args
    vars=request.vars
    redirect(URL(r=request, c='admin', args=args, vars=vars))
    
def group():
    "Defined in admin module, so redirect there"
    args=request.args
    vars=request.vars
    redirect(URL(r=request, c='admin', args=args, vars=vars))
    
def membership():
    "Defined in admin module, so redirect there"
    args=request.args
    vars=request.vars
    redirect(URL(r=request, c='admin', args=args, vars=vars))
    