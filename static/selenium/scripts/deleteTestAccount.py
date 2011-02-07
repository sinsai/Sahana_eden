from sahanaTest import SahanaTest
import actions

class DeleteTestAccount(SahanaTest):
    """ Delete the common accounts that were created for the suite of test classes """
    _sortList = ("deleteAll",)

    def deleteAll(self):
        """ Delete the standard testing account: user@example.com """
#        sel = self.selenium
        # This test case will delete the users admin@example.com & user@example.com
        #self.action.login(self._user, self._password, False)
        #self.action.delUser('admin@example.com')
        self.action.login("admin@example.com", "testing", False)
        self.action.delUser("user@example.com")

if __name__ == "__main__":
    SahanaTest.setUpHierarchy()
    unittest.main()
