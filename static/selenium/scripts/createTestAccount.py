
import unittest, time, re
import testSuite
import actions

class CreateTestAccount(unittest.TestCase):
    

    def setUp(self):
        self.selenium = testSuite.SahanaTestSuite.selenium
        self.user = testSuite.SahanaTestSuite.user;
        self.password = testSuite.SahanaTestSuite.password;
        self.action = actions.Action()
    
    def test_create_test_account(self):
        sel = self.selenium
        
        # *** NOTE this script needs to be run by a user with Administrator privileges. END NOTE ***
        self.action.login(self, self.user, self.password, False)
        # This script creates a test account with the user name of admin@example.com the account is given administrator rights and will be used throughout the testing suite.
        # The user admin@example.com will be deleted by the "Delete Test Account" test case.
        sel.open("/eden/admin/user")
        self.failUnless(sel.is_element_present("show-add-btn"))
        sel.click("show-add-btn")
        sel.type("auth_user_first_name", "Admin")
        sel.type("auth_user_last_name", "User")
        sel.select("auth_user_language", "label=English")
        sel.type("auth_user_email", "admin@example.com")
        sel.type("auth_user_password", "testing")
        sel.click("//input[@value='Save']")
        sel.wait_for_page_to_load("30000")
        # Now that the user has been created search for this user using the list filter so that the "Administrator" roll can be added to it.
        # The search filter is part of the http://datatables.net/ JavaScript getting it to work with Selenium needs a bit of care.
        # Entering text in the filter textbox doesn't always trigger off the filtering and it is not possible with this method to clear the filter.
        # The solution is to put in a call to the DataTables API, namely the fnFilter function
        # However, the first time that the fnFilter() is called in the testing suite it doesn't complete the processing, hence it is called twice.
        sel.run_script("oTable = $('#list').dataTable();  oTable.fnFilter( '' );")
        sel.run_script("oTable = $('#list').dataTable();  oTable.fnFilter( 'admin@example.com' );")
        for i in range(60):
            try:
                if re.search(r"^[\s\S]*1 entries[\s\S]*$", sel.get_text("//div[@class='dataTables_info']")): break
            except: pass
            time.sleep(1)
        else: self.fail("time out")
        sel.click("link=Open")
        sel.wait_for_page_to_load("30000")
        sel.click("//div[@id='content']/a[2]")
        sel.wait_for_page_to_load("30000")
        sel.click("auth_membership_group_id")
        sel.select("auth_membership_group_id", "label=1: Administrator")
        sel.click("//input[@value='Add']")
        sel.wait_for_page_to_load("30000")
        # Log out from the current "Administrator" user and log back in for the remaining test cases as admin@example.com
        sel.click("link=Logout")
        sel.wait_for_page_to_load("30000")
        self.action.login(self, "admin@example.com", "testing" )
        sel.click("link=Logout")
        sel.wait_for_page_to_load("30000")
    


if __name__ == "__main__":
    unittest.main()
