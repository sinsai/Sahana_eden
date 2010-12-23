from sahanaTest import SahanaTest
import unittest


class UserManagement(SahanaTest):
    """ Test the creation of creating user accounts """
    
    
    def firstRun(self):
        self.useSahanaAdminAccount()
        self.action.login(self._user, self._password )
        self.users = []
        sel = self.selenium
        print "Test script to Add test users"
        self.newUsers = self.getUserDetails()
        self.userRole = {}
        for user in self.newUsers:
            details = user.split(',')
            self.assertTrue(len(details)>=4,user)
            # Add the new user
            self.action.addUser(details[0], details[1], details[2], details[3])
            if len(details) == 5:
                self.action.addRole(details[2], details[4].strip())
            self.users.append(details[2])
        self.action.clearSearch()
        sel.click("link=Logout")
        sel.wait_for_page_to_load("30000")

      
    # a file with one user on each line
    # The user details are first_name, last_name, email, password [, roles] 
    def getUserDetails(self):
        source = open("../data/user.txt", "r")
        values = source.readlines()
        source.close()
        return values
#class UserManagementCreate(UserManagement):

    def test_checkUser(self):
        pass

#class UserManagementFinal(UserManagement):
    
#    def test_del_users(self):
    def lastRun(self):
        sel = self.selenium
        self.useSahanaAdminAccount()
        self.action.login(self._user, self._password )
        print "Test script to Delete test users"
        for user in self.users:
            self.action.delUser(user)
        self.action.clearSearch()
        sel.click("link=Logout")
        sel.wait_for_page_to_load("30000")

if __name__ == "__main__":
    SahanaTest.setUpHierarchy()
    unittest.main()
    OrganisationTest.selenium.stop()
