# -*- coding: utf-8 -*-
"""
This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
"""
import logging,optparse,os,sys,glob,ConfigParser,socket,platform
from pkg_resources import Requirement, resource_filename, resource_string, resource_stream, resource_listdir

import locale
try: locale.setlocale(locale.LC_ALL,'fr_FR')
except: pass

sys.path.insert(0, os.getcwd())
from vogelerclient import mainmodule
from vogelerclient import loggers
import vogelerclient

CONFDIR=os.path.expanduser('~/vogelerclient')
MODULENAME='vogelerclient'


#FORMAT = '%(asctime)s %(levelname)s: %(message)s'
#logging.basicConfig(datefmt='%H:%M:%S', format=FORMAT, filename='/tmp/%s.log' % MODULENAME, filemode='w')
#log.setLevel(logging.INFO)

###################
def get_module_conf_files():
    list_files = resource_listdir(MODULENAME,'data')
    # The name of the configuration file HAS to be the name of the module (here, server)
    for fil in list_files:
        if fil.endswith('.conf'):
            yield fil

def initialize_module(ask_permission=True):
    print "Initializing the module"
    try:
        os.mkdir(CONFDIR)
    except: pass

    for filename in os.listdir(CONFDIR):
        print "Will remove", os.path.join(CONFDIR,filename)
        if ask_permission:
            while True:
                choice = raw_input('Are you sure ? [Y/n]')
                if choice in ['y','Y']:
                    os.unlink(os.path.join(CONFDIR,filename))
                if choice in ['n', 'N']:
                    break

    for filename in get_module_conf_files():
        print "Copying file %s to %s" % (filename, CONFDIR)
        data=resource_string(MODULENAME,'data/%s' % filename)
        open(os.path.join(CONFDIR,filename), 'w').write(data)
        #os.chmod(os.path.join(CONFDIR,'post_script.sh'), 0751)

    print "You can now eventually edit/verify the parameters in %s.conf" % os.path.join(CONFDIR,MODULENAME)

sys.path.insert(0, os.getcwd())

def daemonize(pidfile, user):
    log.info('Daemonizing...')
    if os.fork(): sys.exit(0)
    os.umask(0)
    os.setsid()
    if os.fork(): sys.exit(0)

    sys.stdout.flush()
    sys.stderr.flush()
    si = open(os.path.devnull, 'r')
    so = open(os.path.devnull, 'a+')
    se = open(os.path.devnull, 'a+', 0)
    os.dup2(si.fileno(), sys.stdin.fileno())
    os.dup2(so.fileno(), sys.stdout.fileno())
    os.dup2(se.fileno(), sys.stderr.fileno())


    if pidfile:
        log.info("Writing pidfile %s", pidfile)
        pidfile = open(self.params.pidfile, 'w')
        pidfile.write('%i\n' % os.getpid())
        pidfile.close()

    if user:
        import grp
        import pwd
        delim = ':'
        user, sep, group = user.partition(delim)

        # If group isn't specified, try to use the username as
        # the group.
        if delim != sep:
            group = user
        log.info("Changing to %s:%s", user, group)
        os.setgid(grp.getgrnam(group).gr_gid)
        os.setuid(pwd.getpwnam(user).pw_uid)

    log.info("Changing directory to /")
    os.chdir('/')
    return True


def main():
    #if not os.geteuid()==0:
    #    sys.exit("\nOnly root can run this function\n")

    if hasattr(os, "getuid") and os.getuid() != 0:
        sys.path.insert(0, os.path.abspath(os.getcwd()))

    if not os.path.exists(os.path.join(CONFDIR,MODULENAME+'.conf')):
        print "Configuration not found, initializing..."
        initialize_module()

        # Set Node name in configuration
        node_name = socket.getfqdn(platform.node())
        config = ConfigParser.ConfigParser()
        config.read(os.path.join(CONFDIR,MODULENAME+'.conf'))
        config.set('main','local_node_name', node_name)
        configfile = open(os.path.join(CONFDIR,MODULENAME+'.conf'), 'wb')
        config.write(configfile)
        configfile.close()
        print "The local node name has been set to %s (FQDN). If that's not what you want" % node_name
        print "Please change the variable 'local_node_name' in %s" % os.path.join(CONFDIR,MODULENAME+'.conf')

        sys.exit(1)

    # Post-init
    config = ConfigParser.ConfigParser()
    config.read(os.path.join(CONFDIR,MODULENAME+'.conf'))

    # Setup the logs format/handler
    loggers.setup_logs(config)
    log = logging.getLogger(MODULENAME)

    parser = optparse.OptionParser(usage="%prog", version=vogelerclient.__version__)
    parser.add_option('-a', '--action', help="Action", dest="action")
    parser.add_option('-v', '--verbose', dest='verbose', action='count',
                      help="Increase verbosity (specify multiple times for more)")
    parser.add_option('-s', '--disksize', dest='disksize', default=5, type='int',
                      help="Specifier la taille du disque a creer")
    parser.add_option("-r", "--reinit", default=False, action="store_true",
                      help="reinitialize the configuration with the default files")
    parser.add_option("-d", "--daemonize", default=False, action="store_true",
                      help="run the application in the background")
    parser.add_option("-u", "--user", default=None,
                      help="change to USER[:GROUP] after daemonizing")
    parser.add_option("-p", "--pidfile", default=None,
                      help="write PID to PIDFILE after daemonizing")

    (options, args) = parser.parse_args()

    # Logging SETUP
    log_level = logging.WARNING # default
    if options.verbose == 1:
        log_level = logging.INFO
    elif options.verbose >= 2:
        log_level = logging.DEBUG
    logging.basicConfig(level=log_level)

    if options.reinit:
        initialize_module(ask_permission=False)

    # Daemonization
    if options.daemonize:
        daemonize(options.pidfile,options.user)

    mainmodule.main(config,options,args)

