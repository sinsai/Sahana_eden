from __future__ import with_statement
from fabric.api import *
from fabric.colors import red, green
import os
import pexpect

#
# http://eden.sahanafoundation.org/wiki/PakistanDeploymentCycle
#
# Assumptions:
# - /root/.my.cnf is configured to allow root access to MySQL without password
# - root on Prod/Demo can SSH to Test without password
#
# Usage:
# fab [test|demo|prod] deploy
#

test_host = "test.eden.sahanafoundation.org"
demo_host = "demo.eden.sahanafoundation.org"
prod_host = "pakistan.sahanafoundation.org"
all_hosts = [prod_host, demo_host, test_host, "eden.sahanafoundation.org", "humanityroad.sahanafoundation.org", "geo.eden.sahanafoundation.org", "camp.eden.sahanafoundation.org"]
env.key_filename = ["/root/.ssh/sahana_release"]

# Definitions for 'Test' infrastructure
def test():
    """ List of server(s) for Test infrastructure """
    env.user = "root"
    env.hosts = [test_host]

# Definitions for 'Demo' infrastructure
def demo():
    """ List of server(s) for Demo infrastructure """
    env.user = "root"
    env.hosts = [demo_host]

# Definitions for 'Production' infrastructure
def prod():
    """ List of server(s) for Production infrastructure """
    env.user = "root"
    env.hosts = [prod_host]


# Definitions for 'All' infrastructure
def all():
    """ List of server(s) for All infrastructure """
    env.user = "root"
    env.hosts = all_hosts


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
        - need to prefix with 'demo', 'test' or 'prod'
    """
    print(green("Deploying to %s" % env.host))
    maintenance_on()
    backup()
    pull()
    cleanup()
    migrate_on()
    if "test" in env.host:
        db_sync()
    else:
        db_upgrade()
        # Step 3: Allow web2py to run the Eden model to configure the Database structure
        migrate()
        # Do the actual DB upgrade
        # (split into a separate function to allow it to easily be run manually if there is a problem with the previous step)
        db_upgrade_()
    migrate_off()
    optimise()
    maintenance_off()

def backup():
    """ Backup the current state """
    print(green("%s: Backing up" % env.host))
    with cd("/home/web2py/applications/eden/"):
        # Backup VERSION for rollbacks
        run("cp -f VERSION /root", pty=True)
        # Backup customised files
        # - should just be 000_config, Views, 00_db & zzz_1st_run prod optimisations
        # - currently still a few controller settings not yet controlled by deployment_settings
        # Using >, >> causes an error to be reported even when there's no error
        env.warn_only = True
        run("bzr diff controllers > /root/custom.diff", pty=True)
        run("bzr diff models >> /root/custom.diff", pty=True)
        run("bzr diff views >> /root/custom.diff", pty=True)
        env.warn_only = False
        # Backup database
        run("mysqldump sahana > /root/backup.sql", pty=True)
        # Backup databases folder
        run("rm -rf /root/databases", pty=True)
        run("cp -ar /home/web2py/applications/eden/databases /root", pty=True)

def cleanup():
    """
        Cleanup after the bzr pull
        - assumes that backup() was run before the upgrade!
    """
    print(green("%s: Cleaning up" % env.host))
    with cd("/home/web2py/applications/eden/"):
        # Remove compiled version of the app
        run("/bin/rm -rf compiled", pty=True)
        # Resolve conflicts
        # @ToDo deal with .moved files
        run("find . -name *.BASE -print | xargs /bin/rm -f", pty=True)
        run("find . -name *.THIS -print | xargs /bin/rm -f", pty=True)
        run("for i in `find . -name *.OTHER` ; do mv $i ${i/.OTHER/}; done", pty=True)
        run("bzr resolve", pty=True)
        # Restore customisations
        print(green("%s: Restoring Customisations" % env.host))
        # @ToDo: Only apply customisations to files which had conflicts
        env.warn_only = True
        run("patch -f -p0 < /root/custom.diff", pty=True)
        env.warn_only = False

def db_upgrade():
    """
        Upgrade the Database
        - this assumes that /root/.my.cnf is configured on both Test & Prod to allow root to have access to the MySQL DB
          without needing '-u root -p'
    """
    print(green("%s: Upgrading Database" % env.host))
    # See dbstruct.py
    with cd("/home/web2py/applications/eden/"):
        # Step 0: Drop old database 'sahana'
        print(green("%s: Dropping old Database" % env.host))
        # If database doesn't exist, we don't want to stop
        env.warn_only = True
        run("mysqladmin -f drop sahana", pty=True)
        env.warn_only = False
        print(green("%s: Cleaning databases folder" % env.host))
        run("rm -rf databases/*", pty=True)
        # Step 1: Create a new, empty MySQL database 'sahana' as-normal
        print(green("%s: Creating new Database" % env.host))
        run("mysqladmin create sahana", pty=True)
        # Step 2: set deployment_settings.base.prepopulate = False in models/000_config.py
        print(green("%s: Disabling prepopulate" % env.host))
        run("sed -i 's/deployment_settings.base.prepopulate = True/deployment_settings.base.prepopulate = False/g' models/000_config.py", pty=True)

def db_upgrade_():
    """
        Upgrade the Database (called by db_upgrade())
        - this assumes that /root/.my.cnf is configured on both Test & Prod to allow root to have access to the MySQL DB
          without needing '-u root -p'
    """
    with cd("/root/"):
        # Step 5: Use the backup to populate a new table 'old'
        print(green("%s: Restoring backup to 'old'" % env.host))
        # If database doesn't exist, we don't want to stop
        env.warn_only = True
        run("mysqladmin -f drop old", pty=True)
        env.warn_only = False
        run("mysqladmin create old", pty=True)
        run("mysql old < backup.sql", pty=True)
    # Step 7: Run the script: python dbstruct.py
    # use pexpect to allow us to jump in to do manual fixes
    print(green("%s: Fixing Database Structure" % env.host))
    child = pexpect.spawn("ssh -i /root/.ssh/sahana_release %s@%s" % (env.user, env.host))
    child.expect(":~#")
    child.sendline("cd /home/web2py/applications/eden/static/scripts/tools")
    child.expect(":/home/web2py/applications/eden/static/scripts/tools#")
    child.sendline("python dbstruct.py")
    # @ToDo check if we need to interact otherwise automate
    child.expect(":/home/web2py/applications/eden/static/scripts/tools#")
    child.sendline("exit")
    #print child.before
    # Step 8: Fixup manually anything which couldn't be done automatically
    #print (green("Need to exit the SSH session once you have fixed anything which needs fixing"))
    #child.interact()     # Give control of the child to the user.
    with cd("/root/"):
        # Step 9: Take a dump of the fixed data (no structure, full inserts)
        print(green("%s: Dumping fixed data" % env.host))
        run("mysqldump -tc old > old.sql", pty=True)
        # Step 10: Import it into the empty database
        print(green("%s: Importing fixed data" % env.host))
        run("mysql sahana < old.sql", pty=True)

def db_sync():
    """
        Synchronise the Database
        - this assumes that /root/.my.cnf is configured on both Test & Prod to allow the root SSH user to have access to the MySQL DB
          without needing '-u root -p'
    """
    if not "test" in env.host:
        db_upgrade()
    else:
        print(green("%s: Synchronising Database" % env.host))
        # See dbstruct.py
        with cd("/home/web2py/applications/eden/"):
            # Step 0: Drop old database 'sahana'
            print(green("%s: Dropping old Database" % env.host))
            # If database doesn't exist, we don't want to stop
            env.warn_only = True
            run("mysqladmin -f drop sahana", pty=True)
            env.warn_only = False
            print(green("%s: Cleaning databases folder" % env.host))
            run("rm -rf databases/*", pty=True)
            # Step 1: Create a new, empty MySQL database 'sahana' as-normal
            print(green("%s: Creating new Database" % env.host))
            run("mysqladmin create sahana", pty=True)
            # Step 2: set deployment_settings.base.prepopulate = False in models/000_config.py
            print(green("%s: Disabling prepopulate" % env.host))
            run("sed -i 's/deployment_settings.base.prepopulate = True/deployment_settings.base.prepopulate = False/g' models/000_config.py", pty=True)
        # Step 3: Allow web2py to run the Eden model to configure the Database structure
        migrate()
        # Step 4: Export the Live database from the Live server (including structure)
        child = pexpect.spawn("ssh -i /root/.ssh/sahana_release %s@%s" % (env.user, prod_host))
        child.expect(":~#")
        print(green("%s: Dumping live" % env.host))
        child.sendline("mysqldump sahana > new.sql")
        live = "/root/live.sql"
        print(green("%s: Transferring live" % env.host))
        child.sendline("scp -i /root/.ssh/sahana_release new.sql %s@%s:%s" % (env.user, env.host, live))
        child.expect(":~#")
        child.sendline("exit")
        with cd("/root/"):
            # Step 5: Use this to populate a new table 'old'
            print(green("%s: Restoring live to 'old'" % env.host))
            # If database doesn't exist, we don't want to stop
            env.warn_only = True
            run("mysqladmin -f drop old", pty=True)
            env.warn_only = False
            run("mysqladmin create old", pty=True)
            run("mysql old < live.sql", pty=True)
        # Step 7: Run the script: python dbstruct.py
        # use pexpect to allow us to jump in to do manual fixes
        child = pexpect.spawn("ssh -i /root/.ssh/sahana_release %s@%s" % (env.user, env.host))
        child.expect(":~#")
        child.sendline("cd /home/web2py/applications/eden/static/scripts/tools")
        child.expect(":/home/web2py/applications/eden/static/scripts/tools#")
        child.sendline("python dbstruct.py")
        # @ToDo check if we need to interact otherwise automate
        child.expect(":/home/web2py/applications/eden/static/scripts/tools#")
        child.sendline("exit")
        #print child.before
        # Step 8: Fixup manually anything which couldn't be done automatically
        #print (green("Need to exit the SSH session once you have fixed anything which needs fixing"))
        #child.interact()     # Give control of the child to the user.
        with cd("/root/"):
            # Step 9: Take a dump of the fixed data (no structure, full inserts)
            print(green("%s: Dumping fixed data" % env.host))
            run("mysqldump -tc old > old.sql", pty=True)
            # Step 10: Import it into the empty database
            print(green("%s: Importing fixed data" % env.host))
            run("mysql sahana < old.sql", pty=True)

def maintenance_on():
    """ Enable maintenance mode """
    print(green("%s: Enabling Maintenance Mode" % env.host))
    # ToDo Disable Cron
    run("a2dissite %s" % env.host, pty=True)
    run("a2ensite maintenance", pty=True)
    reload()

def maintenance_off():
    """ Disable maintenance mode """
    print(green("%s: Disabling Maintenance Mode" % env.host))
    # ToDo Enable Cron
    run("a2dissite maintenance", pty=True)
    run("a2ensite %s" % env.host, pty=True)
    reload()

def migrate_on():
    """ Enabling migrations """
    print(green("%s: Enabling Migrations" % env.host))
    with cd("/home/web2py/applications/eden/models/"):
        run("sed -i 's/deployment_settings.base.migrate = False/deployment_settings.base.migrate = True/g' 000_config.py", pty=True)

def migrate():
    """ Perform a Migration """
    print(green("%s: Performing Migration" % env.host))
    with cd("/home/web2py"):
        run("sudo -H -u web2py python web2py.py -N -S eden -M -R applications/eden/static/scripts/tools/noop.py", pty=True)
    #child = pexpect.spawn("ssh -i /root/.ssh/sahana_release %s@%s" % (env.user, env.host))
    #child.expect(":~#")
    #child.sendline("cd /home/web2py")
    #child.expect("/home/web2py#")
    #child.sendline("sudo -H -u web2py python web2py.py -N -S eden -M")
    # @ToDo check if we need to interact otherwise automate
    # - not working :/
    # special characters in regexes matching?
    #child.expect("]:", timeout=30)
    #child.sendline("exit()")
    #child.expect("/n)?")
    #child.sendline("y")
    #child.expect("/home/web2py#")
    #child.sendline("exit")

    #print child.before
    #print (green("Need to exit() w2p shell & also exit the SSH session once you have fixed anything which needs fixing"))
    # Give control of the child to the user.
    #child.interact()

def migrate_off():
    """ Disabling migrations """
    print(green("%s: Disabling Migrations" % env.host))
    with cd("/home/web2py/applications/eden/models/"):
        run("sed -i 's/deployment_settings.base.migrate = True/deployment_settings.base.migrate = False/g' 000_config.py", pty=True)

def optimise():
    """ Apply Optimisation """
    #@ ToDo
    # Restore indexes via Python script run in Web2Py environment
    #      w2p
    #       tablename = "pr_person"
    #       field = "first_name"
    #       db.executesql("CREATE INDEX %s__idx on %s(%s);" % (field, tablename, field))
    #       field = "middle_name"
    #       db.executesql("CREATE INDEX %s__idx on %s(%s);" % (field, tablename, field))
    #       field = "last_name"
    #       db.executesql("CREATE INDEX %s__idx on %s(%s);" % (field, tablename, field))
    #       tablename = "gis_location"
    #       field = "name"
    #       db.executesql("CREATE INDEX %s__idx on %s(%s);" % (field, tablename, field))
    # Compile application via Python script run in Web2Py environment
    with cd("/home/web2py/"):
        run("python web2py.py -S eden -M -R applications/eden/static/scripts/tools/compile.py", pty=True)

def pull():
    """ Upgrade the Eden code """
    print(green("%s: Upgrading code" % env.host))
    with cd("/home/web2py/applications/eden/"):
        try:
            print(green("%s: Upgrading to version %i" % (env.host, env.revno)))
            run("bzr pull -r %i" % env.revno, pty=True)
        except:
            if "test" in env.host or "demo" in env.host:
                # Upgrade to current Trunk
                print(green("%s: Upgrading to current Trunk" % env.host))
                run("bzr pull", pty=True)
            else:
                # work out the VERSION to pull
                print(green("%s: Getting the version to update to" % env.host))
                run("scp -i /root/.ssh/sahana_release %s@%s:/home/web2py/applications/eden/VERSION /root/VERSION_test" % (env.user, test_host), pty=True)
                version = run("cat /root/VERSION_test", pty=True)
                env.revno = int(version.split(" ")[0].replace("r", ""))
                #version = "/root/VERSION_test"
                #print(green("%s: Getting the version to update to" % env.host))
                #get("/home/web2py/applications/eden/VERSION", version)
                #if os.access(version, os.R_OK):
                #    f = open(version, "r")
                #    lines = f.readlines()
                #    f.close()
                #    env.revno = int(lines[0].split(" ")[0].replace("r", ""))
                print(green("%s: Upgrading to version %i" % (env.host, env.revno)))
                run("bzr pull -r %i" % env.revno, pty=True)

def rollback():
    """
        Rollback from a failed upgrade
        - assumes that backup() was run before the upgrade!
    """
    print(green("%s: Rolling back" % env.host))
    with cd("/home/web2py/applications/eden/"):
        version = run("cat /root/VERSION", pty=True)
        env.revno = int(version.split(" ")[0].replace("r", ""))
        #version = "/root/VERSION"
        #get(version, version)
        #if os.access(version, os.R_OK):
        #    f = open(version, "r")
        #    lines = f.readlines()
        #    f.close()
        #    env.revno = int(lines[0].split(" ")[0].replace("r", ""))
        print(green("%s: Rolling back to rev %i" % (env.host, env.revno)))
        run("bzr revert -r %i" % env.revno, pty=True)
        # Restore customisations
        print(green("%s: Restoring Customisations" % env.host))
        env.warn_only = True
        run("patch -p0 < /root/custom.diff", pty=True)
        env.warn_only = False
        # Restore database
        print(green("%s: Restoring Database" % env.host))
        run("mysqladmin -f drop sahana", pty=True)
        run("mysqladmin create sahana", pty=True)
        run("mysql sahana < backup.sql", pty=True)
        # Restore databases folder
        run("rm -rf databases/*", pty=True)
        run("cp -ar /root/databases/* databases", pty=True)
        reload()

def reload():
    """ Reload Apache """
    print(green("%s: Restarting Apache" % env.host))
    run("apache2ctl restart", pty=True)

def os_upgrade():
    """ Update OS """
    print(green("%s: Updating OS" % env.host))
    run("apt-get update", pty=True)
    run("apt-get upgrade -y", pty=True)

