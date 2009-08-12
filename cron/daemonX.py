# -*- coding: utf-8 -*-

# DaemonX
# author: Hasanat Kazmi <hasanatkazmi@gmail.com>
# This script requires jsonrpc, install it from json-rpc.org/wiki/python-json-rpc
# written using python 2.5, should work on 2.6

import os, os.path
import sys
import logging, logging.handlers
from ConfigParser import RawConfigParser
import pickle
import shutil
exec('import applications.%s.modules.Zeroconf' % request.application)
# Faster for Production (where app-name won't change):
#import applications.sahana.modules.Zeroconf
import socket
import time
from jsonrpc import ServiceProxy, JSONRPCException

class LogManager(object):
    """ Manages error logs """
    def __init__(self, logLevel = logging.DEBUG):
        self.logfolder = "synclogs"
        self.logfilename = "log.out"
        self.level = logLevel
        
        scriptfolder = sys.path[0]
        if not os.path.isdir(os.path.join(scriptfolder, self.logfolder)):
            os.mkdir(os.path.join(scriptfolder, self.logfolder)) # mkdir is only available for Windows & Unix

        handler = logging.handlers.RotatingFileHandler(os.path.join(scriptfolder, self.logfolder, self.logfilename), maxBytes=128*1024*8)#128kb

        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)

        self.handler = handler

    def log(self, caller, severity, message):
        """
        caller is name of the class which is logging
        severity is type of log entry like warning or error
        message is log message
        """
        if severity not in [logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL]:
            raise Exception("severity must be one of these: logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL")
        my_logger = logging.getLogger(str(caller))
        my_logger.setLevel(self.level)
        my_logger.addHandler(self.handler)
        my_logger.log(severity, message)
        
class Config(object):
    """ (not to confuse with zeroConf) It saves configurations for the system  """
    def __init__(self):
        items = {}
        items['localhost'] = "127.0.0.1"
        items['localhost-port'] = 8000
        items['servername'] = 'sahana'
        self.items = items

    def getConfFromServer(self, server):
        "gets configurations by calling server (localhost)"
        if not isinstance(server, RpcManager):
            raise
        # getting congis from server
        try:
            settings = server.execute('getconf')
            serveritems = {}
            serveritems['uuid'] = settings['uuid']
            serveritems['zeroconfig_lookuport'] = settings['zeroconfig_lookuport']
            
            zeroconfproperties = {}
            zeroconfproperties['discription'] = settings['zeroconf_discription']
            zeroconfproperties['uuid'] = settings['uuid']
            zeroconfproperties['serverport'] = self.items['localhost-port']
            zeroconfproperties['zeroconfig_lookuport'] = settings['zeroconfig_lookuport']
            serveritems['zeroconfproperties'] = zeroconfproperties
            
            self.items.update(serveritems)
        except:
            raise Exception("invalid settings called form server, or server may be down")

class DumpManager(object):
    """ All data dump related operations are performed by this """
    """
        note that date can not be processed by pickle, so web services should not export date as date object (which it isnt right at the time to writting this code)
    """

    def __init__(self, logger=None):
        self.logger = logger
        default_dump_folder = "dumps"
        self.default_dump_folder_path = os.path.join(sys.path[0], default_dump_folder)

        if not os.path.isdir(self.default_dump_folder_path):
            os.mkdir(self.default_dump_folder_path)
       
    def __next(self): # this is enumerate function, but meeting our unique requirement
        def isintfolder(i):
            try:
                int(i)
                return True
            except:
                return False

        dirs = os.listdir(self.default_dump_folder_path)
        dirs = [int(i) for i in dirs if os.path.isdir(os.path.join(self.default_dump_folder_path, i)) if isintfolder(i) ]
        dirs.sort()
        for i in range(len(dirs)+1):
            if not i in dirs:
                #self.lastdir = i
                #return self.lastdir
                return i
    
    def createdump(self, *data):
        """
        This function creates dumps and returns reference id
        data are any python objects
        """
        folderref = self.__next()
        folder = os.path.join(self.default_dump_folder_path, str(folderref))
        os.mkdir(folder)
        for i in range(len(data)):
            fileobj = file(os.path.join(folder, str(i)), "w")
            pickle.dump(data[i], fileobj)
            fileobj.close()
            if not self.logger == None:
                self.logger.log('DumpManager', logging.INFO, "created Dump in " + os.path.join(folder, str(i)))

        return folderref

    def createobj(self, referenceid, deletedump = True):
        "when referenceid is passed, all object related to that reference id are returned as list"
        folder = os.path.join(self.default_dump_folder_path, str(referenceid))
        def isnumfile(i):
            try:
                int(i)
                return True
            except:
                return False
        
        try:
            files = [i for i in os.listdir(folder) if os.path.isfile(os.path.join(folder, i))]
        except:
            try:
                int(referenceid)
            except:
                raise Exception("referenceid must be an integer")
            raise Exception("Invalid reference id, no such file")
        files.sort()
        toreturn = [pickle.load(file(os.path.join(folder, i), "r")) for i in files]
        if not self.logger == None:
            self.logger.log('DumpManager', logging.INFO, "read Dumps from " + folder)

        if deletedump:
            shutil.rmtree(folder)
            if not self.logger == None:
                self.logger.log('DumpManager', logging.INFO, "deleted Dump folder: " + folder)

        print toreturn

    def cleardump():
        shutil.rmtree(self.default_dump_folder_path)
        os.mkdir(self.default_dump_folder_path)
        if not self.logger == None:
            self.logger.log('DumpManager', logging.INFO, "cleared all dump: " + self.default_dump_folder_path)

class ZeroConfExpose(object):
    """ exposes the service for zeroConf """
    def __init__(self, conf, logger = None):
        self.conf = conf
        self.logger = logger

        server = Zeroconf.Zeroconf()
        # Get local IP address
        local_ip = socket.gethostbyname(socket.gethostname())
        local_ip = socket.inet_aton(local_ip)

        svc1 = Zeroconf.ServiceInfo('_durus._tcp.local.',
                                      'Database 1._durus._tcp.local.',
                                      address = local_ip,
                                      port = self.conf.items['zeroconfig_port'],
                                      weight = 0, priority=0,
                                      properties = self.conf.items['zeroconfproperties']
                                     )
        if not self.logger == None:
            self.logger.log('ZeroConfExpose', logging.INFO, "exposed ZeroConf service")
        server.registerService(svc1)


class ZeroConfSearch(object):
    """ searches for other servers, if a server is found, gets its information, and puts in Server object. It passes server object to SyncManager """

    class MyListener(object):
        def __init__(self, conf, servermanager, localrpc, logger=None):
            self.conf = conf
            self.servermanager = servermanager
            self.localrpc = localrpc
            self.logger = logger

        def removeService(self, server, type, name):
            if not self.logger == None:
                self.logger.log('ZeroConfSearch', logging.INFO, "Service "+ repr(name)+ " removed")
        
        def addService(self, server, type, name):
            if not self.logger == None:
                self.logger.log('ZeroConfSearch', logging.INFO, "Service "+ repr(name)+ " added")
            # Request more information about the service
            info = server.getServiceInfo(type, name)
            if not info is None:
                "printing for debuging purposes"
                print info.getProperties()
                # IP address as unsigned short, network byte order, translate it into string
                print info.getAddress()
                #conversion yet to be done 
                print info.getPort()
                self.servermanager.addServer(info.getAddress(), info.getPort(), info.getProperties())

    def __init__(self, conf, servermanager, localrpc, logger = None):
        self.conf = conf
        self.servermanager = servermanager
        self.localrpc = localrpc
        self.logger = logger
        
        server = Zeroconf.Zeroconf()
        listener = self.MyListener(self.conf, self.servermanager, self.localrpc, logger = self.logger)
        browser = Zeroconf.ServiceBrowser(server, "_durus._tcp.local.", listener)

class ServerManager(object):
    """ gets server object as parameter, it calls local server json rpc service through RpcManager. When it gets data from rpcManager, it calls local server for data, if it gets error, it logs that in error log using errorLogManager or if it gets successful, it calls another dumpManager's instance and stores data and gets reference id, then foreign server's postdata through rpcManager  """
    def __init__(self, conf, dumpmanager, localrpc, logger=None):
        self.conf = conf
        self.localrpc = localrpc
        self.logger = logger
        self.dumpmanager = dumpmanager
        self.starttime = None
        self.cue = []
        
    def addServer(self, adress, port, properties):
        """server is URI of the server to be called"""
        node = []
        node.append( adress )
        node.append( port )
        node.append( properties )
        self.cue.append(node)
        #log it
        
    def process(self):
        """ it does all json transactions between servers """
        while True:
            # For each element in self.cue, call that server and exchange data with local server
            self.starttime = int(time.time())
            for i in self.cue:
                try:
                    url = "http://"+i[0]+":" + str(i[1]) + i[2]['rpc_service_url']
                    foriegnrpc = RpcManager(self.conf, self.logger, server = url)
                    foriegnrpc.open_server()
                    
                    cred = self.localrpc.execute("getAuthCred", i[2]['uuid'])
                    dataforiegn = foriegnrpc.execute("getdata", self.conf.uuid, cred[0], cred[1])
                    ref1 = self.dumpmanager.createdump(dataforiegn)
                    self.localrpc.execute("putdata", "","", dataforiegn)
                    
                    datalocal = self.localrpc.execture("getdata", i[2]['uuid'], "", "")
                    ref2 = self.dumpmanager.createdump(datalocal)
                    foriegnrpc.execute("putdata",cred[0], cred[1], datalocal)
                    self.dumpmanager.cleardump()
                except Exception, e:
                    if not self.logger == None:
                        self.logger.log('ServerManager', logging.ERROR, "error occured while processing: " + e )
            
            pausetime = 30 * 60 # 30 mins
            if int(time.time()) - self.starttime < pausetime:
                time.sleep(pausetime - time.time() + self.starttime)
            
        
class RpcManager(object):
    """ all RPC related activities are performed through this """
    def __init__(self, conf, logger=None, server = None):
        if not isinstance(conf, Config):
            raise
        self.server = server
        self.conf = conf
        self.logger = logger
    
        self.open_server()
    
    def open_server(self):
        if self.server == None:
            try:
                url = "http://"+self.conf.items['localhost']+":"+ str(self.conf.items['localhost-port']) +"/"+ self.conf.items['servername'] +"/admin/call/jsonrpc"
            except:
                raise Exception("Configuration file seems to be corrupt. Delete it, system will regenerate new for you, you can edit it later on")
            try:
                self.server = ServiceProxy(url)
            except:
                raise Exception("Server proxy couldn't be resolved: " + url)

    def execute(self, function, *args):
        try:
            toreturn = eval('self.server.'+str(function))(*args)
            message = "function "+str(function)+" sucessfull with arguments: " + str(*args)
            if not self.logger == None:
                self.logger.log('RpcManager', logging.INFO, message)
        except:
            message = "function "+str(function)+" failed with arguments: " + str(*args)
            if not self.logger == None:
                self.logger.log('RpcManager', logging.ERROR, message)
            raise Exception(message)
        return toreturn


class init(object):
    """ Manages execution """
    def __init__(self):
        "if dumps folder has files in it, it means there were were partial sync attempts, that need to be solved"
        logger = LogManager()
        c = Config()
        r = RpcManager(c, logger=logger) #this instance deals with local server
        while True:
            try:
                c.getConfFromServer(r)
                break
            except Exception, e:
                print "Couldn't call local server. " + e
                # Try it after a minute
                time.sleep(60)
        d = DumpManager(logger = logger)
        #ref = d.createdump(2,3,[1,2,3], "23")
        #d.createobj(ref)
        sm = ServerManager(c, d, r, logger=logger)

        ze = ZeroConfExpose(c, logger=logger)
        zs = ZeroConfSearch(c, sm, r, logger=logger)
        sm.process() # this is non returning

if __name__ == '__main__':
    init()