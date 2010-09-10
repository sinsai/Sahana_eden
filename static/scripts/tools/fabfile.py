from __future__ import with_statement
from fabric.api import *
import pexpect
#import urllib2

#
# http://eden.sahanafoundation.org/wiki/PakistanDeploymentCycle
#

test_host = "test.eden.sahanafoundation.org"
prod_host = "pakistan.sahanafoundation.org"
env.key_filename = ["/home/release/.ssh/sahana_release"]


# Definitions for 'Test' infrastructure
def test():
    """ List of server(s) for Test infrastructure """
    env.user = "root"
    env.hosts = [test_host]

# Definitions for 'Production' infrastructure
def prod():
    """ List of server(s) for Production infrastructure """
    env.user = "root"
    env.hosts = [prod_host]


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
    """
    # Upgrade Production to current Test version
    prod()
    maintenance_on()
    migrate_on()
    pull()
    cleanup()
    migrate()
    migrate_off()
    maintenance_off()
    # Upgrade Test to current Trunk version
    test()
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
        # ToDo: Extend to all conflicts (models & languages at least)
        # ToDo: Provide more comforting output (an error here is good!)
        run("mv models/000_config.py.THIS models/000_config.py", pty=True)

def db_sync():
    """
        Synchronise the Database
        - this assumes that /root/.my.cnf is configured on both Test & Prod to allow the root SSH user to have access to the MySQL DB
          without needing '-u root -p'
    """
    if not "test" in env.host:
        # Skip for Production sites
        pass
    else:
        # See dbstruct.py
        with cd("/home/web2py/applications/eden/models/"):
            # Step 0: Drop old database 'sahana'
            run("mysqladmin drop sahana", pty=True)
            # Step 1: Create a new, empty MySQL database 'sahana' as-normal
            run("mysqladmin create sahana", pty=True)
            # Step 2: set deployment_settings.base.prepopulate = False in models/000_config.py
            run("sed -i 's/deployment_settings.base.prepopulate = True/deployment_settings.base.prepopulate = False/g' 000_config.py", pty=True)
        # Step 3: Allow web2py to run the Eden model to configure the Database structure
        migrate()
        # Step 4: Export the Live database from the Live server (including structure)
        prod()
        with cd("/root"):
            run("mysqldump sahana > backup.sql", pty=True)
        test()
        with cd("/root"):
            # Step 4.5: Copy this dumpfile to the Test server
            run("scp %s/backup.sql ." % prod_host, pty=True)
            # Step 5: Use this to populate a new table 'old'
            run("mysqladmin create old", pty=True)
            run("mysql old < backup.sql", pty=True)
            # Step 7: Run the script: python dbstruct.py
            # copy the script to outside the web-readable area so that we can add the passwords safely
            run("cp -f /home/web2py/applications/eden/static/scripts/tools/dbstruct.py .", pty=True)
            # read the passwords from /root/.my.cnf
            # @ToDo
            # replace the password in the script copy
            run("sed -i 's/user="sahana", passwd="password"/user="root", passwd="password"/g' dbstruct.py", pty=True)
        # Run the modified script
        # use pexpect to allow us to jump in to do manual fixes
        child = pexpect.spawn("ssh -i /root/.ssh/sahana_release %s@%s" % (env.user, env.host))
        child.expect(":~#")
        child.sendline("cd /root")
        child.expect("/root#")
        child.sendline("python dbstruct.py")
        print child.before
        # Step 8: Fixup manually anything which couldn't be done automatically
        # @ToDo List issues as clearly/concisely as possible for us to resolve manually
        # @ToDo Try to resolve any FK constraint issues automatically
        child.interact()     # Give control of the child to the user.
        # Need to exit() w2p shell & also the SSH session
        with cd("/root"):
            # Step 9: Take a dump of the fixed data (no structure, full inserts)
            run("mysqldump -tc old > old.sql", pty=True)
            # Step 10: Import it into the empty database
            run("mysql sahana < old.sql", pty=True)
            # Cleanup
            run("rm -f backup.sql", pty=True)
            run("rm -f old.sql", pty=True)
            run("rm -f dbstruct.py", pty=True)

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
    child.expect(":~#")
    child.sendline("cd /home/web2py")
    child.expect("/home/web2py#")
    child.sendline("sudo -H -u web2py python web2py.py -N -S eden -M")
    print child.before
    child.interact()     # Give control of the child to the user.
    # Need to exit() w2p shell & also the SSH session

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

