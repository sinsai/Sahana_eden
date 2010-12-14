import testSuite
import unittest, time, re
import actions

class DeleteTestAccount(unittest.TestCase):
    def setUp(self):
        self.action = actions.Action()
        self.verificationErrors = []
        self.selenium = testSuite.SahanaTestSuite.selenium
        self.user = testSuite.SahanaTestSuite.user;
        self.password = testSuite.SahanaTestSuite.password;
    
    def test_delete_test_account(self):
        sel = self.selenium
        # This test case will delete the users admin@example.com & user@example.com
        # It will log in as the default user, which requires the details to have been remembered by the browser.
        # If it is unable to log in as the default user or the default user doesn't have sufficient privileges then this test case will fail.
        self.action.login(self, self.user, self.password, False)
        sel.open("/eden/admin/user")
        # Ensure that the only user displayed is admin@example.com before deleting it
        # Call the fnFilter() twice to force it to work. See "Create Test Account" for more details
        sel.run_script("oTable = $('#list').dataTable();  oTable.fnFilter( '' );")
        sel.run_script("oTable = $('#list').dataTable(); oTable.fnFilter( 'admin@example.com' );")
        for i in range(60):
            try:
                if re.search(r"^[\s\S]*1 entries[\s\S]*$", sel.get_text("//div[@class='dataTables_info']")): break
            except: pass
            time.sleep(1)
        else: self.fail("time out")
        # The following asserts is needed in case the above waitFor times out
        self.failUnless(re.search(r"^[\s\S]*1 entries[\s\S]*$", sel.get_text("//div[@class='dataTables_info']")))
        self.failUnless(re.search(r"^[\s\S]*admin@example\.com[\s\S]*$", sel.get_text("//table[@class='display']")))
        sel.click("link=Delete")
        self.failUnless(re.search(r"^Sure you want to delete this object[\s\S]$", sel.get_confirmation()))
        # Ensure that the only user displayed is user@example.com before deleting it
        # Call the fnFilter() twice to force it to work. See "Create Test Account" for more details
        sel.run_script("oTable = $('#list').dataTable();  oTable.fnFilter( '' );")
        sel.run_script("oTable = $('#list').dataTable(); oTable.fnFilter( 'user@example.com' );")
        for i in range(60):
            try:
                if re.search(r"^[\s\S]*1 entries[\s\S]*$", sel.get_text("//div[@class='dataTables_info']")): break
            except: pass
            time.sleep(1)
        else: self.fail("time out")
        # The following asserts is needed in case the above waitFor times out
        self.failUnless(re.search(r"^[\s\S]*1 entries[\s\S]*$", sel.get_text("//div[@class='dataTables_info']")))
        self.failUnless(re.search(r"^[\s\S]*admin@example\.com[\s\S]*$", sel.get_text("//table[@class='display']")))
        sel.click("link=Delete")
        self.failUnless(re.search(r"^Sure you want to delete this object[\s\S]$", sel.get_confirmation()))
        # Clear the DataTables filter
        sel.run_script("oTable = $('#list').dataTable();  oTable.fnFilter( '' );")
        for i in range(60):
            try:
                if re.search(r"^[\s\S]*entries[\s\S]*$", sel.get_text("//div[@class='dataTables_info']")): break
            except: pass
            time.sleep(1)
        else: self.fail("time out")
        sel.click("link=Logout")
        sel.wait_for_page_to_load("30000")
    
    def tearDown(self):
        self.assertEqual([], self.verificationErrors)

if __name__ == "__main__":
    unittest.main()
