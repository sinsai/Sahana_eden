from sahanaTest import SahanaTest
import actions

class CreateTestAccount(SahanaTest):
    """ Set up common accounts to be used by the suite of test classes """
    _sortList = ("createAll",)

    def createAll(self):
        """ Create the standard testing accounts admin@example.com and user@example.com """
        # *** NOTE this script needs to be run by a user with Administrator privileges. END NOTE ***
        self.action.login(self._user, self._password, False)
        self.action.addUser("Admin", "User", "admin@example.com", "testing")
        self.action.addRole("admin@example.com", "1")
        self.action.addUser("Normal", "User", "user@example.com", "testing")

if __name__ == "__main__":
    SahanaTest.setUpHierarchy()
    unittest.main()
