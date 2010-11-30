import testSuite
import unittest, time, re
import actions

from utilities import Utilities

class UserManagement(unittest.TestCase):

    def setUp(self):
        self.action = actions.Action()
        self.selenium = testSuite.SahanaTestSuite.selenium
        self.newUsers = Utilities().getUserDetails()
    
    def header(self):
        # *** NOTE this script needs to be run by the user testing@example.com END NOTE ***
        self.action.login(self, "testing@example.com", "testing" )
        # This script will run various test cases against the User Management module found within the Administrator menu
        # All users created by this test case will 'belong' to the example.com domain
        self.assertTrue(self.selenium.is_element_present("link=testing@example.com"))

      
class UserManagementCreate(UserManagement):
    def test_add_user(self):
        sel = self.selenium
        self.header()
        print "Test script to Add test users"
        self.userRole = {}
        for user in self.newUsers:
            details = user.split(',')
            self.assertTrue(len(details)>=4,user)
            # Add the new user
            self.action.addUser(self, details[0], details[1], details[2], details[3])
            if len(details) == 5:
                self.action.addRole(self, details[2], details[4].strip())
        self.action.clearSearch(self)
        sel.click("link=Logout")
        sel.wait_for_page_to_load("30000")

class UserManagementFinal(UserManagement):
    
    def test_del_users(self):
        sel = self.selenium
        self.header()
        print "Test script to Delete test users"
        for user in self.newUsers:
            details = user.split(',')
            self.assertTrue(len(details)>=4,user)
            # Add the new user
            self.action.delUser(self, details[2])
        self.action.clearSearch(self)
        sel.click("link=Logout")
        sel.wait_for_page_to_load("30000")

if __name__ == "__main__":
    unittest.main()
