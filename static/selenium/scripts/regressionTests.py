from Tkinter import *
from subprocess import call

from testSuite import SahanaTestSuite
from sahanaTest import SahanaTest
import thread
import unittest

import os
import thread
import time
from subprocess import Popen

class TestWindow(Frame):

    def runTestSuite(self):
        # call static method of the base class for all Sahana test case classes
        # this method will ensure that one Selenium instance exists and can be shared 
        SahanaTest.setUpHierarchy(self.radioB.get(),
                                  self.browserPath.get(),
                                  self.ipAddr.get(),
                                  self.ipPort.get(),
                                  self.URL.get()
                                  )
        SahanaTestSuite.setSahanaAdminDetails(self.adminUser.get(),
                                              self.adminPassword.get(),
                                             )
        self.clean = False
        test = SahanaTestSuite()
        test.test_main(self.getTestModules())
        call(["firefox", os.path.join("..", "results", "regressionTest.html")])
        SahanaTest.selenium.stop() # Debug comment out to keep the Selenium window open 
        self.clean = True
    
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
        Label(panel, text="To run the tests a user with admin rights needs to be provided.").pack(side=TOP, anchor=W)
        Label(panel, text="If this is left blank then the user of testing@example.com will be used.").pack(side=TOP, anchor=W)
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
        
    # a file with test details listed per line, with the format being:
    # <display name>, <dotted notation of the test>
    # any line not meeting this criteria will be ignored.
    # <dotted notation of the test> is:
    # module optionally followed by the class name optionally followed by the method
    # OR: module[.class[.method]]
    def getTestModuleDetails(self):
        source = open("../data/testModules.txt", "r")
        modules = source.readlines()
        source.close()
        moduleList =[]
        for module in modules:
            details = module.split(',')
            if len(details) == 2:
                moduleList.append((details[0].strip(),details[1].strip()))
        return tuple(moduleList)

    def getTestModules(self):
        i = 0
        testModuleList = []
        for module in self.checkboxModules:
            if module.get() == 1:
                testModuleList.append(self.moduleList[i][1].strip())
            i += 1
        return tuple(testModuleList)
        
    def testModulepanel(self, panel):
        self.moduleList = self.getTestModuleDetails()
        Label(panel, text="Test Modules").pack(side=TOP)
        Label(panel, text="Select the test modules that you would like to run.").pack(side=TOP, anchor=W)
        detailPanel = Frame(panel)
        detailPanel.pack(side=TOP, anchor=W, fill=X)
        self.checkboxModules = []
        i = 0
        for module in self.moduleList:
            var = IntVar()
            chk = Checkbutton(detailPanel, text=module[0], variable=var)
            self.checkboxModules.append(var)
            if i % 2:
                # Even
                chk.grid(row=i - 1, column=1, sticky=NW)
            else:
                # Odd
                chk.grid(row=i, column=0, sticky=NW)
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
        Radiobutton(logPanel, text="No Logging", value="None", command=self.onPressServerLog, variable=self.radioLog).pack(side=TOP, anchor = W)
        Radiobutton(logPanel, text="Log to file", value="File", command=self.onPressServerLog, variable=self.radioLog).pack(side=TOP, anchor = W)
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
        self.startSelenium = Button(button, text="Start", command=self.startSelenium)
        self.startSelenium.pack(side=RIGHT, anchor=SE)
        self.stopSelenium = Button(button, text="Stop", command=self.stopSelenium)
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
        args = [java, r"-jar", r"selenium-server.jar", r"-singlewindow", "-port", "%s" % self.ipPort.get()]
        if self.radioLog.get() == "File":
            args.append("-log")
            args.append(self.logFilename.get())
        return tuple(args)
        
    def startSelenium(self):
        # start the Selenium server
        os.chdir(r"../server/")
        args = self.buildServerStartCommand()
        self.startSelenium.config(state="disabled")
        self.seleniumServer = Popen(args)
        # crude wait to give the server time to start
        os.chdir(r"../scripts/")
        time.sleep(5)
        self.serverStatus(Event())
        
    def stopSelenium(self):
        # stop the Selenium server
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
                    print "Stopping process %s started with command %s" % (pid, line)
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
            Radiobutton(panel, text=browser[0], command=self.onPressBrowser, value=browser[1], variable=self.radioB).pack(side=TOP, anchor=W)
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
    
    def run(self):
        thread.start_new(self.runTestSuite, ())

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

if __name__ == "__main__":
    TestWindow().mainloop()
