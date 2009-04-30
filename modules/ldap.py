#import ldap, ldap.sasl
import ldap
import sys, getpass
from gluon.html import *
from gluon.tools import Auth

class AuthLDAP(Auth):
    def __init__(self, environment, db=None):
        "Initialise parent class & make any necessary modifications"
        Auth.__init__(self,environment,db)
        self.settings.ldap_server = "localhost"
        self.settings.ldap_port = "389"
        self.settings.ldap_basedn = "ou=users,dc=domain,dc=com"
        
    def login(self):
        request = self.environment.request
        session = self.environment.session
        form=FORM('username:',INPUT(_name='username'),
            'password:',INPUT(_name='password',_type='password'),
            INPUT(_type='submit',_value='login'))
        if form.accepts(request.vars, session):
            try:
                con = ldap.initialize("ldap://"+self.settings.ldap_server+":"+self.settings.ldap_port)
                #auth_tokens = ldap.sasl.digest_md5(form.vars.username, reqest.vars.password)
                #con.sasl_interactive_bind_s("", auth_tokens)
                dn = "uid="+form.vars.username+","+self.settings.ldap_basedn
                con.simplebind(dn, reqest.vars.password)
                con.unbind()
                user = self.settings.table_user
                users = self.db (user.username==form.vars.username).select()
                if not users:
                    user_id = user.insert(username=form.vars.username, password=form.vars.username)
                    group_id = self.add_group('user_%i' % user_id)
                    self.add_membership(group_id, user_id)
                    user = user.filter_fields(user[user_id],id=True)
                else:
                    user = user.filter_fields(users[0],id=True)
                self.user = user
                session.auth = Storage(user=user, last_visit=request.now, expiration=self.settings.expiration)
                session.flash = self.messages.logged_in
                log = self.settings.login_log
                if log:
                    self.log_event(log % self.user)
                if onaccept:
                    onaccept(form)
                if not next:
                    next = URL(r=request)
                elif next and not next[0] == '/' and next[:4] != 'http':
                    next = URL(r=request, f=next.replace('[id]', str(form.vars.id)))
                redirect(next)
            except ldap.LDAPError, e:
                print e.message['info']
                if type(e.message) == dict and e.message.has_key('desc'):
                    print e.message['desc']
                else:
                    print e
        return dict(form=form)
