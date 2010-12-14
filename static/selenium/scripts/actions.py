import unittest, time, re

class Action:
    def login(self, test, username, password, reveal=True):
        # TODO add test for no user logged in, if user logged in check that it is different from username
        sel = test.selenium
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
        # TODO add test for user to be logged in
        sel = test.selenium
        sel.click("link=Logout")
        sel.wait_for_page_to_load("30000")

    def searchUser(self, test, searchString, expected):
        sel = test.selenium
        result = ""
        # TODO only open this page if on another page
        sel.open("/eden/admin/user")
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
        self.searchUniqueUser(test, email)

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
        test.assertTrue(sel.is_element_present(element))
        print "Form element %s is present" % (id)
        
    # Method to check that form button is present
    def button(self, test, name):
        sel = test.selenium
        element = '//input[@value="%s"]' % (name)
        test.assertTrue(sel.is_element_present(element))
        print "%s button is present" % (name)
        
    # Method to check that the help message is displayed
    def helpBallon(self, test, helpTitle):
        sel = test.selenium
        element = "//div[contains(@title,'%s')]" % (helpTitle)
        test.assertTrue(sel.is_element_present(element))
        sel.mouse_over(element)
        test.assertFalse(sel.is_element_present(element))
        print "Help %s is present" % (helpTitle)

        