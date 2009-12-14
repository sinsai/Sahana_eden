# -*- coding: utf-8 -*-

# Help Menu (available in all screens)
s3.menu_help = [T('Help'), True, URL(request.application, 'default', 'help'), [
        [T('About'), False, URL(request.application, 'default', 'about')],
    ]]

# Auth Menu (available in all screens)
if not auth.is_logged_in():
    try:
        self_registration = db().select(db.s3_setting.self_registration)[0].self_registration
    except:
        self_registration = True
    if self_registration:
        s3.menu_auth = [T('Login'), True, URL(request.application, 'default', 'user/login'),
             [
                    [T('Register'), False,
                     URL(request.application, 'default', 'user/register')],
                    [T('Lost Password'), False,
                     URL(request.application, 'default', 'user/retrieve_password')]]
             ]
    else:
        s3.menu_auth = [T('Login'), True, URL(request.application, 'default', 'user/login'),
             [
                    [T('Lost Password'), False,
                     URL(request.application, 'default', 'user/retrieve_password')]]
             ],
else:
    s3.menu_auth = ['Logged-in as: ' + auth.user.first_name + ' ' + auth.user.last_name, True, None,
         [
                [T('Logout'), False, 
                 URL(request.application, 'default', 'user/logout')],
                [T('Edit Profile'), False, 
                 URL(request.application, 'default', 'user/profile')],
                [T('Change Password'), False,
                 URL(request.application, 'default', 'user/change_password')]]
         ]

# Menu for Admin module
# (defined here as used in several different Controller files)        
admin_menu_options = [
    [T('Settings'), False, URL(r=request, c='admin', f='setting', args=['update', 1]), [
        [T('Edit Themes'), False, URL(r=request, c='admin', f='theme')]
    ]],
    [T('User Management'), False, '#', [
        [T('Users'), False, URL(r=request, c='admin', f='user')],
        [T('Roles'), False, URL(r=request, c='admin', f='group')],
        #[T('Membership'), False, URL(r=request, c='admin', f='membership')]
    ]],
    [T('Database'), False, '#', [
        [T('Import'), False, URL(r=request, c='admin', f='import_data')],
        [T('Export'), False, URL(r=request, c='admin', f='export_data')],
        [T('Raw Database access'), False, URL(r=request, c='appadmin', f='index')]
    ]],
    [T('Synchronisation'), False, URL(r=request, c='sync', f='index'), [
            [T('Sync History'), False, URL(r=request, c='sync', f='history')],
            [T('Sync Partners'), False, URL(r=request, c='sync', f='partner')],
            [T('Sync Settings'), False, URL(r=request, c='sync', f='setting', args=['update', 1])]
    ]],
    [T('Mobile'), False, URL(r=request, c='mobile', f='index'),[
            [T('Modem Settings'), False, URL(r=request, c='mobile', f='setting', args=['update', 1])]
    ]],
    [T('Edit Application'), False, URL(r=request, a='admin', c='default', f='design', args=['sahana'])],
    [T('Functional Tests'), False, URL(r=request, c='static', f='selenium', args=['core', 'TestRunner.html'], vars=dict(test='../tests/TestSuite.html', auto='true', resultsUrl=URL(r=request, c='admin', f='handleResults')))]
]
