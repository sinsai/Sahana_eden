from selenium import selenium
import unittest, time, re
import actions
import inspect

# Class that will provide a constant interface to the Selenium test suite
#
# The following variables are shared by all classes that inherit SahanaTest 
# self.selenium will provide a reference to the shared selenium object
# self.action will provide a reference to the shared action object
#
# The following variables are unique to each class that will inherit SahanaTest
# These are used to create test data at the start of a run and delete the test data at the end
# self.testcaseStartedCount will provide a count of the number of tests within the class that have been started
# self.testcaseFinishedCount will provide a count of the number of tests within the class that have completed
# self.testcaseCount will provide a count of the number of tests within the class that will be run

class SahanaTest(unittest.TestCase):

    _seleniumCreated = False
    _classDetailsCollected = False
    _user = "user@example.com"
    _password = "testing"
    @staticmethod
    def setUpHierarchy(browser = "*chrome", 
                       path = "", 
                       ipaddr = "localhost", 
                       ipport = 4444, 
                       webURL = "http://127.0.0.1:8000/"):
        # only run once
        if not SahanaTest._seleniumCreated:
            if browser == "*custom":
                browser += " " + path
            print "selenium %s %s %s %s" % (ipaddr, ipport, browser, webURL)
            SahanaTest.selenium = selenium(ipaddr, ipport, browser, webURL)
            SahanaTest.action = actions.Action()
            SahanaTest._seleniumCreated = True
        if SahanaTest.selenium.sessionId == None:
            SahanaTest.selenium.start()

    @classmethod
    def start(cls):
        print "class %s first time %s" % (cls, cls._classDetailsCollected)
        if not cls._classDetailsCollected:
            cls.testcaseStartedCount = 0
            cls.testcaseFinishedCount = 0
            cls.testcaseCount = 0
            cls.firstRunExists = False
            cls.lastRunExists = False
            # Use inspect to find the number of test methods
            # this is then used in tearDown() to work out if lastRun() needs to be invoked
            methods = inspect.getmembers(cls, inspect.ismethod)
            for (name, value) in methods:
                if re.search(r'^test_', name)!= None:
                    cls.testcaseCount += 1
                if name == "firstRun":
                    cls.firstRunExists = True
                if name == "lastRun":
                    cls.lastRunExists = True
            # This cls version will now hide the SahanaTest version
            cls._classDetailsCollected = True
        cls.testcaseStartedCount += 1
    
    @classmethod
    def finish(cls):
        cls.testcaseFinishedCount += 1
        return cls.testcaseFinishedCount == cls.testcaseCount

    @classmethod
    def useSahanaAdminAccount(cls):
        cls._user = "admin@example.com"
        cls._password = "testing"
        
    @classmethod
    def useSahanaUserAccount(cls):
        cls._user = "user@example.com"
        cls._password = "testing"
        
    @classmethod
    def useSahanaAccount(cls, email, password):
        cls._user = email
        cls._password = password
    
    def setUp(self):
        print self.shortDescription()
        self.start()
        if self.testcaseStartedCount == 1:
            if self.firstRunExists:
                self.firstRun()
        
    def tearDown(self):
        if self.finish():
            if self.lastRunExists:
                self.lastRun()
            self.action.logout(self)
