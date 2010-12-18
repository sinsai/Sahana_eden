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

    _run = False
    @staticmethod
    def setUpHierarchy(browser = "*chrome", 
                       path = "", 
                       ipaddr = "localhost", 
                       ipport = 4444, 
                       webURL = "http://127.0.0.1:8000/"):
        # only run once
        if not SahanaTest._run:
            if browser == "*custom":
                browser += " " + path
            print "selenium %s %s %s %s" % (ipaddr, ipport, browser, webURL)
            SahanaTest.selenium = selenium(ipaddr, ipport, browser, webURL)
            SahanaTest.action = actions.Action()
            SahanaTest._run = True
        if SahanaTest.selenium.sessionId == None:
            SahanaTest.selenium.start()

    @classmethod
    def start(cls):
        cls.testcaseStartedCount = 0
        cls.testcaseFinishedCount = 0
        cls.testcaseCount = 0
        # Use inspect to find the number of test methods
        # this is then used in tearDown() to work out if lastRun() needs to be invoked
        methods = inspect.getmembers(cls, inspect.ismethod)
        for (name, value) in methods:
            if re.search(r'^test_', name)!= None:
                cls.testcaseCount += 1
    
    @classmethod
    def finish(cls):
        cls.testcaseFinishedCount += 1
        return cls.testcaseFinishedCount == cls.testcaseCount

    def tearDown(self):
        self.action.logout(self)