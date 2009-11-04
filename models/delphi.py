# coding: utf8

module = 'delphi'

# Problem
resource = 'problem'
problem_table = module + '_' + resource
db.define_table(problem_table,
    Field('title', 'string', notnull=True),
    Field('description', 'text'),
    Field('criteria', 'text', notnull=True),
    Field('active', 'boolean', default=True),
    Field('created_by', db.auth_user, writable=False, readable=False),
    Field('last_modification','datetime', default=request.now, writable=False))

db[problem_table].title.label = T('Problem Title')
db[problem_table].title.requires = IS_NOT_IN_DB(db,"%s.title" % problem_table) and IS_NOT_EMPTY()
db[problem_table].created_by.default = auth.user.id if auth.user else 0

def get_last_problem_id():
    last_problems = db(db[problem_table].id>0).select(db[problem_table].id, orderby=~db[problem_table].id, limitby=(0, 1))
    if last_problems: 
        return last_problems[0].id

# Solution Item
resource = 'solution_item'
solution_item_table = module + '_' + resource
db.define_table(solution_item_table,
    Field('problem',db[problem_table], notnull=True),
    Field('title','string'),
    Field('suggested_by', db.auth_user, writable=False, readable=False),
    Field('last_modification','datetime', default=request.now, writable=False))

db[solution_item_table].title.requires = IS_NOT_EMPTY()
db[solution_item_table].suggested_by.default = auth.user.id if auth.user else 0
db[solution_item_table].problem.default = get_last_problem_id()


# Vote
resource = 'vote'
vote_table = module + '_' + resource
db.define_table(vote_table,
    Field('solution_item', db[solution_item_table]),
    Field('rank','integer'),
    Field('user', db.auth_user, writable=False, readable=False),
    Field('last_modification','datetime', default=request.now, writable=False))

db[vote_table].user.default = auth.user.id if auth.user else 0


# Forum
resource = 'forum_post'
forum_post_table = module + '_' + resource
db.define_table(forum_post_table,
    Field('problem',db[problem_table], notnull=True),
    Field('title','string'),
    Field('post', 'text', notnull=True),
    Field('post_html', 'text', default=""),
    Field('user', db.auth_user, writable=False, readable=False),
    Field('last_modification','datetime', default=request.now, writable=False))

db[forum_post_table].user.default = auth.user.id if auth.user else 0
