import unittest, time, re

class Action:
    def login(self, test, username, password, reveal=True):
        sel = test.selenium
        if sel.is_element_present("link=Logout"):
            # Already logged in check the account
            if sel.is_element_present("link=%s" % username):
                # already logged in
                return
            else:
                # logged in but as a different user
                self.logout(test)
        sel.open("/eden/default/user/login")
        sel.click("auth_user_email")
        sel.type("auth_user_email", username)
        sel.type("auth_user_password", password)
        sel.click("//input[@value='Submit']")
        msg = "Unable to log in as " + username
        if reveal:
            msg += " with password " + password
        sel.wait_for_page_to_load("30000")
        test.assertTrue(self.successMsg(test, "Logged in"),msg)

    def logout(self, test):
        sel = test.selenium
        if sel.is_element_present("link=Logout"):
            sel.click("link=Logout")
            sel.wait_for_page_to_load("30000")

    def search(self, test, searchString, expected):
        sel = test.selenium
        # The search filter is part of the http://datatables.net/ JavaScript getting it to work with Selenium needs a bit of care.
        # Entering text in the filter textbox doesn't always trigger off the filtering and it is not possible with this method to clear the filter.
        # The solution is to put in a call to the DataTables API, namely the fnFilter function
        # However, the first time that the fnFilter() is called in the testing suite it doesn't complete the processing, hence it is called twice.
        sel.run_script("oTable = $('#list').dataTable();  oTable.fnFilter( '' );")
        time.sleep(1)
        sel.run_script("oTable = $('#list').dataTable();  oTable.fnFilter( '"+searchString+"' );")
        time.sleep(1)
        for i in range(12):
            try:
                result = sel.get_text("//div[@id='table-container']")
                if  expected in result: break
            except: pass
            time.sleep(5)
        else: test.fail("time out: Looking for %s within %s" % (expected, result ))
        
    def searchUnique(self, test, uniqueName):
        self.search(test, uniqueName, r"1 entries")
        
    def searchUser(self, test, searchString, expected):
        sel = test.selenium
        result = ""
        # TODO only open this page if on another page
        sel.open("/eden/admin/user")
        self.search(test, searchString, expected)

    def searchUniqueUser(self, test, userName):
        self.searchUser(test, userName, r"1 entries")
        
    def clearSearch(self, test):
        sel = test.selenium
        sel.run_script("oTable = $('#list').dataTable();  oTable.fnFilter( 'Clearing...' );")
        self.searchUser(test, '', r"entries")
        
    def addUser(self, test, first_name, last_name, email, password):
        first_name = first_name.strip()
        last_name = last_name.strip()
        email = email.strip()
        password = password.strip()
        
        sel = test.selenium
        # TODO only open this page if on another page
        sel.open("/eden/admin/user")
        test.assertTrue(sel.is_element_present("show-add-btn"))
        sel.click("show-add-btn")
        sel.type("auth_user_first_name", first_name)
        sel.type("auth_user_last_name", last_name)
        sel.select("auth_user_language", "label=English")
        sel.type("auth_user_email", email)
        sel.type("auth_user_password", password)
        sel.click("//input[@value='Save']")
        sel.wait_for_page_to_load("30000")
        msg = "Unable to create user " + first_name + " " + last_name + " with email " + email
        test.assertTrue(self.successMsg(test, "User added"),msg)
        self.searchUniqueUser(test, email)
        test.assertTrue(re.search(r"Showing 1 to 1 of 1 entries", sel.get_text("//div[@class='dataTables_info']")))
        print "User %s created" % (email)

    def addRole(self, test, email, roles):
        email = email.strip()
        roles = roles.strip()
        roleList = roles.split(' ')
        sel = test.selenium
        self.searchUniqueUser(test, email)
        sel.click("link=Open")
        sel.wait_for_page_to_load("30000")
        sel.click("//div[@id='content']/a[2]")
        sel.wait_for_page_to_load("30000")
        sel.click("auth_membership_group_id")
        for role in roleList:
            sel.select("auth_membership_group_id", "value="+str(role.strip()))
            sel.click("//input[@value='Add']")
            sel.wait_for_page_to_load("30000")
            msg = "Failed to add role %s to user %s" % (role.strip() , email)
            test.assertTrue(self.successMsg(test, "User Updated"),msg)
            print "User %s added to group %s" % (email, role.strip())
        sel.open("/eden/admin/user")

    def delUser(self, test, email):
        email = email.strip()
        sel = test.selenium
        sel.open("/eden/admin/user")
        self.searchUnique(test, email)

        sel.click("link=Delete")
        test.assertTrue(re.search(r"^Sure you want to delete this object[\s\S]$", sel.get_confirmation()))
        test.assertTrue(self.successMsg(test,"User deleted"))
        self.searchUser(test, email, r"No matching records found")
        print "User %s deleted" % (email)

    # Method to locate a message in a div with a class given by type
    def findMsg(self, test, message, type):
        sel = test.selenium
        for cnt in range (60):
            i = 1
            while sel.is_element_present('//div[@class="%s"][%s]' % (type, i)):
                if re.search(message, sel.get_text('//div[@class="%s"][%s]' % (type, i))): return True
                i += 1
            time.sleep(1)
        return False
    
    # Method used to check for confirmation messages
    def successMsg(self, test, message):
        return self.findMsg(test, message, "confirmation")

    # Method used to check for error messages
    def errorMsg(self, test, message):
        return self.findMsg(test, message, "error")

    # Method to check that form element is present
    def element(self, test, type, id):
        sel = test.selenium
        element = '//%s[@id="%s"]' % (type, id)
        test.assertTrue(sel.is_element_present(element), "%s element %s is missing" % (type, id))
        print "Form %s element %s is present" % (type, id)
        
    # Method to click on a tab
    def clickTab(self, test, name):
        sel = test.selenium
        element = "//div[@id='rheader_tabs']/span/a[text()='%s']" % (name)
        sel.click(element)
        sel.wait_for_page_to_load("30000")
        
    # Method to check button link
    def btnLink(self, test, id, name):
        sel = test.selenium
        element = '//a[@id="%s"]' % (id)
        errMsg = "%s button is missing" % (name)
        test.assertTrue(sel.is_element_present(element), errMsg)
        test.assertTrue(sel.get_text(element),errMsg)
        print "%s button is present" % (name)
        
    # Method to check button link is not present
    def noBtnLink(self, test, id, name):
        sel = test.selenium
        element = '//a[@id="%s"]' % (id)
        errMsg = "Unexpected presence of %s button" % (name)
        if sel.is_element_present(element):
            test.assertFalse(sel.get_text(element),errMsg)
        print "%s button is not present" % (name)

    # Method to check that form button is present
    def button(self, test, name):
        sel = test.selenium
        element = '//input[@value="%s"]' % (name)
        errmsg = "%s button is missing" % (name)
        test.assertTrue(sel.is_element_present(element), errmsg)
        print "%s button is present" % (name)
        
    # Method to check that the help message is displayed
    def helpBallon(self, test, helpTitle):
        sel = test.selenium
        element = "//div[contains(@title,'%s')]" % (helpTitle)
        test.assertTrue(sel.is_element_present(element))
        sel.mouse_over(element)
        test.assertFalse(sel.is_element_present(element), "Help %s is missing" % (helpTitle))
        print "Help %s is present" % (helpTitle)

    # Method to check that the layout of a form
    def checkForm (self, test, elementList, buttonList, helpList):
        for (type, id) in elementList:
            self.element(test, type, id)
        for name in buttonList:
            self.button(test, name)
        for title in helpList:
            self.helpBallon(test, title)
