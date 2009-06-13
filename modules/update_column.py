# -*- coding: utf-8 -*-

# From http://groups.google.com/group/web2py/msg/9803f6bf92349e32
# currently unused
import re
def update_column(table, argument_col_num=0, target_col_num=-1, pattern="(\d+)", replace_with="A(%(g1)s, _href=URL(r=request, f='show', args=[%(arg)s]))"):
    #pass 'replace_with' as a string like "A(%(g1)s, URL(r=request, f='show', args=[%(arg)s]))"
    #where (g1) means group1 from reg. exp. match (count from 1)
    #      (arg) is value of column number 'argument_col_num'
    regexp = re.compile(pattern)
    tagz = re.compile("<.*?>")
    for i in range(len(table.components[1])):
        target_td = table.components[1][i].components[target_col_num]
        arg_td = table.components[1][i].components[argument_col_num]
        if type(target_td) == type(TD()) and len(target_td.components) > 0 and len(arg_td.components) > 0:
            m = re.match(regexp, str(target_td.components[0]))
            a = re.sub(tagz, '' , str(arg_td.components[0]))
            d = {'arg': a}
            if m:
                for j in range(1, len(m.groups()) + 1): d['g' + str(j)] = m.group(j)
            table.components[1][i].components[target_col_num] = TD(eval(replace_with % d))
    return table

