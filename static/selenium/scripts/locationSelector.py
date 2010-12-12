from selenium import selenium
import unittest, time, re
import testSuite
import actions

class LocationSelector(unittest.TestCase):
    def setUp(self):
        self.verificationErrors = []
        self.action = actions.Action()
        self.selenium = testSuite.SahanaTestSuite.selenium
        # @ToDo: Import Test Data (e.g. Haiti subset)

    def header(self):
        # Login
        self.action.login(self, "user@example.com", "testing" )
        self.assertTrue(self.selenium.is_element_present("link=user@example.com"))
        # Load the Create Shelter page
        sel.open("/eden/cr/index")
        sel.click("link=Add")
        sel.wait_for_page_to_load("10000")
        self.assertEqual("Add Shelter", sel.get_text("//h2"))

    def tearDown(self):
        pass
        #self.selenium.stop()
        #self.assertEqual([], self.verificationErrors)

class LocationEmpty(LocationSelector):
    def test_locationEmpty(self):
        """ Create a new Shelter without any Location specified """
        sel = self.selenium
        self.header()
        # Fill in the mandatory fields
        sel.click("cr_shelter_name")
        sel.type("cr_shelter_name", "Shelter with no Location")
        # Save the form
        sel.click("//input[@value='Save']")
        sel.wait_for_page_to_load("30000")
        # Shelter saved
        self.assertEqual("Shelter added", sel.get_text("//div[@class=\"confirmation\"]"))

class LocationNoParent(LocationSelector):
    def test_locationEmpty(self):
        """ Create a new Shelter without any Location specified """
        sel = self.selenium
        self.header()
        # Fill in the mandatory fields
        sel.click("cr_shelter_name")
        sel.type("cr_shelter_name", "Shelter with no Location")
        # Save the form
        sel.click("//input[@value='Save']")
        sel.wait_for_page_to_load("30000")
        # Shelter saved
        self.assertEqual("Shelter added", sel.get_text("//div[@class=\"confirmation\"]"))

class LocationL0(LocationSelector):
    def test_locationL0(self):
        """ Create a new Shelter with an L0 location """
        sel = self.selenium
        self.header()
        # Fill in the mandatory fields
        sel.click("cr_shelter_name")
        sel.type("cr_shelter_name", "Shelter with an L0 Location")
        # Select the Location
        sel.click("gis_location_L0")
        sel.select("gis_location_L0", "label=Afghanistan")
        # Check that L1 dropdown appears correctly
        time.sleep(2)
        self.assertEqual("No locations registered at this level", sel.get_table("//div[@id='content']/div[2]/form/table.11.0"))
        # Save the form
        sel.click("//input[@value='Save']")
        sel.wait_for_page_to_load("30000")
        # Shelter saved
        self.assertEqual("Shelter added", sel.get_text("//div[@class=\"confirmation\"]"))
        # Shelter has correct location
        self.assertEqual("Afghanistan", sel.get_table("//div[@id='rheader']/div/table.1.1"))

class LocationInL0(LocationSelector):
    def test_location_in_L0(self):
        """ Create a new Shelter with an L0 location """
        sel = self.selenium
        self.header()
        # Fill in the mandatory fields
        sel.click("cr_shelter_name")
        sel.type("cr_shelter_name", "Shelter within L0 Location")
        # Select the Location
        sel.click("gis_location_L0")
        sel.select("gis_location_L0", "label=Afghanistan")
        # Check that L1 dropdown appears correctly
        time.sleep(2)
        self.assertEqual("No locations registered at this level", sel.get_table("//div[@id='content']/div[2]/form/table.11.0"))
        # Create a new location
        sel.click("gis_location_add-btn")
        sel.type("gis_location_name", "Specific Location in Afghanistan")
        # Save the form
        sel.click("//input[@value='Save']")
        sel.wait_for_page_to_load("30000")
        # Shelter saved
        self.assertEqual("Shelter added", sel.get_text("//div[@class=\"confirmation\"]"))
        # Shelter has correct location
        self.assertEqual("Specific Location in Afghanistan", sel.get_table("//div[@id='rheader']/div/table.1.1"))

#class LocationL1(LocationSelector):
#    def test_locationL1(self):
#        """ Create a new Shelter with an L1 location """
#        sel = self.selenium
#        self.header()
#        # Fill in the mandatory fields
#        sel.click("cr_shelter_name")
#        sel.type("cr_shelter_name", "Shelter with an L1 Location")
#        # Select the Location
#        sel.click("gis_location_L0")
#        sel.select("gis_location_L0", "label=Haiti")
#        # Check that L1 dropdown appears correctly
#        time.sleep(2)
#        # @ToDo: Select a Haiti Province from test file
#        #self.assertEqual("No locations registered at this level", sel.get_table("//div[@id='content']/div[2]/form/table.11.0"))
#        sel.click("gis_location_L1")
#        sel.select("gis_location_L1", "label=@ToDoHaitiProvince")
#        # Check that L2 dropdown appears correctly
#        time.sleep(2)
#        self.assertEqual("No locations registered at this level", sel.get_table("//div[@id='content']/div[2]/form/table.11.0"))
#        # Save the form
#        sel.click("//input[@value='Save']")
#        sel.wait_for_page_to_load("30000")
#        # Shelter saved
#        self.assertEqual("Shelter added", sel.get_text("//div[@class=\"confirmation\"]"))
#        # Shelter has correct location
#        self.assertEqual("@ToDo: Haiti province", sel.get_table("//div[@id='rheader']/div/table.1.1"))

if __name__ == "__main__":
    unittest.main()
