from sahanaTest import SahanaTest
import actions

class DeleteTestAccount(SahanaTest):
    
    def test_delete_test_account(self):
        """ Delete the standard testing accounts of admin@example.com and user@example.com """
        sel = self.selenium
        # This test case will delete the users admin@example.com & user@example.com
        self.action.login(self, self._user, self._password, False)
        self.action.delUser(self, 'admin@example.com')
        self.action.delUser(self, 'user@example.com')

if __name__ == "__main__":
    SahanaTest.setUpHierarchy()
    unittest.main()
