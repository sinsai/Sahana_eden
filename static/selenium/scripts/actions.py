import unittest, time, re

class Action(unittest.TestCase):
    def __init__ (self, selenium):
        self.sel = selenium
        
    def login(self, username, password, reveal=True):
        sel = self.sel
        if sel.is_element_present("link=Logout"):
            # Already logged in check the account
            if sel.is_element_present("link=%s" % username):
                # already logged in
                return
            else:
                # logged in but as a different user
                self.logout()
        sel.open("/eden/default/user/login")
        sel.click("auth_user_email")
        sel.type("auth_user_email", username)
        sel.type("auth_user_password", password)
        sel.click("//input[@value='Submit']")
        msg = "Unable to log in as " + username
        if reveal:
            msg += " with password " + password
        sel.wait_for_page_to_load("30000")
        self.assertTrue(self.successMsg("Logged in"),msg)

    def logout(self):
        sel = self.sel
        if sel.is_element_present("link=Logout"):
            sel.click("link=Logout")
            sel.wait_for_page_to_load("30000")

    def search(self, searchString, expected):
        sel = self.sel
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
        else: self.fail("time out: Looking for %s within %s" % (expected, result ))
        
    def searchUnique(self, uniqueName):
        self.search(uniqueName, r"1 entries")
        
    def searchUser(self, searchString, expected):
        sel = self.sel
        result = ""
        # TODO only open this page if on another page
        sel.open("/eden/admin/user")
        self.search(searchString, expected)

    def searchUniqueUser(self, userName):
        self.searchUser(userName, r"1 entries")
        
    def clearSearch(self):
        sel = self.sel
        sel.run_script("oTable = $('#list').dataTable();  oTable.fnFilter( 'Clearing...' );")
        self.searchUser('', r"entries")
        
    def addUser(self, first_name, last_name, email, password):
        first_name = first_name.strip()
        last_name = last_name.strip()
        email = email.strip()
        password = password.strip()
        
        sel = self.sel
        # TODO only open this page if on another page
        sel.open("/eden/admin/user")
        self.assertTrue(sel.is_element_present("show-add-btn"))
        sel.click("show-add-btn")
        sel.type("auth_user_first_name", first_name)
        sel.type("auth_user_last_name", last_name)
        sel.select("auth_user_language", "label=English")
        sel.type("auth_user_email", email)
        sel.type("auth_user_password", password)
        sel.click("//input[@value='Save']")
        sel.wait_for_page_to_load("30000")
        msg = "Unable to create user " + first_name + " " + last_name + " with email " + email
        self.assertTrue(self.successMsg("User added"),msg)
        self.searchUniqueUser(email)
        self.assertTrue(re.search(r"Showing 1 to 1 of 1 entries", sel.get_text("//div[@class='dataTables_info']")))
        print "User %s created" % (email)

    def addRole(self, email, roles):
        email = email.strip()
        roles = roles.strip()
        roleList = roles.split(' ')
        
        sel = self.sel
        self.searchUniqueUser(email)
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
            self.assertTrue(self.successMsg("User Updated"),msg)
            print "User %s added to group %s" % (email, role.strip())
        sel.open("/eden/admin/user")

    def delUser(self, email):
        email = email.strip()
        sel = self.sel
        sel.open("/eden/admin/user")
        self.searchUnique(email)

        sel.click("link=Delete")
        self.assertTrue(re.search(r"^Sure you want to delete this object[\s\S]$", sel.get_confirmation()))
        self.assertTrue(self.successMsg("User deleted"))
        self.searchUser(email, r"No matching records found")
        print "User %s deleted" % (email)

    # Method to locate a message in a div with a class given by type
    def findMsg(self, message, type):
        sel = self.sel
        for cnt in range (60):
            i = 1
            while sel.is_element_present('//div[@class="%s"][%s]' % (type, i)):
                if re.search(message, sel.get_text('//div[@class="%s"][%s]' % (type, i))): return True
                i += 1
            time.sleep(1)
        return False
    
    # Method used to check for confirmation messages
    def successMsg(self, message):
        return self.findMsg(message, "confirmation")

    # Method used to check for error messages
    def errorMsg(self, message):
        return self.findMsg(message, "error")

    # Method to check that form element is present
    def element(self, type, id):
        sel = self.sel
        element = '//%s[@id="%s"]' % (type, id)
        self.assertTrue(sel.is_element_present(element), "%s element %s is missing" % (type, id))
        print "Form %s element %s is present" % (type, id)
        
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
            self.assertFalse(sel.get_text(element),errMsg)
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
        for (type, id) in elementList:
            self.element(type, id)
        for name in buttonList:
            self.button(name)
        for title in helpList:
            self.helpBallon(title)
