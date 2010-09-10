from __future__ import with_statement
from fabric.api import *
from fabric.colors import red, green
import pexpect
#import urllib2

#
# http://eden.sahanafoundation.org/wiki/PakistanDeploymentCycle
#
# Assumptions:
# - /root/.my.cnf is configured to allow root access to MySQL without password
#

test_host = "test.eden.sahanafoundation.org"
#prod_host = "pakistan.sahanafoundation.org"
env.key_filename = ["/home/release/.ssh/sahana_release"]

demo_host = "demo.eden.sahanafoundation.org"

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
    print(green("Upgrading Demo to current Test version"))
    demo()
    maintenance_on()
    backup()
    pull()
    cleanup()
    migrate_on()
    # @ToDo db_sync
    db_upgrade()
    migrate_off()
    maintenance_off()
    print(green("Upgrading Production to current Test version"))
    prod()
    maintenance_on()
    backup()
    pull()
    cleanup()
    migrate_on()
    db_upgrade()
    migrate_off()
    maintenance_off()
    print(green("Upgrading Test to current Trunk version"))
    test()
    maintenance_on()
    backup()
    pull()
    cleanup()
    migrate_on()
    db_sync()
    migrate_off()
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
        run("bzr diff controllers > /root/custom.diff", pty=True)
        run("bzr diff models >> /root/custom.diff", pty=True)
        run("bzr diff views >> /root/custom.diff", pty=True)
        # Backup database
        run("mysqldump sahana > /root/backup.sql", pty=True)

def cleanup():
    """
        Cleanup after the bzr pull
        - assumes that backup() was run before the upgrade!
    """
    print(green("%s: Cleaning up" % env.host))
    with cd("/home/web2py/applications/eden/"):
        # Resolve conflicts
        run("find . -name *.BASE -print | xargs /bin/rm -f", pty=True)
        run("find . -name *.THIS -print | xargs /bin/rm -f", pty=True)
        run("for i in `find . -name *.OTHER` ; do mv $i ${i/.OTHER/}; done", pty=True)
        run("bzr resolve", pty=True)
        # Restore customisations
        print(green("%s: Restoring Customisations" % env.host))
        run("patch -p0 < /root/custom.diff", pty=True)
        # Fix permissions
        run("chown web2py:web2py languages/*", pty=True)

def db_upgrade():
    """
        Upgrade the Database
        - this assumes that /root/.my.cnf is configured on both Test & Prod to allow root to have access to the MySQL DB
          without needing '-u root -p'
    """
    if "test" in env.host:
        # Skip for Test sites
        # (they use db_sync instead)
        pass
    else:
        print(green("%s: Upgrading Database" % env.host))
        # See dbstruct.py
        with cd("/home/web2py/applications/eden/models/"):
            # Step 0: Drop old database 'sahana'
            print(green("%s: Dropping old Database" % env.host))
            run("mysqladmin drop sahana", pty=True)
            # Step 1: Create a new, empty MySQL database 'sahana' as-normal
            print(green("%s: Creating new Database" % env.host))
            run("mysqladmin create sahana", pty=True)
            # Step 2: set deployment_settings.base.prepopulate = False in models/000_config.py
            print(green("%s: Disabling prepopulate" % env.host))
            run("sed -i 's/deployment_settings.base.prepopulate = True/deployment_settings.base.prepopulate = False/g' 000_config.py", pty=True)
        # Step 3: Allow web2py to run the Eden model to configure the Database structure
        migrate()
        with cd("/root/"):
            # Step 5: Use the backup to populate a new table 'old'
            print(green("%s: Restoring backup to 'old'" % env.host))
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
        print child.before
        # Step 8: Fixup manually anything which couldn't be done automatically
        print (green("Need to exit the SSH session once you have fixed anything which needs fixing"))
        child.interact()     # Give control of the child to the user.
        with cd("/root/"):
            # Step 9: Take a dump of the fixed data (no structure, full inserts)
            print(green("%s: Dumping fixed data" % env.host))
            run("mysqldump -tc old > old.sql", pty=True)
            # Step 10: Import it into the empty database
            print(green("%s: Importing fixed data" % env.host))
            run("mysql sahana < old.sql", pty=True)
        #@ ToDo
        # Restore indexes
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

def db_sync():
    """
        Synchronise the Database
        - this assumes that /root/.my.cnf is configured on both Test & Prod to allow the root SSH user to have access to the MySQL DB
          without needing '-u root -p'
    """
    if not "test" in env.host:
        # Skip for Production sites
        # (they use db_upgrade instead)
        pass
    else:
        print(green("%s: Synchronising Database" % env.host))
        # See dbstruct.py
        with cd("/home/web2py/applications/eden/models/"):
            # Step 0: Drop old database 'sahana'
            print(green("%s: Dropping old Database" % env.host))
            run("mysqladmin drop sahana", pty=True)
            # Step 1: Create a new, empty MySQL database 'sahana' as-normal
            print(green("%s: Creating new Database" % env.host))
            run("mysqladmin create sahana", pty=True)
            # Step 2: set deployment_settings.base.prepopulate = False in models/000_config.py
            print(green("%s: Disabling prepopulate" % env.host))
            run("sed -i 's/deployment_settings.base.prepopulate = True/deployment_settings.base.prepopulate = False/g' 000_config.py", pty=True)
        # Step 3: Allow web2py to run the Eden model to configure the Database structure
        migrate()
        # Step 4: Export the Live database from the Live server (including structure)
        live = "/root/live.sql"
        prod()
        with cd("/root/"):
            print(green("%s: Dumping live" % env.host))
            run("mysqldump sahana > new.sql", pty=True)
        print(green("%s: Downloading live" % env.host))
        get("/root/new.sql", live)
        test()
        print(green("%s: Uploading live" % env.host))
        put(live, live)
        with cd("/root/"):
            # Step 5: Use this to populate a new table 'old'
            print(green("%s: Restoring live to 'old'" % env.host))
            run("mysqladmin create old", pty=True)
            run("mysql old < live.sql", pty=True)
        # Step 7: Run the script: python dbstruct.py
        # use pexpect to allow us to jump in to do manual fixes
        child = pexpect.spawn("ssh -i /root/.ssh/sahana_release %s@%s" % (env.user, env.host))
        child.expect(":~#")
        child.sendline("cd /home/web2py/applications/eden/static/scripts/tools")
        child.expect(":/home/web2py/applications/eden/static/scripts/tools#")
        child.sendline("python dbstruct.py")
        print child.before
        # Step 8: Fixup manually anything which couldn't be done automatically
        print (green("Need to exit the SSH session once you have fixed anything which needs fixing"))
        child.interact()     # Give control of the child to the user.
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
    child = pexpect.spawn("ssh -i /root/.ssh/sahana_release %s@%s" % (env.user, env.host))
    child.expect(":~#")
    child.sendline("cd /home/web2py")
    child.expect("/home/web2py#")
    child.sendline("sudo -H -u web2py python web2py.py -N -S eden -M")
    #child.sendline("exit()")
    #child.sendline("exit")
    print child.before
    print (green("Need to exit() w2p shell & also the SSH session once you have fixed anything which needs fixing"))
    # Give control of the child to the user.
    child.interact()

def migrate_off():
    """ Disabling migrations """
    print(green("%s: Disabling Migrations" % env.host))
    with cd("/home/web2py/applications/eden/models/"):
        run("sed -i 's/deployment_settings.base.migrate = True/deployment_settings.base.migrate = False/g' 000_config.py", pty=True)

def pull():
    """ Upgrade the Eden code """
    print(green("%s: Upgrading code" % env.host))
    with cd("/home/web2py/applications/eden/"):
        try:
            print(green("%s: Upgrading to version %i" % (env.host, env.revno)))
            run("bzr pull -r %i" % env.revno, pty=True)
        except:
            if "test" in env.host:
                # Upgrade to current Trunk
                print(green("%s: Upgrading to current Trunk" % env.host))
                run("bzr pull", pty=True)
            else:
                if "demo" in env.host:
                    demo = True
                else:
                    demo = False
                # work out the VERSION to pull
                test()
                version = "/root/VERSION_test"
                get("/home/web2py/applications/eden/VERSION", version)
                if os.access(version, os.R_OK):
                    f = open(version, "r")
                    lines = f.readlines()
                    f.close()
                    env.revno = lines[0].split(" ")[0].replace("r", "")
                if demo:
                    demo()
                else:
                    prod()
                print(green("%s: Upgrading to version %i" % (env.host, env.revno)))
                run("bzr pull -r %i" % env.revno, pty=True)

def rollback():
    """
        Rollback from a failed upgrade
        - assumes that backup() was run before the upgrade!
    """
    print(green("%s: Rolling back" % env.host))
    with cd("/home/web2py/applications/eden/"):
        version = "/root/VERSION"
        if os.access(version, os.R_OK):
            f = open(version, "r")
            lines = f.readlines()
            f.close()
            env.revno = lines[0].split(" ")[0].replace("r", "")
        print(green("%s: Rolling back to rev %i" % (env.host, env.revno)))
        run("bzr revert -r %i" % env.revno, pty=True)
        # Restore customisations
        print(green("%s: Restoring Customisations" % env.host))
        run("patch -p0 < /root/custom.diff", pty=True)
        # Restore database
        print(green("%s: Restoring Database" % env.host))
        run("mysqladmin drop sahana", pty=True)
        run("mysqladmin create sahana", pty=True)
        run("mysql sahana < backup.sql", pty=True)
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

