from Tkinter import *

from subprocess import call
from subprocess import Popen
#import thread

import unittest
from sahanaTest import SahanaTest
import HTMLTestRunner
from xmlrunner import *
from selenium import selenium

import os
import time
import sys
import StringIO
import traceback

class TestConfig(object):
    """ Functions which are useful in both interactive & non-interactive mode """
    def __init__(self):
        self.suite = unittest.TestSuite()

    def test_main(self, testList, browser):
        for testModule in testList: # dotted notation module.class
            self.overrideClassSortList(testModule["class"], testModule["tests"])
#            self.suite.addTests(unittest.defaultTestLoader.loadTestsFromName(testName))
        # Invoke TestRunner
        buf = StringIO.StringIO()
        runner = HTMLTestRunner.HTMLTestRunner(
                    stream=buf,
                    title="<Sahana Eden Test>",
                    description="Suite of regressions tests for Sahana Eden."
                    )
        runner.run(self.suite)
        # check out the output
        byte_output = buf.getvalue()
        # output the main test output for debugging & demo
        # print byte_output
        # HTMLTestRunner pumps UTF-8 output
        output = byte_output.decode("utf-8")
        self.fileName = "../results/regressionTest-%s-%s.html" % (browser.replace("*", ""), time.strftime("%Y%m%d-%H%M%S"))
        file = open(self.fileName, "w")
        file.write(output)

    def overrideClassSortList(self, className, testList):
        testLoader = unittest.defaultTestLoader
        tempTests = unittest.TestSuite
        try:
            # loadTestsFromName will also import the module 
            tempTests = testLoader.loadTestsFromName(className)
        except:
            print "Unable to run test %s, check the test exists." % className
            traceback.print_exc()
        parts = className.split(".")
        if len(parts) == 2:
            # Grab the loaded module and get a instance of the class
            module = sys.modules[parts[0]]
            obj = getattr(module, parts[1])
            obj.setSortList(testList)
            # Add the sorted tests to the suite of test cases to be run
            suite = unittest.TestSuite(map(obj, obj._sortList))
            self.suite.addTests(suite)

    # a file with test details listed per line, with the format being:
    # <display name>, <dotted notation of the test>
    # any line not meeting this criteria will be ignored.
    # <dotted notation of the test> is:
    # module optionally followed by the class name optionally followed by the method
    # OR: module[.class[.method]]
    def getTestModuleDetails(self):
        # Read in the testModules files this is a comma separated list
        # Each row consists of two values, the name to be displayed in the UI
        # and the name of the class that will be invoked.
        source = open("../data/testModules.txt", "r")
        modules = source.readlines()
        source.close()
        # moduleList is a data structure containing all the details required by the UI for a module
        # The outer structure is a list of modules
        # The value is a map that will have three values
        # name:display name, class the ClassName and tests:map of testcases
        # The map of tests consists of the testName and a bool to indicate if it should be run
        # [0]{
        #       name:CreateLocations:
        #       class:locations.Locations,
        #       tests:{'name':"loadLocationTestData",'state':True,
        #              'name':"test_locationEmpty",'state':False,
        #              'name':"test_addL0Location",'state':False,
        #              'name':"removeLocationTestData",'state':True
        #             }
        #    }
        moduleList = []
        for module in modules:
            details = module.split(",")
            if len(details) == 2:
                moduleDetails = {}
                moduleDetails["name"] = details[0].strip() 
                moduleDetails["class"] = details[1].strip()
                moduleDetails["tests"] = self.readTestCasesForClass(moduleDetails["class"])
                moduleList.append(moduleDetails)
        return moduleList

    def readTestCasesForClass(self, className):
        try:
            source = open("../tests/%s.txt" % className, "r")
            testcases = source.readlines()
            source.close()
        except:
            # Need to generate the list from the class
            print "File ../tests/%s.txt not found" % className
            return self.extractTestCasesFromClassSource(className)
        testList = []
        for test in testcases:
            details = test.split(",")
            if len(details) ==  2:
                testDetails = {}
                testDetails["name"] = details[0].strip()
                if details[1].strip() == "True":
                    testDetails["state"] = True
                else:
                    testDetails["state"] = False
                testList.append(testDetails)
        return testList

    def extractTestCasesFromClassSource(self, className):
        parts = className.split(".")
        if len(parts) == 2:
            # Grab the loaded module and get a instance of the class
            try:
                module = __import__( parts[0] )
            except ImportError:
                print "Failed to import module %s" % parts[0]
                raise
            module = sys.modules[parts[0]]
            obj = getattr(module, parts[1])
            testList = []
            for test in obj._sortList:
                tests = {}
                tests["state"] = True 
                tests["name"] = test
                testList.append(tests)
            return testList
        return []
    
    def getTestCasesToRun(self, moduleList):
        """ Take a moduleList & convert to the correct format """
        i = 0
        testModuleList = []
        for module in moduleList:
            testModule = {}
            testDetail = []
            for test in moduleList[i]["tests"]:
                if test["state"] == True:
                    testDetail.append(test["name"])
            testModule["class"] = moduleList[i]["class"]
            testModule["tests"] = testDetail
            testModuleList.append(testModule)
            i += 1
        return tuple(testModuleList)

class TestWindow(Frame):
    """ TK GUI to set the Test Settings"""

    def __init__(self, parent=None):
        self.seleniumServer = 0
        Frame.__init__(self, parent=parent)
        self.winfo_toplevel().title("Sahana Eden regression testing helper program")
        
        self.pack(fill=BOTH)
        title = Frame(self)
        title.pack(side=TOP)
        detail = Frame(self)
        detail.pack(side=TOP, fill=BOTH)
        Label(title, text="Sahana Eden Regression Tests - Control Panel").pack(side=LEFT)
        
        sahanaPanel = Frame(detail, borderwidth=2, relief=SUNKEN)
        sahanaPanel.grid(row=0, column=0, sticky=NSEW)
        self.sahanaPanel(sahanaPanel)

        serverPanel = Frame(detail, borderwidth=2, relief=SUNKEN)
        serverPanel.grid(row=0, column=1, sticky=NSEW)
        self.serverPanel(serverPanel)

        testModulesPanel = Frame(detail, borderwidth=2, relief=SUNKEN)
        testModulesPanel.grid(row=1, column=0, sticky=NSEW)
        self.testModulepanel(testModulesPanel)
        
        browserPanel = Frame(detail, borderwidth=2, relief=SUNKEN)
        browserPanel.grid(row=1, column=1, sticky=NSEW)
        self.browser(browserPanel)

        detail.rowconfigure(0, weight=1)
        detail.rowconfigure(1, weight=1)
        detail.columnconfigure(0, weight=1)
        detail.columnconfigure(1, weight=1)

    def run(self):
        self.runTestSuite()
        ##thread.start_new(self.runTestSuite, ())

    def runTestSuite(self):
        # call static method of the base class for all Sahana test case classes
        # this method will ensure that one Selenium instance exists and can be shared
        SahanaTest.setUpHierarchy(self.radioB.get(),
                                  self.browserPath.get(),
                                  self.ipAddr.get(),
                                  self.ipPort.get(),
                                  self.URL.get() + self.app.get()
                                 )
        SahanaTest.useSahanaAccount(self.adminUser.get(),
                                    self.adminPassword.get(),
                                   )
        self.clean = False
        testConfig = TestConfig()
        testModuleList = self.getTestCasesToRun()
        testConfig.test_main(testModuleList, self.radioB.get())
        call(["firefox", os.path.join("..", "results", testConfig.fileName)])
        SahanaTest.selenium.stop() # Debug: Comment out to keep the Selenium window open 
        self.clean = True

    def getTestCasesToRun(self):
        """ Read the status of the checkBoxes & use this to work out which tests to run """
        i = 0
        testModuleList = []
        for module in self.checkboxModules:
            testModule = {}
            if module.get() == 1:
                testDetail = []
                for test in self.moduleList[i]["tests"]:
                    if test["state"] == True:
                        testDetail.append(test["name"])
                testModule["class"] = self.moduleList[i]["class"]
                testModule["tests"] = testDetail
                testModuleList.append(testModule)
            i += 1
        return tuple(testModuleList)

    def __del__(self):
        if (not self.clean):
            SahanaTestSuite.stopSelenium()

    def isSeleniumRunning(self):
        if sys.platform[:5] == "linux":
            # Need to find if a service is running on the Selenium port 
            sockets = os.popen("netstat -lnt").read()
            # look for match on IPAddr and port
            service = ":%s" % (self.ipPort.get())
            if (service in sockets):
                return True
            else:
                return False
        if self.seleniumServer != 0:
            return True
    
    def sahanaPanel(self, panel):
        Label(panel, text="Sahana options").pack(side=TOP)
        Label(panel,
              text="To run the tests a user with admin rights needs to be provided.").pack(side=TOP,
                                                                                           anchor=W)
        Label(panel,
              text="If this is left blank then it is assumed that there is a blank database & so this can be created by registering the user.").pack(side=TOP,
                                                                                                                                                     anchor=W)
        detailPanel = Frame(panel)
        detailPanel.pack(side=TOP, anchor=W, fill=X)
        Label(detailPanel, text="User name:").grid(row=0, column=0, sticky=NW)
        self.adminUser = Entry(detailPanel, width=30)
        self.adminUser.grid(row=0, column=1, sticky=NW)
        Label(detailPanel, text="Password:").grid(row=1, column=0, sticky=NW)
        self.adminPassword = Entry(detailPanel, show="*", width=16)
        self.adminPassword.grid(row=1, column=1, sticky=NW)
        Label(detailPanel, text="Sahana URL:").grid(row=2, column=0, sticky=NW)
        self.URL = Entry(detailPanel, width=40)
        self.URL.grid(row=2, column=1, sticky=NW)
        self.URL.insert(0, "http://127.0.0.1:8000/")
        Label(detailPanel, text="Sahana Application:").grid(row=3, column=0,
                                                            sticky=NW)
        self.app = Entry(detailPanel, width=40)
        self.app.grid(row=3, column=1, sticky=NW)
        self.app.insert(0, "eden/")
        
    def selectTests(self, i, module, details):
        dialog = SelectTestWindow(self, module, details)
        i = 0
        for lbl in self.labelList:
            lbl["text"] = self.testcaseTotals(self.moduleList[i])
            lbl["fg"] = self.testcaseColour
            i += 1
        self.writeTestCasesForClass(module, details)
    
    def toggleButton(self):
        i = 0
        for module in self.checkboxModules:
            # Show or hide the button to select the tests
            if module.get() == 1:
                self.buttonList[i].grid()
            else:
                self.buttonList[i].grid_remove()
            i += 1
        
    def testcaseTotals(self, testList):
        total = 0
        run = 0
        for test in testList["tests"]:
            total += 1
            if test["state"] == True:
                run += 1
        if total == run:
            self.testcaseColour = "black"
        else:
            self.testcaseColour = "red"
        return "%s of %s" % (run, total)
        
    def testModulepanel(self, panel):
        self.moduleList = TestConfig().getTestModuleDetails()
        Label(panel, text="Test Modules").pack(side=TOP)
        Label(panel,
              text="Select the test modules that you would like to run.").pack(side=TOP,
                                                                               anchor=W)
        detailPanel = Frame(panel)
        detailPanel.pack(side=TOP, anchor=W, fill=X)
        self.checkboxModules = []
        self.buttonList = []
        self.moduleName = []
        self.labelList = []
        i = 0
        details = {}
        for details in self.moduleList:
            name = details["name"]
            self.moduleName.append(name)
            var = IntVar()
            
            chk = Checkbutton(detailPanel, text=name, variable=var,
                              command=self.toggleButton)
            self.checkboxModules.append(var)
            btnFrame = Frame(detailPanel)
            chk.grid(row=i//2, column=i%2*3, sticky=NW)
            lbl = Label(detailPanel,
                        text=self.testcaseTotals(self.moduleList[i]))
            lbl["fg"] = self.testcaseColour
            lbl.grid(row=i//2, column=i%2*3+1, sticky=NW)
            self.labelList.append(lbl)
            btn = Button(btnFrame, text="Select tests")
            btn.grid()
            btnFrame.grid(row=i//2, column=i%2*3+2, sticky=NW)
            btnFrame.grid_remove()
            self.buttonList.append(btnFrame)
            def handler(event, i=i, module=name, details=details):
                return self.selectTests(i, module, details)
            btn.bind(sequence="<ButtonRelease-1>", func=handler)
            i += 1
                    
    def serverStatus(self, event):
        if (self.ipAddr.get() != "127.0.0.1"):
            self.statusLbl.config(text="Unknown")
            self.stopSelenium.config(state="disabled")
            self.startSelenium.config(state="disabled")
        elif self.isSeleniumRunning():
            self.statusLbl.config(text="Running")
            self.stopSelenium.config(state="active")
            self.startSelenium.config(state="disabled")
        else:
            self.statusLbl.config(text="Stopped")
            self.stopSelenium.config(state="disabled")
            self.startSelenium.config(state="active")
        self.updateServerCommand()
            
    def serverPanel(self, panel):
        Label(panel, text="Selenium server options").pack(side=TOP)
        detailPanel = Frame(panel)
        detailPanel.columnconfigure(0, weight=0)
        detailPanel.columnconfigure(1, weight=1)
        detailPanel.pack(side=TOP, anchor=W, fill=X)
        Label(detailPanel, text="Status:").grid(row=0, column=0, sticky=NW)
        self.statusLbl = Label(detailPanel, text="Unknown")
        self.statusLbl.grid(row=0, column=1, sticky=NW)
        Label(detailPanel, text="IP Address:").grid(row=1,column=0, sticky=NW)
        self.ipAddr = Entry(detailPanel, width=16)
        self.ipAddr.insert(0, "127.0.0.1")
        self.ipAddr.grid(row=1, column=1, sticky=NW)
        Label(detailPanel, text="Port:").grid(row=2, column=0, sticky=NW)
        self.ipPort = Entry(detailPanel, width=6)
        self.ipPort.insert(0, "4444")
        self.ipPort.grid(row=2, column=1, sticky=NW)
        self.ipAddr.bind("<FocusOut>", self.serverStatus)
        self.ipPort.bind("<FocusOut>", self.serverStatus)
        Label(detailPanel, text="Logging:").grid(row=4, column=0, sticky=NW)
        logPanel = Frame(detailPanel)
        logPanel.grid(row=4, column=1, sticky=NSEW)
        self.radioLog = StringVar()
        Radiobutton(logPanel, text="No Logging", value="None",
                    command=self.onPressServerLog,
                    variable=self.radioLog).pack(side=TOP, anchor = W)
        Radiobutton(logPanel, text="Log to file", value="File",
                    command=self.onPressServerLog,
                    variable=self.radioLog).pack(side=TOP, anchor = W)
        self.logFilename = Entry(logPanel, width=40)
        self.logFilename.insert(0, "SahanaEdenRegressionTests.log")
        self.logFilename.config(state="readonly")
        self.logFilename.pack(side=TOP, anchor=W, expand=YES, fill=X)
        self.radioLog.set("None")
        self.serverCommand = Entry(detailPanel, state="readonly", width=50)
        self.serverCommand.grid(row=5, column=0, columnspan=2, sticky=NSEW)
        self.updateServerCommand()
        button = Frame(logPanel)
        button.pack(side=TOP, fill=BOTH)
        self.startSelenium = Button(button, text="Start",
                                    command=self.startSelenium)
        self.startSelenium.pack(side=RIGHT, anchor=SE)
        self.stopSelenium = Button(button, text="Stop",
                                   command=self.stopSelenium)
        self.stopSelenium.pack(side=RIGHT, anchor=SE)

        self.serverStatus(Event())

    def updateServerCommand(self):
        args = self.buildServerStartCommand()
        self.serverCommand.config(state="normal")
        self.serverCommand.delete(0, len(self.serverCommand.get()))
        self.serverCommand.insert(0, args)
        self.serverCommand.config(state="readonly")
        
    def buildServerStartCommand(self):
        if os.environ.has_key("JAVA_HOME"):
            java = os.path.join(os.environ["JAVA_HOME"], "bin", "java")
        else:
            java = "java"
        # http://wiki.openqa.org/display/SIDE/record+and+assert+Ext+JS
        #args = [java, r"-jar", r"selenium-server.jar", r"-userExtensions", r"user-extensions.js", r"-singlewindow", "-port", "%s" % self.ipPort.get()]
        args = [java, r"-jar", r"selenium-server.jar", r"-singlewindow",
                "-port", "%s" % self.ipPort.get()]
        if self.radioLog.get() == "File":
            args.append("-log")
            args.append(self.logFilename.get())
        return tuple(args)
        
    def startSelenium(self):
        """ Start the Selenium server """
        os.chdir(r"../server/")
        args = self.buildServerStartCommand()
        self.startSelenium.config(state="disabled")
        self.seleniumServer = Popen(args)
        os.chdir(r"../scripts/")
        # Crude wait to give the server time to start
        time.sleep(5)
        self.serverStatus(Event())
        
    def stopSelenium(self):
        """ Stop the Selenium server """
        if self.seleniumServer != 0:
            self.seleniumServer.terminate()
            self.seleniumServer = 0
            self.serverStatus(Event())
            return
        if sys.platform[:5] == "linux":
            result = os.popen("ps x").readlines()
            for line in result:
                if "selenium" in line and "java" in line:
                    pid = line.split()[0]
                    os.system("kill %s" % pid)
                    print "Stopping process %s started with command %s" % (pid,
                                                                           line)
            self.serverStatus(Event())
            return
    
    def onPressServerLog(self):
        if self.radioLog.get() == "None":
            self.logFilename.config(state="readonly")
        else:
            self.logFilename.config(state="normal")
        self.updateServerCommand()
    
    # a file with one browser detail on each line
    # The browser name is first followed by the command to pass to selenium to start the browser 
    def getBrowserDetails(self):
        source = open("../data/browser.txt", "r")
        values = source.readlines()
        source.close()
        browserList = []
        for browser in values:
            details = browser.split(",")
            if len(details) == 2:
                browserList.append((details[0].strip(), details[1].strip()))
        return browserList

    def browser(self, panel):
        # See http://svn.openqa.org/fisheye/browse/~raw,r=2335/selenium-rc/website/src/main/webapp/experimental.html
        browserList = self.getBrowserDetails()
        self.radioB = StringVar()
        Label(panel, text="Browser").pack(side=TOP)
        for browser in browserList:
            Radiobutton(panel, text=browser[0], command=self.onPressBrowser,
                        value=browser[1],
                        variable=self.radioB).pack(side=TOP, anchor=W)
        path = Frame(panel)
        path.pack(side=TOP, fill=X)
        Label(path, text="Path to custom Browser").pack(side=TOP, anchor=W)
        self.browserPath = Entry(path, width=40)
        self.browserPath.insert(0, "<<enter path to executable here>>")
        self.browserPath.config(state="readonly")
        self.browserPath.pack(side=TOP, anchor=W, expand=YES, fill=X)
        self.radioB.set("*chrome")
        button = Frame(panel)
        button.pack(side=TOP, fill=BOTH)
        Button(button, text="Run", command=self.run).pack(side=RIGHT, anchor=SE)
        Button(button, text="Quit", command=self.quit).pack(side=RIGHT, anchor=SE)

    def onPressBrowser(self):
        if self.radioB.get() == "*custom":
            self.browserPath.config(state="normal")
        else:
            self.browserPath.config(state="readonly")
    
    def writeTestCasesForClass(self, module, details):
        """ Save details of the tests run """
        try:
            source = open("../tests/%s.txt" % details['class'], "w")
        except:
            print "Failed to write to file ../tests/%s.txt" % details["class"]
        for tests in details["tests"]:
            source.write("%s, %s\n" % (tests["name"], tests["state"]))

import tkSimpleDialog

class SelectTestWindow(tkSimpleDialog.Dialog):
    def __init__(self, parent, module, details):
        self.module = module
        self.details = details
        tkSimpleDialog.Dialog.__init__(self, parent)

    def body(self, parent):
        self.testList = []
        self.slectedList = []
        self.winfo_toplevel().title("%s test cases" % self.module)
        Label(parent, text="Watch this space...").grid(row =0)
        testPanel = Frame(parent, borderwidth=2, relief=SUNKEN)
        testPanel.grid(row=0, column=0, sticky=NSEW)
        self.testcasePanel(testPanel)

    def buttonbox(self):
        box = Frame(self)

        w = Button(box, text="OK", width=10, command=self.ok, default=ACTIVE)
        w.pack(side=LEFT, padx=5, pady=5)

        self.bind("<Return>", self.ok)

        box.pack()

    def toggleButton(self):
        i = 0
        for testcase in self.testcases:
            # Set the state of the testcase depending upon the checkbox 
            if self.checkboxModules[i].get() == 1:
                testcase["state"] = True
            else:
                testcase["state"] = False
            i += 1

    def testcasePanel(self, panel):
        Label(panel,
              text="Select the test cases that you would like to run.").pack(side=TOP,
                                                                             anchor=W)
        detailPanel = Frame(panel)
        detailPanel.pack(side=TOP, anchor=W, fill=X)
        self.checkboxModules = []
        i = 0
        self.testcases = self.details["tests"]
        for test in self.testcases:
            var = IntVar()
            chk = Checkbutton(detailPanel, text=test["name"], variable=var,
                              command=self.toggleButton)
            if test["state"]:
                chk.select()
            self.checkboxModules.append(var)
            chk.grid(row=i//2, column=i%2*2, sticky=NW)
            i += 1

if __name__ == "__main__":
    # Do we have any command-line arguments?
    args = sys.argv
    if args[1:]:
        # Yes: we are running the tests from the CLI (e.g. from Hudson)
        # The 1st argument is taken to be the config file:
        config_filename = args[1]
        exec("from %s import Settings" % config_filename)
        testSettings = Settings()
        browser = testSettings.radioB
        SahanaTest.setUpHierarchy(browser,
                                  testSettings.browserPath,
                                  testSettings.ipAddr,
                                  testSettings.ipPort,
                                  testSettings.URL + testSettings.app
                                 )
        # When running non-interactively, Username/Password are blank
        SahanaTest.useSahanaAccount("",
                                    "",
                                   )
        testConfig = TestConfig()
        moduleList = testConfig.getTestModuleDetails()
        testList = testConfig.getTestCasesToRun(moduleList)
        suite = testConfig.suite
        for testModule in testList: # dotted notation module.class
            testConfig.overrideClassSortList(testModule["class"],
                                             testModule["tests"])
        # Invoke TestRunner
        buf = StringIO.StringIO()
        try:
            report_format = args[2]
        except:
            report_format = "html"

        if report_format == "xml": # Arg 2 is used to generate xml output for jenkins
            runner = XMLTestRunner(file("../results/regressionTest-%s.xml" % (browser.replace("*", "")),
                                                                              "w"))
            runner.run(suite)

        elif report_format == "html":
            runner = HTMLTestRunner.HTMLTestRunner(
                        stream=buf,
                        title="<Sahana Eden Test>",
                        description="Suite of regressions tests for Sahana Eden."
                        )
            fileName = "../results/regressionTest-%s-%s.html" % (browser.replace("*", ""),
                                                                 time.strftime("%Y%m%d-%H%M%S"))
            file = open(fileName, "w")
            runner.run(suite)
            # check out the output
            byte_output = buf.getvalue()
            # output the main test output for debugging & demo
            # print byte_output
            # HTMLTestRunner pumps UTF-8 output
            output = byte_output.decode("utf-8")
            file.write(output)

        SahanaTest.selenium.stop()
    else:
        # No: we should bring up the GUI for interactive control
        TestWindow().mainloop()
