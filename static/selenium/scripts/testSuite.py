"""
Copyright 2006 ThoughtWorks, Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import unittest
import sys
import StringIO

import HTMLTestRunner
from selenium import selenium

class SahanaTestSuite():
        
    def startSelenium(className, browser, path, ipaddr, ipport, webURL):
        if browser == "*custom":
            browser += " " + path
        print "selenium %s %s %s %s" % (ipaddr, ipport, browser, webURL)
        className.selenium = selenium(ipaddr, ipport, browser, webURL)
        className.selenium.start()
    startSelenium = classmethod(startSelenium)

    def setSahanaAdminDetails(className, email, password):
        className.user = email
        className.password = password
    setSahanaAdminDetails = classmethod(setSahanaAdminDetails)

    def stopSelenium(className):        
        className.selenium.stop()
    stopSelenium = classmethod(stopSelenium)
                
    def test_main(self, testList):

        testLoader = unittest.defaultTestLoader
        self.suite = unittest.TestSuite()
        for testName in testList: #dotted notation module[.class[.method]]
            self.suite.addTests(testLoader.loadTestsFromName(testName))
        # Invoke TestRunner
        buf = StringIO.StringIO()
        runner = HTMLTestRunner.HTMLTestRunner(
                    stream=buf,
                    title='<Sahana Eden Test>',
                    description='Suite of regressions tests for Sahana Eden.'
                    )
        runner.run(self.suite)
        # check out the output
        byte_output = buf.getvalue()
        # output the main test output for debugging & demo
        # print byte_output
        # HTMLTestRunner pumps UTF-8 output
        output = byte_output.decode('utf-8')
        file = open('../results/regressionTest.html','w')
        file.write(output)
        
