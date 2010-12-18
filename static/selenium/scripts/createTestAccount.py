import testSuite
from sahanaTest import SahanaTest
import actions

class CreateTestAccount(SahanaTest):
    

    def setUp(self):
        self.user = testSuite.SahanaTestSuite.user;
        self.password = testSuite.SahanaTestSuite.password;
    
    def test_create_test_accounts(self):
        sel = self.selenium
        
        # *** NOTE this script needs to be run by a user with Administrator privileges. END NOTE ***
        self.action.login(self, self.user, self.password, False)
        self.action.addUser(self,"Admin", "User", "admin@example.com", "testing")
        self.action.addRole(self, "admin@example.com", '1')
        self.action.addUser(self,"Normal", "User", "user@example.com", "testing")

CreateTestAccount.start()

if __name__ == "__main__":
    SahanaTest.setUpHierarchy()
    unittest.main()
