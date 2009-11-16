# coding: utf8

module = 'delphi'
# Current Module (for sidebar title)
module_name = db(db.s3_module.name==module).select()[0].name_nice

response.menu_options = [
    [T("Active Problems"), False, URL(r=request, f='index')],
]

if auth.has_membership(1):
    response.menu_options.extend([
        [T('New Problem'), False, URL(r=request, f='problem', args='create')],
    ])


UNIT_NORMAL = (
    ( 0.0, .0, .01, .02, .03, .04, .05, .06, .07, .08, .09 ),
    ( .0, .5000, .5040, .5080, .5120, .5160, .5199, .5239, .5279, .5319, .5359 ),
    ( .1, .5398, .5438, .5478, .5517, .5557, .5596, .5636, .5675, .5714, .5753 ),
    ( .2, .5793, .5832, .5871, .5910, .5948, .5987, .6026, .6064, .6103, .6141 ),
    ( .3, .6179, .6217, .6255, .6293, .6331, .6368, .6406, .6443, .6480, .6517 ),
    ( .4, .6554, .6591, .6628, .6664, .6700, .6736, .6772, .6808, .6844, .6879 ),
    
    ( .5, .6915, .6950, .6985, .7019, .7054, .7088, .7123, .7157, .7190, .7224 ),
    ( .6, .7257, .7291, .7324, .7357, .7389, .7422, .7454, .7486, .7517, .7549 ),
    ( .7, .7580, .7611, .7642, .7673, .7703, .7734, .7764, .7794, .7823, .7852 ),
    ( .8, .7881, .7910, .7939, .7967, .7995, .8023, .8051, .8078, .8106, .8133 ),
    ( .9, .8159, .8186, .8212, .8238, .8264, .8289, .8315, .8340, .8365, .8389 ),
    
    ( 1.0, .8415, .8438, .8461, .8485, .8508, .8531, .8554, .8577, .8509, .8621 ),
    ( 1.1, .8643, .8665, .8686, .8708, .8729, .8749, .8770, .8790, .8810, .8830 ),
    ( 1.2, .8849, .8869, .8888, .8907, .8925, .8944, .8962, .8980, .8997, .90147 ),
    ( 1.3, .90320, .90490, .90658, .90824, .90988, .91149, .91309, .91466, .91621, .91774 ),
    ( 1.4, .91924, .92073, .92220, .92364, .92507, .92647, .92785, .92922, .93056, .93189 ),
    
    ( 1.5, .93319, .93448, .93574, .93699, .93822, .93943, .94062, .94179, .94295, .94408 ),
    ( 1.6, .94520, .94630, .94738, .94845, .94950, .95053, .95154, .95254, .95352, .95449 ),
    ( 1.7, .95543, .95637, .95728, .95818, .95907, .95994, .96080, .96164, .96246, .96327 ),
    ( 1.8, .96407, .96485, .96562, .96638, .96712, .96784, .97856, .96926, .96995, .97062 ),
    ( 1.9, .97128, .97193, .97257, .97320, .97381, .97441, .97500, .97558, .97615, .97670 ),
    
    ( 2.0, .97725, .97778, .97831, .97882, .97932, .97982, .98030, .98077, .98124, .98169 ),
    ( 2.1, .98214, .98257, .98300, .98341, .98382, .98422, .98461, .98500, .98537, .98574 ),
    ( 2.2, .98610, .98645, .98679, .98713, .98745, .98778, .98809, .98840, .98870, .98899 ),
    ( 2.3, .98928, .98956, .98983, .990097, .990358, .990613, .990863, .991106, .991344, .991576 ),
    ( 2.4, .991802, .992024, .992240, .992451, .992656, .992857, .993053, .993244, .993431, .993613 ),
    
    ( 2.5, .993790, .993963, .994132, .994297, .994457, .994614, .994766, .994915, .995060, .995201 ),
    ( 2.6, .995339, .995473, .995604, .995731, .995855, .995975, .996093, .996207, .996319, .996427 ),
    ( 2.7, .996533, .996636, .996736, .996833, .996928, .997020, .997110, .997197, .997282, .997365 ),
    ( 2.8, .997445, .997523, .997599, .997673, .997744, .997814, .997882, .997948, .998012, .998074 ),
    ( 2.9, .998134, .998193, .998250, .998305, .998359, .998411, .998460, .998511, .998559, .998605 ),
    
    ( 3.0, .998650, .998694, .998736, .998777, .998817, .998856, .998893, .998930, .998965, .998999 ),
    ( 3.1, .9990324, .9990646, .9990957, .9991260, .9991553, .9991836, .9992112, .9992378, .9992636, .9992886 ),
    ( 3.2, .9993129, .9993363, .9993590, .9993810, .9994024, .9994230, .9994429, .9994623, .9994810, .9994991 ),
    ( 3.3, .9995166, .9995335, .9995499, .9995658, .9995811, .9995959, .9996103, .9996242, .9996376, .9996505 ),
    ( 3.4, .9996631, .9996752, .9996869, .9996982, .9997091, .9997197, .9997299, .9997398, .9997493, .9997585 ),
    
    ( 3.5, .9997674, .9997759, .9997842, .9997922, .9997999, .9998074, .9998146, .9998215, .9998282, .9998347 ),
    ( 3.6, .9998409, .9998469, .9998527, .9998583, .9998637, .9998689, .9998739, .9998787, .9998834, .9998879 ),
    ( 3.7, .9998922, .9998964, .99990039, .99990426, .99990799, .99991158, .99991504, .99991838, .99992159, .99992468 ),
    ( 3.8, .99992765, .99993052, .99993327, .99993593, .99993848, .99994094, .99994331, .99994558, .99994777, .99994988 ),
    ( 3.9, .99995190, .99995385, .99995573, .99995753, .99995926, .99996092, .99996253, .99996406, .99996554, .99996696 ),
    
    ( 4.0, .99996833, .99996964, .99997090, .99997211, .99997327, .99997439, .99997546, .99997649, .99997748, .99997843 ),
    ( 4.1, .99997934, .99998022, .99998106, .99998186, .99998263, .99998338, .99998409, .99998477, .99998542, .99998605 ),
    ( 4.2, .99998665, .99998723, .99998778, .99998832, .99998882, .99998931, .99998978, .999990226, .999990655, .999991066 ),
    ( 4.3, .999991460, .999991837, .999992199, .999992545, .999992876, .999993193, .999993497, .999993788, .999994066, .999994332 ),
    ( 4.4, .999994587, .999994831, .999995065, .999995288, .999995502, .999995706, .999995902, .999996089, .999996268, .999996439 ),
    
    ( 4.5, .999996602, .999996759, .999996908, .999997051, .999997187, .999997318, .999997442, .999997561, .999997675, .999997784 ),
    ( 4.6, .999997888, .999997987, .999998081, .999998172, .999998258, .999998340, .999998419, .999998494, .999998566, .999998634 ),
    ( 4.7, .999998699, .999998761, .999998821, .999998877, .999998931, .999998983, .9999990320, .9999990789, .9999991235, .9999991661 ),
    ( 4.8, .9999992067, .9999992453, .9999992822, .9999993173, .9999993508, .9999993827, .9999994131, .9999994420, .9999994696, .9999994958 ),
    ( 4.9, .9999995208, .9999995446, .9999995673, .9999995889, .9999996094, .9999996289, .9999996475, .9999996652, .9999996821, .9999996981 )
)
MIN_COLOR = (0xfc, 0xaf, 0x3e)
MAX_COLOR = (0x4e, 0x9a, 0x06)


def lookupTable(mp):
    unitValue = 0.0
    
    for j in range(1, 50):
        if mp == UNIT_NORMAL[j][1]:
            unitValue = UNIT_NORMAL[j][0]
        elif (UNIT_NORMAL[j][1] < mp) and (mp < UNIT_NORMAL[j + 1][1]):
            for i in range(2, 11):
                if (UNIT_NORMAL[j][i - 1] < mp) and (mp <= UNIT_NORMAL[j][i]):
                    unitValue = UNIT_NORMAL[j][0] + UNIT_NORMAL[0][i]
            if mp > UNIT_NORMAL[j][10]:
                unitValue = UNIT_NORMAL[j + 1][0]
    
    if (mp > UNIT_NORMAL[50][1]) and (mp < UNIT_NORMAL[50][10]):
        for i in range(2, 11):
            if (UNIT_NORMAL[50][i - 1] < mp) and (mp <= UNIT_NORMAL[50][i]):
                unitValue = UNIT_NORMAL[50][0] + UNIT_NORMAL[0][i];
    
    if mp > UNIT_NORMAL[50][10]:
        unitValue = 5.0; # suppose infinite value occur
    
    return unitValue


def index():
    latest_problems = db(db.delphi_problem.active==True).select(orderby=~db.delphi_problem.last_modification)
    return dict(latest_problems=latest_problems, title="Active Problems",
                module_name=module_name)

def problem():
    return shn_rest_controller(module, 'problem', list_fields=['title', 'created_by', 'last_modification'])

def solution_item():
    return shn_rest_controller(module, 'solution_item', list_fields=['problem', 'title', 'suggested_by', 'last_modification'])

def summary():
    problem_id = request.args(0)
    pr = db.delphi_problem[problem_id]
    if not pr: raise HTTP(404)
    authorised = shn_has_permission("update", db.delphi_problem, problem_id) and auth.has_membership(1)
    user = db.auth_user[auth.user.id] if (auth.is_logged_in() and session.auth) else 0
    can_vote = user is not 0
    voted = user.delphi_vote.select() if user else False
    
    if can_vote and 'item_title' in request.post_vars:
        db.delphi_solution_item.insert(problem=pr, title=request.post_vars['item_title'])
    
    return dict(problem=pr, items=pr.delphi_solution_item.select(),
                authorised=authorised, can_vote=can_vote, voted=voted, title="Options")


def vote():
    def check(i, j):
        if ('v_%d_%d' % (i, j) in request.post_vars) and \
            request.post_vars['v_%d_%d' % (i, j)] == "+":
            return True
        if ('v_%d_%d' % (j, i) in request.post_vars) and \
            request.post_vars['v_%d_%d' % (j, i)] == "-":
            return True
        return False
    
    problem_id = request.args(0)
    pr = db.delphi_problem[problem_id]
    if not pr: raise HTTP(404)
    authorised = shn_has_permission("update", db.delphi_problem, problem_id) and auth.has_membership(1)
    user = db.auth_user[auth.user.id] if (auth.is_logged_in() and session.auth) else 0
    can_vote = user is not 0
    voted = user.delphi_vote.select() if user else False
    if can_vote and 'submit' in request.post_vars:
        items = []
        for si1 in pr.delphi_solution_item.select():
            items.append(si1)
        n = len(items)
        for i in range(n):
            top = i
            for j in range(i+1, n):
                if check(items[j].id, items[top].id):
                    top = j
            items[i], items[top] = items[top], items[i]
        
        #FIXME: User's selection will be disappeared if there is an error
        error = False
        for i in range(n):
            for j in range(i+1, n):
                if check(items[j].id, items[i].id):
                    session.error = T('There is a loop in the priority list you have submited!')
                    redirect(URL(r=request, f='summary', args=problem_id))    
                    error = True
                if not check(items[i].id, items[j].id):
                    session.error = T("You haven't completed all the available pairs!")
                    redirect(URL(r=request, f='summary', args=problem_id))    
                    error = True
        
        if not error:
            if voted:
                for old in voted:
                    del db.delphi_vote[old.id]
            for i in range(n):
                db.delphi_vote.insert(solution_item=items[i].id, rank=i+1)
            voted = user.delphi_vote.select(db.delphi_vote.solution_item, db.delphi_vote.rank)
    
    if voted:
        voted = dict([(v.solution_item, v.rank) for v in voted])
    pairs = []
    for si1 in pr.delphi_solution_item.select():
        for si2 in pr.delphi_solution_item(db.delphi_solution_item.id>si1.id).select():
            pairs.append((si1, si2, voted and (si1.id in voted) and (si2.id in voted) and (voted[si1.id] < voted[si2.id] and 1 or 2)))
    return dict(problem=pr, pairs=pairs,
                authorised=authorised, can_vote=can_vote, voted=voted, title="Vote")


def status():
    problem_id = request.args(0)
    pr = db.delphi_problem[problem_id]
    user = db.auth_user[auth.user.id] if (auth.is_logged_in() and session.auth) else 0
    can_view = True
    
    votes = {}
    items = dict([(i.id, i.title) for i in pr.delphi_solution_item.select()])
    i_ids = items.keys()
    n = len(i_ids)
    users = db(db.auth_user.id>0).select()
    num_users = len(users)
    
    if n == 0:
        return dict(problem=pr, can_view=can_view, items=items, beans=[],
                    votes=votes, scale={}, title="Scale of Results", 
                    num_users=num_users, num_voted=0, worst=[], best=[])
    
    for i1 in i_ids:
        for i2 in i_ids:
            votes[(i1, i2)] = 0
    num_voted = 0
    for u in users:
        u_votes = [v.solution_item for v in u.delphi_vote.select(db.delphi_vote.solution_item) if db.delphi_solution_item[v.solution_item].problem == pr.id] # FIXME
        if u_votes: num_voted += 1
        for i1 in range(len(u_votes)):
            for i2 in range(i1+1, len(u_votes)):
                votes[(u_votes[i1], u_votes[i2])] += 1
    scale = {}
    worst = {}
    best = {}
    tt = float(num_users)
    tt2 = float(num_voted)
    for i1 in i_ids:
        scale[i1] = worst[i1] = best[i1] = 0
        for i2 in i_ids:
            if i1 == i2 or tt == 0:
                continue
            if votes[(i1, i2)] > votes[(i2, i1)]:
                scale[i1] += lookupTable(votes[(i1, i2)]/tt2)
            else:
                scale[i1] -= lookupTable(votes[(i2, i1)]/tt2)

            not_voted = num_users - votes[(i1, i2)] - votes[(i2, i1)]
            b_votes = num_users - votes[(i2, i1)]
            if b_votes > votes[(i2, i1)]:
                best[i1] += lookupTable(b_votes/tt)
            else:
                best[i1] -= lookupTable(votes[(i2, i1)]/tt)
            
            w_votes = num_users - votes[(i1, i2)]
            if votes[(i1, i2)] > w_votes:
                worst[i1] += lookupTable(votes[(i1, i2)]/tt)
            else:
                worst[i1] -= lookupTable(w_votes/tt)

    def cc(i1, i2):
        if scale[i1] > scale[i2]: return -1
        if scale[i1] < scale[i2]: return +1
        return 0
    
    i_ids.sort(cc)

    beans_num = int((n+1) * 2)
    bean_size = 10.0 * n / beans_num
    beans = []
    i = 0
    for j in range(beans_num):
        color = "%02x%02x%02x" % tuple([int(((j*MIN_COLOR[k]) + ((beans_num-j)*MAX_COLOR[k])) / beans_num) for k in (0, 1, 2)])
        limit = ((beans_num - j - 1) * bean_size) - (5 * n)
        bean = []
        while i < n and scale[i_ids[i]] >= limit:
            bean.append(i_ids[i])
            i += 1
        beans.append((color, bean))


    return dict(problem=pr, can_view=can_view, items=items, beans=beans,
                scale=scale,
                title="Scale of Results", num_users=num_users,
                votes=votes, is_admin=auth.has_membership(1),
                num_voted=num_voted, worst=worst, best=best)


def discuss():
    problem_id = request.args(0)
    pr = db.delphi_problem[problem_id]
    user = db.auth_user[auth.user.id] if (auth.is_logged_in() and session.auth) else 0
    can_post = user is not 0
    
    form=SQLFORM(db.delphi_forum_post, 
        fields=['title', 'post'],
        labels=dict(post="%s %s:" % (user.first_name, user.last_name)))
    if can_post and form.accepts(request.post_vars,session):
        post = request.post_vars['post']
        title = request.post_vars['title']
        post_html = ""
        k = -1
        for l in post.split("\n"):
            l = l.strip()
            old = k
            k = 0
            while k<len(l) and l[k] == '>':
                k += 1
            if k != old:
                if old > 0:
                    post_html += "</blockquote>"
                else:
                    post_html += "</p>"
                if k > 0:
                    post_html += "<blockquote class='delphi_q%d'>" % k
                else:
                    post_html += "<p>"
            else:
                post_html += "<br/>"
            post_html += l[k:]
        if k > 0:
            post_html += "</blockquote>"
        db.delphi_forum_post.insert(title=title, problem=pr, post=post, post_html=post_html)
        response.flash='your post was added successfully.'
    elif form.errors:
        response.error='there are errors'

    return dict(problem=pr, can_post=can_post, user=user, 
                form=form, title="Discussion Forum")
