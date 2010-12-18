import testSuite
from sahanaTest import SahanaTest
import actions

class DeleteTestAccount(SahanaTest):
    def setUp(self):
        self.user = testSuite.SahanaTestSuite.user;
        self.password = testSuite.SahanaTestSuite.password;
    
    def test_delete_test_account(self):
        sel = self.selenium
        # This test case will delete the users admin@example.com & user@example.com
        self.action.login(self, self.user, self.password, False)
        self.action.delUser(self, 'admin@example.com')
        self.action.delUser(self, 'user@example.com')

DeleteTestAccount.start()

if __name__ == "__main__":
    SahanaTest.setUpHierarchy()
    unittest.main()
