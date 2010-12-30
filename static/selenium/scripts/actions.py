import unittest, time, re
from selenium import selenium

class Action(unittest.TestCase):
    def __init__ (self, selenium):
        self.sel = selenium
        
    def login(self, username, password, reveal=True):
        sel = self.sel
        if sel.is_element_present("link=Logout"):
            # Already logged in check the account
            if sel.is_element_present("link=%s" % username):
                # already logged in
                return
            else:
                # logged in but as a different user
                self.logout()
        sel.open("/eden/default/user/login")
        sel.click("auth_user_email")
        sel.type("auth_user_email", username)
        sel.type("auth_user_password", password)
        sel.click("//input[@value='Submit']")
        msg = "Unable to log in as " + username
        if reveal:
            msg += " with password " + password
        self.assertTrue(self.successMsg("Logged in"),msg)

    def logout(self):
        sel = self.sel
        if sel.is_element_present("link=Logout"):
            sel.click("link=Logout")
            sel.wait_for_page_to_load("30000")

    def search(self, searchString, expected, abort=None):
        sel = self.sel
        result = ""
        # The search filter is part of the http://datatables.net/ JavaScript getting it to work with Selenium needs a bit of care.
        # Entering text in the filter textbox doesn't always trigger off the filtering and it is not possible with this method to clear the filter.
        # The solution is to put in a call to the DataTables API, namely the fnFilter function
        # However, the first time that the fnFilter() is called in the testing suite it doesn't complete the processing, hence it is called twice.
        sel.run_script("oTable = $('#list').dataTable();  oTable.fnFilter( '' );")
        time.sleep(1)
        sel.run_script("oTable = $('#list').dataTable();  oTable.fnFilter( '%s' );" % searchString)
        time.sleep(5)
        for i in range(10):
            try:
                result = sel.get_text("//div[@id='table-container']")
            except:
                time.sleep(3)
                continue
            if  expected in result:
                return True
            if abort != None:
                if abort in result:
                    return False
        if abort != None:
            self.fail("time out: Looking for %s or %s within %s" % (expected, abort, result))
        else:
            self.fail("time out: Looking for %s within %s" % (expected, result))
        
    def searchUnique(self, uniqueName):
        self.search(uniqueName, r"1 entries")
        
    def clearSearch(self):
        sel = self.sel
        sel.run_script("oTable = $('#list').dataTable();  oTable.fnFilter( 'Clearing...' );")
        self.search("", r"entries")
        
    def addUser(self, first_name, last_name, email, password):
        first_name = first_name.strip()
        last_name = last_name.strip()
        email = email.strip()
        password = password.strip()
        
        sel = self.sel
        # TODO only open this page if on another page
        sel.open("/eden/admin/user")
        self.assertTrue(sel.is_element_present("show-add-btn"))
        sel.click("show-add-btn")
        sel.type("auth_user_first_name", first_name)
        sel.type("auth_user_last_name", last_name)
        sel.select("auth_user_language", "label=English")
        sel.type("auth_user_email", email)
        sel.type("auth_user_password", password)
        sel.type("password_two", password)
        sel.click("//input[@value='Save']")
        sel.wait_for_page_to_load("30000")
        msg = "Unable to create user %s %s with email %s" % (first_name, last_name, email)
        self.assertTrue(self.successMsg("User added"), msg)
        self.searchUnique(email)
        self.assertTrue(re.search(r"Showing 1 to 1 of 1 entries", sel.get_text("//div[@class='dataTables_info']")))
        print "User %s created" % (email)

    def addRole(self, email, roles):
        email = email.strip()
        roles = roles.strip()
        roleList = roles.split(" ")
        
        sel = self.sel
        self.searchUnique(email)
        sel.click("link=Open")
        sel.wait_for_page_to_load("30000")
        sel.click("//div[@id='content']/a[2]")
        sel.wait_for_page_to_load("30000")
        sel.click("auth_membership_group_id")
        for role in roleList:
            sel.select("auth_membership_group_id", "value=" + str(role.strip()))
            sel.click("//input[@value='Add']")
            sel.wait_for_page_to_load("30000")
            msg = "Failed to add role %s to user %s" % (role.strip() , email)
            self.assertTrue(self.successMsg("User Updated"), msg)
            print "User %s added to group %s" % (email, role.strip())
        sel.open("/eden/admin/user")

    def delUser(self, email):
        email = email.strip()
        print "Deleting user %s" % email
        sel = self.sel
        sel.open("/eden/admin/user")
        self.searchUnique(email)

        sel.click("link=Delete")
        self.assertTrue(re.search(r"^Sure you want to delete this object[\s\S]$", sel.get_confirmation()))
        self.assertTrue(self.successMsg("User deleted"))
        self.search(email, r"No matching records found")
        print "User %s deleted" % (email)

    def addLocation(self, holder, name, level, parent=None, lat=None, lon=None):
        sel = self.sel
        name = holder + name + holder
        if parent == None:
            parentHolder = None
        else:
            parentHolder = holder + parent + holder
        # Load the Create Location page
        sel.open("/eden/gis/location/create")
        # Create the Location
        sel.type("gis_location_name", name)
        if level:
            sel.select("gis_location_level", "value=%s" % level)
        if parent:
            try:
                sel.select("gis_location_parent", "label=%s" % parentHolder)
            except:
                parentHolder = parent
                sel.select("gis_location_parent", "label=%s" % parentHolder)
        if lat:
            sel.type("gis_location_lat", lat)
        if lon:
            sel.type("gis_location_lon", lon)
        # Save the form
        sel.click("//input[@value='Save']")
        sel.wait_for_page_to_load("30000")
        # Location saved
        msg = "Failed to add location %s level %s with parent %s" % (name , level, parentHolder)
        self.assertTrue(self.successMsg("Location added"), msg)
        print "Location %s level %s with parent %s added" % (name , level, parentHolder)

    def deleteObject(self, page, objName, type="Object"):
        sel = self.sel
        # need the following line which reloads the page otherwise the search gets stuck  
        sel.open(page)
        try:
            self.searchUnique(objName)
            sel.click("link=Delete")
            self.assertTrue(re.search(r"^Sure you want to delete this object[\s\S]$", sel.get_confirmation()))
            self.successMsg("%s deleted" % type)
            print "%s %s deleted" % (type, objName)
        except:
            print "Failed to delete %s %s from page %s" % (type, objName, page)

    def deleteLocation(self, name):
        self.deleteObject("/eden/gis/location", name, "Location")

    # Method to check the details that are displayed in the heading
    def checkHeading(self, detailMap):
        sel = self.sel
        heading = sel.get_text("//div[@id='rheader']/div/table/tbody")
        searchString = ""
        for key, value in detailMap.items():
            msg = "Unable to find details of %s in the header of %s"
            self.assertTrue(key in heading, msg % (key, heading))
            self.assertTrue(value in heading, msg % (value, heading))

    # Method to save the details
    def saveForm(self, message=None):
        sel = self.sel
        sel.click("//input[@value='Save']")
        sel.wait_for_page_to_load("30000")
        if message != None:
            return self.successMsg(message)

    # Method to locate a message in a div with a class given by type
    def findMsg(self, message, type):
        sel = self.sel
        for cnt in range (10):
            i = 1
            while sel.is_element_present('//div[@class="%s"][%s]' % (type, i)):
                banner = sel.get_text('//div[@class="%s"][%s]' % (type, i))
                if message in banner:
                    return True
                i += 1
            time.sleep(1)
        return False
    
    # Method used to check for confirmation messages
    def successMsg(self, message):
        return self.findMsg(message, "confirmation")

    # Method used to check for error messages
    def errorMsg(self, message):
        return self.findMsg(message, "error")

    # Method to check that form element is present
    def element(self, element):
        sel = self.sel
        type = element[0]
        id = element[1]
        if (len(element) >= 3):
            visible = element[2] 
        else:
            visible = True
        if (len(element) >= 4):
            value = element[3] 
        else:
            value = None
        element = '//%s[@id="%s"]' % (type, id)
        self.assertTrue(sel.is_element_present(element), "%s element %s is missing" % (type, id))
        if visible:
            self.assertTrue(sel.is_visible(element), "%s element %s is not visible" % (type, id))
        else:
            self.assertFalse(sel.is_visible(element), "%s element %s is not hidden" % (type, id))
        if value!= None:
            actual = sel.get_value(element)
            msg = "expected %s for element %s doesn't equal the actual value of %s" % (value, id, actual)
            self.assertEqual(value, actual, msg)
                
    # Method to click on a tab
    def clickTab(self, name):
        sel = self.sel
        element = "//div[@id='rheader_tabs']/span/a[text()='%s']" % (name)
        sel.click(element)
        sel.wait_for_page_to_load("30000")
        
    # Method to check button link
    def btnLink(self, id, name):
        sel = self.sel
        element = '//a[@id="%s"]' % (id)
        errMsg = "%s button is missing" % (name)
        self.assertTrue(sel.is_element_present(element), errMsg)
        self.assertTrue(sel.get_text(element),errMsg)
        print "%s button is present" % (name)
        
    # Method to check button link is not present
    def noBtnLink(self, id, name):
        sel = self.sel
        element = '//a[@id="%s"]' % (id)
        errMsg = "Unexpected presence of %s button" % (name)
        if sel.is_element_present(element):
            self.assertFalse(sel.get_text(element), errMsg)
        print "%s button is not present" % (name)

    # Method to check that form button is present
    def button(self, name):
        sel = self.sel
        element = '//input[@value="%s"]' % (name)
        errmsg = "%s button is missing" % (name)
        self.assertTrue(sel.is_element_present(element), errmsg)
        print "%s button is present" % (name)
        
    # Method to check that the help message is displayed
    def helpBallon(self, helpTitle):
        sel = self.sel
        element = "//div[contains(@title,'%s')]" % (helpTitle)
        self.assertTrue(sel.is_element_present(element))
        sel.mouse_over(element)
        self.assertFalse(sel.is_element_present(element), "Help %s is missing" % (helpTitle))
        print "Help %s is present" % (helpTitle)

    # Method to check that the layout of a form
    def checkForm (self, elementList, buttonList, helpList):
        elements = []
        for element in elementList:
            self.element(element)
            elements.append(element[1])
        for name in buttonList:
            self.button(name)
        for title in helpList:
            self.helpBallon(title)
        if len(elements) > 0:
            print "Verified the following form elements %s" % elements
