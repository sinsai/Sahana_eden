from sahanaTest import SahanaTest
import actions

class CreateTestAccount(SahanaTest):
      
    def test_create_test_accounts(self):
        """ Create the standard testing accounts admin@example.com and user@example.com """
        sel = self.selenium
        
        # *** NOTE this script needs to be run by a user with Administrator privileges. END NOTE ***
        self.action.login(self, self._user, self._password, False)
        self.action.addUser(self,"Admin", "User", "admin@example.com", "testing")
        self.action.addRole(self, "admin@example.com", '1')
        self.action.addUser(self,"Normal", "User", "user@example.com", "testing")

if __name__ == "__main__":
    SahanaTest.setUpHierarchy()
    unittest.main()
