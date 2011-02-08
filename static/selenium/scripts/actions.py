import unittest, time, re
from selenium import selenium

class Action(unittest.TestCase):
    def __init__ (self, selenium):
        self.sel = selenium
        self._diag = False # make True for profiling diagnostics
        
    def openReport(self):
        if self._diag:
            self._diag_SearchResults = open('diagTestResults.txt', 'a')
            self._diag_SearchResults.write(time.strftime('New Search run %d %b %Y (%H:%M:%S)\n'))
    
    def closeReport(self, msg):
        if self._diag:
            self._diag_SearchResults.write(msg)
            self._diag_SearchResults.close()

    def login(self, username, password, reveal=True):
        print "Logging in as user: " + username
        sel = self.sel
        if sel.is_element_present("link=Logout"):
            # Already logged in check the account
            if sel.is_element_present("link=%s" % username):
                # already logged in
                return
            else:
                # logged in but as a different user
                self.logout()
        sel.open("default/user/login")
        sel.click("auth_user_email")
        sel.type("auth_user_email", username)
        sel.type("auth_user_password", password)
        sel.click("//input[@value='Submit']")
        msg = "Unable to log in as " + username
        if reveal:
            msg += " with password " + password
        self.assertTrue(self.successMsg("Logged in"),msg)

    def logout(self):
        sel = self.sel
        if sel.is_element_present("link=Logout"):
            sel.click("link=Logout")
            self.successMsg("Logged out")
#            sel.wait_for_page_to_load("30000")

    def _performSearch(self, searchString):
        # The search filter is part of the http://datatables.net/ JavaScript getting it to work with Selenium needs a bit of care.
        # Entering text in the filter textbox doesn't always trigger off the filtering and it is not possible with this method to clear the filter.
        # The solution is to put in a call to the DataTables API, namely the fnFilter function
        # However, the first time that the fnFilter() is called in the testing suite it doesn't complete the processing, hence it is called twice.
        sel = self.sel
        clearString = ""
        if searchString == '': clearString = "Clearing..."
        # First clear the search field and add a short pause
        sel.run_script("oTable = $('#list').dataTable();  oTable.fnFilter( '%s' );" % clearString)
        time.sleep(1)
        self._diag_sleepTime += 1
        # Now trigger off the true search
        sel.run_script("oTable = $('#list').dataTable();  oTable.fnFilter( '%s' );" % searchString)
        for i in range(10):
            if not sel.is_visible('list_processing'):
                found = True
                return True
            time.sleep(1)
            self._diag_sleepTime += 1
        return False

    def search(self, searchString, expected):
        sel = self.sel
        self._diag_sleepTime = 0
        self._diag_performCalls = 0
        found = False
        result = ""
        # perform the search it should work first time but, give it up to three attempts before giving up
        for i in range (3):
            self._diag_performCalls += 1
            found = self._performSearch(searchString)
            if found:
                break
        if not found:
            if self._diag:
                self._diag_SearchResults.write("%s\tFAILED\t%s\t%s\n" % (searchString, self._diag_sleepTime, self._diag_performCalls))
            self.fail("time out search didn't respond, whilst searching for %s" % searchString)
        else:
            if self._diag:
                self._diag_SearchResults.write("%s\tSUCCEEDED\t%s\t%s\n" % (searchString, self._diag_sleepTime, self._diag_performCalls))
        # The search has returned now read the results
        try:
            result = sel.get_text("//div[@id='table-container']")
        except:
            self.fail("No search data found, whilst searching for %s" % searchString)
        return expected in result

        
    def searchUnique(self, uniqueName):
        self.search(uniqueName, r"1 entries")
        
    def clearSearch(self):
        self.search("", r"entries")
        
    def registerUser(self, first_name, last_name, email, password):
        first_name = first_name.strip()
        last_name = last_name.strip()
        email = email.strip()
        password = password.strip()
        
        sel = self.sel
        sel.open("default/user/register")
        sel.type("auth_user_first_name", first_name)
        sel.type("auth_user_last_name", last_name)
        sel.select("auth_user_language", "label=English")
        sel.type("auth_user_email", email)
        sel.type("auth_user_password", password)
        sel.type("password_two", password)
        sel.click("//input[@value='Submit']")
        sel.wait_for_page_to_load("30000")
        msg = "Unable to register user %s %s with email %s" % (first_name, last_name, email)
        self.assertTrue(self.successMsg("Registration successful"), msg)
        sel.open("admin/user")
        self.searchUnique(email)
        self.assertTrue(re.search(r"Showing 1 to 1 of 1 entries", sel.get_text("//div[@class='dataTables_info']")))
        print "User %s created" % (email)

    def addUser(self, first_name, last_name, email, password):
        first_name = first_name.strip()
        last_name = last_name.strip()
        email = email.strip()
        password = password.strip()
        
        sel = self.sel
        # TODO only open this page if on another page
        sel.open("admin/user")
        self.assertTrue(sel.is_element_present("show-add-btn"))
        sel.click("show-add-btn")
        sel.type("auth_user_first_name", first_name)
        sel.type("auth_user_last_name", last_name)
        sel.select("auth_user_language", "label=English")
        sel.type("auth_user_email", email)
        sel.type("auth_user_password", password)
        sel.type("password_two", password)
        sel.click("//input[@value='Save']")
        sel.wait_for_page_to_load("30000")
        msg = "Unable to create user %s %s with email %s" % (first_name, last_name, email)
        self.assertTrue(self.successMsg("User added"), msg)
        self.searchUnique(email)
        self.assertTrue(re.search(r"Showing 1 to 1 of 1 entries", sel.get_text("//div[@class='dataTables_info']")))
        print "User %s created" % (email)

    def addRole(self, email, roles):
        email = email.strip()
        roles = roles.strip()
        roleList = roles.split(" ")
        
        sel = self.sel
        self.searchUnique(email)
        self.assertEqual("Roles", sel.get_text("//table[@id='list']/tbody/tr[1]/td[1]/a[2]"))
        sel.click("//table[@id='list']/tbody/tr[1]/td[1]/a[2]")
        sel.wait_for_page_to_load("30000")
        for role in roleList:
            sel.click("//input[@name='roles' and @value='%s']" % role.strip())
        sel.click("//input[@value='Save']")
        sel.wait_for_page_to_load("30000")
        # @ToDo: Message to get all roles (if multiple) not just last 1
        msg = "Failed to add role %s to user %s" % (role.strip() , email)
        self.assertTrue(self.successMsg("User Updated"), msg)
        print "User %s added to group %s" % (email, role.strip())
        sel.open("admin/user")

    def delUser(self, email):
        email = email.strip()
        print "Deleting user %s" % email
        sel = self.sel
        sel.open("admin/user")
        self.searchUnique(email)

        sel.click("link=Delete")
        self.assertTrue(re.search(r"^Sure you want to delete this object[\s\S]$", sel.get_confirmation()))
        self.assertTrue(self.successMsg("User deleted"))
        self.search(email, r"No matching records found")
        print "User %s deleted" % (email)

    def deleteObject(self, page, objName, type="Object"):
        sel = self.sel
        # need the following line which reloads the page otherwise the search gets stuck  
        sel.open(page)
        try:
            self.searchUnique(objName)
            sel.click("link=Delete")
            self.assertTrue(re.search(r"^Sure you want to delete this object[\s\S]$", sel.get_confirmation()))
            if self.findResponse("%s deleted" % type, "Integrity error:"):
                print "%s %s deleted" % (type, objName)
            else:
                print "Failed to delete %s %s" % (type, objName)
        except:
            print "Failed to delete %s %s from page %s" % (type, objName, page)

    # Method to check the details that are displayed in the heading
    def checkHeading(self, detailMap):
        sel = self.sel
        heading = sel.get_text("//div[@id='rheader']/div/table/tbody")
        searchString = ""
        for key, value in detailMap.items():
            msg = "Unable to find details of %s in the header of %s"
            self.assertTrue(key in heading, msg % (key, heading))
            self.assertTrue(value in heading, msg % (value, heading))

    # Method to save the details
    def saveForm(self, message=None):
        sel = self.sel
        sel.click("//input[@value='Save']")
        sel.wait_for_page_to_load("30000")
        if message != None:
            return self.successMsg(message)
    
    # Method to check each banner for the desired message
    def checkBanner(self, message, type):
        sel = self.sel
        i = 1
        while sel.is_element_present('//div[@class="%s"][%s]' % (type, i)):
            banner = sel.get_text('//div[@class="%s"][%s]' % (type, i))
            if message in banner:
                if self._diag:
                    self._diag_SearchResults.write("%s\tSUCCEEDED\t%s\t\n" % (message, self._diag_sleepTime))
                return True
            i += 1

    # Method to locate a message in a div with a class given by type
    def findMsg(self, message, type):
        sel = self.sel
        self._diag_sleepTime = 0
        for cnt in range (10):
            if self.checkBanner(message, type):
                return True
            time.sleep(1)
            self._diag_sleepTime += 1
        if self._diag:
            self._diag_SearchResults.write("%s\tFAILED\t%s\t\n" % (message, self._diag_sleepTime))
        return False
    
    # Method used to check for confirmation messages
    def successMsg(self, message):
        return self.findMsg(message, "confirmation")

    # Method used to check for error messages
    def errorMsg(self, message):
        return self.findMsg(message, "error")

    # Method to check on the response of an action by looking at the message
    def findResponse(self, successMsg, errorMsg):
        sel = self.sel
        sType = "confirmation"
        eType = "error"
        self._diag_sleepTime = 0
        for cnt in range (10):
            if self.checkBanner(successMsg, sType):
                return True
            if self.checkBanner(errorMsg, eType):
                return False
            time.sleep(1)
            self._diag_sleepTime += 1
        if self._diag:
            self._diag_SearchResults.write("%s\tFAILED\t%s\t\n" % (message, self._diag_sleepTime))
        raise UserWarning("Response not found")
        
    # Method to check that form element is present
    # The element parameter is a list of up to 4 elements
    # element[0] the type of HTML tag
    # element[1] the id associated with the HTML tag
    # element[2] *optional* the visibility of the HTML tag
    # element[3] *optional* the value or text of the HTML tag
    def element(self, element):
        sel = self.sel
        type = element[0]
        id = element[1]
        if (len(element) >= 3):
            visible = element[2] 
        else:
            visible = True
        if (len(element) >= 4):
            value = element[3] 
        else:
            value = None
        element = '//%s[@id="%s"]' % (type, id)
        if visible:
            if not sel.is_element_present(element): return "%s element %s is missing" % (type, id)
        if sel.is_visible(element) != visible: return "%s element %s doesn't have a visibility of %s"  % (type, id, visible)
        if value!= None:
            actual = sel.get_value(element)
            msg = "expected %s for element %s doesn't equal the actual value of %s" % (value, id, actual)
            if value != actual: return msg
        return True
                
    # Method to click on a tab
    def clickTab(self, name):
        sel = self.sel
        element = "//div[@id='rheader_tabs']/span/a[text()='%s']" % (name)
        sel.click(element)
        sel.wait_for_page_to_load("30000")
        
    # Method to check button link
    def btnLink(self, id, name):
        sel = self.sel
        element = '//a[@id="%s"]' % (id)
        errMsg = "%s button is missing" % (name)
        self.assertTrue(sel.is_element_present(element), errMsg)
        self.assertTrue(sel.get_text(element),errMsg)
        print "%s button is present" % (name)
        
    # Method to check button link is not present
    def noBtnLink(self, id, name):
        sel = self.sel
        element = '//a[@id="%s"]' % (id)
        errMsg = "Unexpected presence of %s button" % (name)
        if sel.is_element_present(element):
            self.assertFalse(sel.get_text(element), errMsg)
        print "%s button is not present" % (name)

    # Method to check that form button is present
    def button(self, name):
        sel = self.sel
        element = '//input[@value="%s"]' % (name)
        errmsg = "%s button is missing" % (name)
        self.assertTrue(sel.is_element_present(element), errmsg)
        print "%s button is present" % (name)
        
    # Method to check that the help message is displayed
    def helpBallon(self, helpTitle):
        sel = self.sel
        element = "//div[contains(@title,'%s')]" % (helpTitle)
        self.assertTrue(sel.is_element_present(element))
        sel.mouse_over(element)
        self.assertFalse(sel.is_element_present(element), "Help %s is missing" % (helpTitle))
        print "Help %s is present" % (helpTitle)

    # Method to check that the layout of a form
    def checkForm (self, elementList, buttonList, helpList):
        elements = []
        failed = []
        for element in elementList:
            result = self.element(element)
            if result == True:
                if len(element)>2 and element[2]: elements.append(element[1])
            else: failed.append(result)
        for name in buttonList:
            self.button(name)
        for title in helpList:
            self.helpBallon(title)
        if len(failed) > 0:
            msg = '/n'.join(failed)
            self.fail(msg)
        if len(elements) > 0:
            print "Verified the following form elements %s" % elements
