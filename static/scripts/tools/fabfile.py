from __future__ import with_statement
from fabric.api import *
import pexpect
#import urllib2

#
# http://eden.sahanafoundation.org/wiki/PakistanDeploymentCycle
#

env.key_filename = ["/home/release/.ssh/sahana_release"]

# Definitions for 'Test' infrastructure
def test():
    """ List of server(s) for test infratructure """
    env.user = "root"
    env.hosts = ["test.eden.sahanafoundation.org"]

# Definitions for 'Production' infrastructure
def prod():
    """ List of server(s) for production infrastructure """
    env.user = "root"
    env.hosts = ["pakistan.sahanafoundation.org"]


# Key distribution and management
def generate_keys():
    """ Generate an SSH key to be used for password-less control """
    local("ssh-keygen -N '' -q -t rsa -f ~/.ssh/sahana_release")

def distribute_keys():
    """ Distribute keys to servers - requires preceding with 'test' or 'prod' """
    local("ssh-copy-id -i ~/.ssh/sahana_release.pub %s@%s" % (env.user, env.host))
#
# Deployment, Maintenance and Migrations
#

def deploy():
    """
        Perform the full upgrade cycle
        - requires preceding with 'test' or 'prod'
    """
    maintenance_on()
    migrate_on()
    db_sync()
    pull()
    cleanup()
    migrate()
    migrate_off()
    maintenance_off()

def cleanup():
    """ Cleanup after the bzr pull """
    with cd("/home/web2py/applications/eden/"):
        run("chown web2py:web2py languages/*", pty=True)
        # ToDo: Extend to all conflicts (models at least)
        # ToDo: Provide more comforting output (an error here is good!)
        run("mv models/000_config.py.THIS models/000_config.py", pty=True)

def db_sync():
    """ Synchronise the Database """
    if not "test" in env.host:
        pass
    else:
        # ToDo: Pull database from Live
        pass

def maintenance_on():
    """ Enable maintenance mode """
    # ToDo Disable Cron
    run("a2dissite %s" % env.host, pty=True)
    run("a2ensite maintenance", pty=True)
    reload()

def maintenance_off():
    """ Disable maintenance mode """
    # ToDo Enable Cron
    run("a2dissite maintenance", pty=True)
    run("a2ensite %s" % env.host, pty=True)
    reload()

def migrate_on():
    """ Enabling migrations """
    with cd("/home/web2py/applications/eden/models/"):
        run("sed -i 's/deployment_settings.base.migrate = False/deployment_settings.base.migrate = True/g' 000_config.py", pty=True)

def migrate():
    """ Perform a Migration """
    #migrate_url = urllib2.urlopen("http://%s/eden/default/index" % env.host) 
    #print migrate_url.read()
    #with cd("/home/web2py"):
    # ToDo: Pass input into remote PTY
    #run("sudo -H -u web2py python web2py.py -N -S eden -M", pty=True)
    child = pexpect.spawn("ssh -i /root/.ssh/sahana_release %s@%s" % (env.user, env.host))
    child.sendline("cd /home/web2py")
    child.expect("/home/web2py#")
    child.sendline("sudo -H -u web2py python web2py.py -N -S eden -M")
    child.expect("In [1]:")
    child.interact()     # Give control of the child to the user.

def migrate_off():
    """ Disabling migrations """
    with cd("/home/web2py/applications/eden/models/"):
        run("sed -i 's/deployment_settings.base.migrate = True/deployment_settings.base.migrate = False/g' 000_config.py", pty=True)

def pull():
    """ Upgrade the Eden code """
    with cd("/home/web2py/applications/eden/"):
        # Backup VERSION for rollbacks & so we know which revision Live should pull
        # ToDo Parse file instead & make it available for rollback() or the prod pull()
        run("cp -f VERSION ..", pty=True)
        # ToDo Pass an argument to upgrade to a specific revision
        #if env.version:
        #    run("bzr pull -r %i" % env.version, pty=True)
        #else:
        run("bzr pull", pty=True)

def rollback():
    """ Rollback from a failed upgrade """
    with cd("/home/web2py/applications/eden/"):
        # Back-up deployment_settings
        run("cp -f models/000_config.py ..", pty=True)
        # ToDo: Dangerous this will remove all other customisations!
        # Need to ensure we list these clearly before doing this!
        run("bzr revert -r %i" % env.version, pty=True)
        # Restore deployment_settings
        run("cp -f ../000_config.py models", pty=True)
        reload()

def reload():
    """ Reload Apache """
    run("apache2ctl restart", pty=True)

def os_upgrade():
    """ Update OS """
    run("apt-get update", pty=True)
    run("apt-get upgrade -y", pty=True)

