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
        sel = self.selenium
        # Login
        self.action.login(self, "user@example.com", "testing" )
        self.assertTrue(self.selenium.is_element_present("link=user@example.com"))
        # Load the Create Shelter page
        sel.open("/eden/cr/shelter/create")

    def tearDown(self):
        #self.assertEqual([], self.verificationErrors)
        pass

class LocationEmpty(LocationSelector):
    def test_locationEmpty(self):
        """ Create a new Shelter without any Location specified """
        sel = self.selenium
        self.header()
        # Fill in the mandatory fields
        sel.type("cr_shelter_name", "Shelter with no Location")
        # Save the form
        sel.click("//input[@value='Save']")
        sel.wait_for_page_to_load("30000")
        # Shelter saved
        self.assertEqual("Shelter added", sel.get_text("//div[@class=\"confirmation\"]"))

class LocationNoParent(LocationSelector):
    def test_locationNoParent(self):
        """ Create a new Shelter without any Location specified """
        sel = self.selenium
        self.header()
        # Fill in the mandatory fields
        sel.type("cr_shelter_name", "Shelter with no Parent")
        # Create a new location
        sel.click("gis_location_add-btn")
        sel.type("gis_location_name", "Location with no Parent")
        # Save the form
        sel.click("//input[@value='Save']")
        sel.wait_for_page_to_load("30000")
        # Shelter saved
        self.assertEqual("Shelter added", sel.get_text("//div[@class=\"confirmation\"]"))
        # Shelter has correct location
        self.assertEqual("Location with no Parent", sel.get_table("//div[@id='rheader']/div/table.1.1"))

class LocationL0(LocationSelector):
    def test_locationL0(self):
        """ Create a new Shelter with an L0 location """
        sel = self.selenium
        self.header()
        # Fill in the mandatory fields
        sel.type("cr_shelter_name", "Shelter with an L0 Location")
        # Select the L0
        sel.select("gis_location_L0", "label=Haiti")
        # Check that L1 dropdown appears correctly
        time.sleep(3)
        self.assertEqual("Select a location...Ouest", sel.get_table("//div[@id='content']/div[2]/form/table.11.0"))
        # Save the form
        sel.click("//input[@value='Save']")
        sel.wait_for_page_to_load("30000")
        # Shelter saved
        self.assertEqual("Shelter added", sel.get_text("//div[@class=\"confirmation\"]"))
        # Shelter has correct location
        self.assertEqual("Haiti", sel.get_table("//div[@id='rheader']/div/table.1.1"))

class LocationInL0(LocationSelector):
    def test_locationInL0(self):
        """ Create a new Shelter inside an L0 location """
        sel = self.selenium
        self.header()
        # Fill in the mandatory fields
        sel.type("cr_shelter_name", "Shelter within L0 Location")
        # Select the L0
        sel.select("gis_location_L0", "label=Haiti")
        # Check that L1 dropdown appears correctly
        time.sleep(3)
        self.assertEqual("Select a location...Ouest", sel.get_table("//div[@id='content']/div[2]/form/table.11.0"))
        # Create a new location
        sel.click("gis_location_add-btn")
        sel.type("gis_location_name", "Specific Location in L0")
        # Save the form
        sel.click("//input[@value='Save']")
        sel.wait_for_page_to_load("30000")
        # Shelter saved
        self.assertEqual("Shelter added", sel.get_text("//div[@class=\"confirmation\"]"))
        # Shelter has correct location
        self.assertEqual("Specific Location in L0", sel.get_table("//div[@id='rheader']/div/table.1.1"))

class LocationL1(LocationSelector):
    def test_locationL1(self):
        """ Create a new Shelter with an L1 location """
        sel = self.selenium
        self.header()
        # Fill in the mandatory fields
        sel.type("cr_shelter_name", "Shelter with an L1 Location")
        # Select the L0
        sel.select("gis_location_L0", "label=Haiti")
        # Check that L1 dropdown appears correctly
        time.sleep(3)
        self.assertEqual("Select a location...Ouest", sel.get_table("//div[@id='content']/div[2]/form/table.11.0"))
        # Select the L1
        sel.select("gis_location_L1", "label=Ouest")
        # Check that L2 dropdown appears correctly
        time.sleep(3)
        self.assertEqual("Select a location...Port-Au-Prince", sel.get_table("//div[@id='content']/div[2]/form/table.13.0"))
        # Save the form
        sel.click("//input[@value='Save']")
        sel.wait_for_page_to_load("30000")
        # Shelter saved
        self.assertEqual("Shelter added", sel.get_text("//div[@class=\"confirmation\"]"))
        # Shelter has correct location
        self.assertEqual("Ouest (Haiti)", sel.get_table("//div[@id='rheader']/div/table.1.1"))

class LocationInL1(LocationSelector):
    def test_locationInL1(self):
        """ Create a new Shelter inside an L1 location """
        sel = self.selenium
        self.header()
        # Fill in the mandatory fields
        sel.type("cr_shelter_name", "Shelter within L1 Location")
        # Select the L0
        sel.select("gis_location_L0", "label=Haiti")
        # Check that L1 dropdown appears correctly
        time.sleep(3)
        self.assertEqual("Select a location...Ouest", sel.get_table("//div[@id='content']/div[2]/form/table.11.0"))
        # Select the L1
        sel.select("gis_location_L1", "label=Ouest")
        # Check that L2 dropdown appears correctly
        time.sleep(3)
        self.assertEqual("Select a location...Port-Au-Prince", sel.get_table("//div[@id='content']/div[2]/form/table.13.0"))
        # Create a new location
        sel.click("gis_location_add-btn")
        sel.type("gis_location_name", "Specific Location in L1")
        # Save the form
        sel.click("//input[@value='Save']")
        sel.wait_for_page_to_load("30000")
        # Shelter saved
        self.assertEqual("Shelter added", sel.get_text("//div[@class=\"confirmation\"]"))
        # Shelter has correct location
        self.assertEqual("Specific Location in L1", sel.get_table("//div[@id='rheader']/div/table.1.1"))

class LocationL2(LocationSelector):
    def test_locationL2(self):
        """ Create a new Shelter with an L2 location """
        sel = self.selenium
        self.header()
        # Fill in the mandatory fields
        sel.type("cr_shelter_name", "Shelter with an L2 Location")
        # Select the L0
        sel.select("gis_location_L0", "label=Haiti")
        # Check that L1 dropdown appears correctly
        time.sleep(3)
        self.assertEqual("Select a location...Ouest", sel.get_table("//div[@id='content']/div[2]/form/table.11.0"))
        # Select the L1
        sel.select("gis_location_L1", "label=Ouest")
        # Check that L2 dropdown appears correctly
        time.sleep(3)
        self.assertEqual("Select a location...Port-Au-Prince", sel.get_table("//div[@id='content']/div[2]/form/table.13.0"))
        # Select the L2
        sel.select("gis_location_L2", "label=Port-Au-Prince")
        # Check that L3 dropdown appears correctly
        time.sleep(3)
        self.assertEqual("Select a location...Martissant", sel.get_table("//div[@id='content']/div[2]/form/table.15.0"))
        # Save the form
        sel.click("//input[@value='Save']")
        sel.wait_for_page_to_load("30000")
        # Shelter saved
        self.assertEqual("Shelter added", sel.get_text("//div[@class=\"confirmation\"]"))
        # Shelter has correct location
        self.assertEqual("Port-Au-Prince (Ouest)", sel.get_table("//div[@id='rheader']/div/table.1.1"))

class LocationInL2(LocationSelector):
    def test_locationInL2(self):
        """ Create a new Shelter inside an L2 location """
        sel = self.selenium
        self.header()
        # Fill in the mandatory fields
        sel.type("cr_shelter_name", "Shelter within L2 Location")
        # Select the L0
        sel.select("gis_location_L0", "label=Haiti")
        # Check that L1 dropdown appears correctly
        time.sleep(3)
        self.assertEqual("Select a location...Ouest", sel.get_table("//div[@id='content']/div[2]/form/table.11.0"))
        # Select the L1
        sel.select("gis_location_L1", "label=Ouest")
        # Check that L2 dropdown appears correctly
        time.sleep(3)
        self.assertEqual("Select a location...Port-Au-Prince", sel.get_table("//div[@id='content']/div[2]/form/table.13.0"))
        # Select the L2
        sel.select("gis_location_L2", "label=Port-Au-Prince")
        # Check that L3 dropdown appears correctly
        time.sleep(3)
        self.assertEqual("Select a location...Martissant", sel.get_table("//div[@id='content']/div[2]/form/table.15.0"))
        # Create a new location
        sel.click("gis_location_add-btn")
        sel.type("gis_location_name", "Specific Location in L2")
        # Save the form
        sel.click("//input[@value='Save']")
        sel.wait_for_page_to_load("30000")
        # Shelter saved
        self.assertEqual("Shelter added", sel.get_text("//div[@class=\"confirmation\"]"))
        # Shelter has correct location
        self.assertEqual("Specific Location in L2", sel.get_table("//div[@id='rheader']/div/table.1.1"))

class LocationL3(LocationSelector):
    def test_locationL3(self):
        """ Create a new Shelter with an L3 location """
        sel = self.selenium
        self.header()
        # Fill in the mandatory fields
        sel.type("cr_shelter_name", "Shelter with an L3 Location")
        # Select the L0
        sel.select("gis_location_L0", "label=Haiti")
        # Check that L1 dropdown appears correctly
        time.sleep(3)
        self.assertEqual("Select a location...Ouest", sel.get_table("//div[@id='content']/div[2]/form/table.11.0"))
        sel.select("gis_location_L1", "label=Ouest")
        # Check that L2 dropdown appears correctly
        time.sleep(3)
        self.assertEqual("Select a location...Port-Au-Prince", sel.get_table("//div[@id='content']/div[2]/form/table.13.0"))
        # Select the L2
        sel.select("gis_location_L2", "label=Port-Au-Prince")
        # Check that L3 dropdown appears correctly
        time.sleep(3)
        self.assertEqual("Select a location...Martissant", sel.get_table("//div[@id='content']/div[2]/form/table.15.0"))
        # Select the L3
        sel.select("gis_location_L3", "label=Martissant")
        # Check that L4 dropdown appears correctly
        time.sleep(3)
        self.assertEqual("Select a location...Carrefour Feuilles", sel.get_table("//div[@id='content']/div[2]/form/table.17.0"))
        # Save the form
        sel.click("//input[@value='Save']")
        sel.wait_for_page_to_load("30000")
        # Shelter saved
        self.assertEqual("Shelter added", sel.get_text("//div[@class=\"confirmation\"]"))
        # Shelter has correct location
        self.assertEqual("Martissant (Port-Au-Prince)", sel.get_table("//div[@id='rheader']/div/table.1.1"))

class LocationInL3(LocationSelector):
    def test_locationInL3(self):
        """ Create a new Shelter inside an L3 location """
        sel = self.selenium
        self.header()
        # Fill in the mandatory fields
        sel.type("cr_shelter_name", "Shelter within L3 Location")
        # Select the L0
        sel.select("gis_location_L0", "label=Haiti")
        # Check that L1 dropdown appears correctly
        time.sleep(3)
        self.assertEqual("Select a location...Ouest", sel.get_table("//div[@id='content']/div[2]/form/table.11.0"))
        # Select the L1
        sel.select("gis_location_L1", "label=Ouest")
        # Check that L2 dropdown appears correctly
        time.sleep(3)
        self.assertEqual("Select a location...Port-Au-Prince", sel.get_table("//div[@id='content']/div[2]/form/table.13.0"))
        # Select the L2
        sel.select("gis_location_L2", "label=Port-Au-Prince")
        # Check that L3 dropdown appears correctly
        time.sleep(3)
        self.assertEqual("Select a location...Martissant", sel.get_table("//div[@id='content']/div[2]/form/table.15.0"))
        # Select the L3
        sel.select("gis_location_L3", "label=Martissant")
        # Check that L4 dropdown appears correctly
        time.sleep(3)
        self.assertEqual("Select a location...Carrefour Feuilles", sel.get_table("//div[@id='content']/div[2]/form/table.17.0"))
        # Create a new location
        sel.click("gis_location_add-btn")
        sel.type("gis_location_name", "Specific Location in L3")
        # Save the form
        sel.click("//input[@value='Save']")
        sel.wait_for_page_to_load("30000")
        # Shelter saved
        self.assertEqual("Shelter added", sel.get_text("//div[@class=\"confirmation\"]"))
        # Shelter has correct location
        self.assertEqual("Specific Location in L3", sel.get_table("//div[@id='rheader']/div/table.1.1"))

class LocationL4(LocationSelector):
    def test_locationL4(self):
        """ Create a new Shelter with an L4 location """
        sel = self.selenium
        self.header()
        # Fill in the mandatory fields
        sel.type("cr_shelter_name", "Shelter with an L4 Location")
        # Select the L0
        sel.select("gis_location_L0", "label=Haiti")
        # Check that L1 dropdown appears correctly
        time.sleep(3)
        self.assertEqual("Select a location...Ouest", sel.get_table("//div[@id='content']/div[2]/form/table.11.0"))
        # Select the L1
        sel.select("gis_location_L1", "label=Ouest")
        # Check that L2 dropdown appears correctly
        time.sleep(3)
        self.assertEqual("Select a location...Port-Au-Prince", sel.get_table("//div[@id='content']/div[2]/form/table.13.0"))
        # Select the L2
        sel.select("gis_location_L2", "label=Port-Au-Prince")
        # Check that L3 dropdown appears correctly
        time.sleep(3)
        self.assertEqual("Select a location...Martissant", sel.get_table("//div[@id='content']/div[2]/form/table.15.0"))
        # Select the L3
        sel.select("gis_location_L3", "label=Martissant")
        # Check that L4 dropdown appears correctly
        time.sleep(3)
        self.assertEqual("Select a location...Carrefour Feuilles", sel.get_table("//div[@id='content']/div[2]/form/table.17.0"))
        # Select the L4
        sel.select("gis_location_L4", "label=Carrefour Feuilles")
        # Check that 'L5' dropdown appears correctly
        time.sleep(3)
        self.assertEqual("Select a location...Clinique Communautaire de Martissant", sel.get_table("//div[@id='content']/div[2]/form/table.19.0"))
        # Save the form
        sel.click("//input[@value='Save']")
        sel.wait_for_page_to_load("30000")
        # Shelter saved
        self.assertEqual("Shelter added", sel.get_text("//div[@class=\"confirmation\"]"))
        # Shelter has correct location
        self.assertEqual("Carrefour Feuilles", sel.get_table("//div[@id='rheader']/div/table.1.1"))

class LocationInL4(LocationSelector):
    def test_locationInL4(self):
        """ Create a new Shelter inside an L4 location """
        sel = self.selenium
        self.header()
        # Fill in the mandatory fields
        sel.type("cr_shelter_name", "Shelter within L4 Location")
        # Select the L0
        sel.select("gis_location_L0", "label=Haiti")
        # Check that L1 dropdown appears correctly
        time.sleep(3)
        self.assertEqual("Select a location...Ouest", sel.get_table("//div[@id='content']/div[2]/form/table.11.0"))
        # Select the L1
        sel.select("gis_location_L1", "label=Ouest")
        # Check that L2 dropdown appears correctly
        time.sleep(3)
        self.assertEqual("Select a location...Port-Au-Prince", sel.get_table("//div[@id='content']/div[2]/form/table.13.0"))
        # Select the L2
        sel.select("gis_location_L2", "label=Port-Au-Prince")
        # Check that L3 dropdown appears correctly
        time.sleep(3)
        self.assertEqual("Select a location...Martissant", sel.get_table("//div[@id='content']/div[2]/form/table.15.0"))
        # Select the L3
        sel.select("gis_location_L3", "label=Martissant")
        # Check that L4 dropdown appears correctly
        time.sleep(3)
        self.assertEqual("Select a location...Carrefour Feuilles", sel.get_table("//div[@id='content']/div[2]/form/table.17.0"))
        # Select the L4
        sel.select("gis_location_L4", "label=Carrefour Feuilles")
        # Check that specific location dropdown appears correctly
        time.sleep(3)
        self.assertEqual("Select a location...Clinique Communautaire de Martissant", sel.get_table("//div[@id='content']/div[2]/form/table.19.0"))
        # Create a new location
        sel.click("gis_location_add-btn")
        sel.type("gis_location_name", "Specific Location in L4")
        # Save the form
        sel.click("//input[@value='Save']")
        sel.wait_for_page_to_load("30000")
        # Shelter saved
        self.assertEqual("Shelter added", sel.get_text("//div[@class=\"confirmation\"]"))
        # Shelter has correct location
        self.assertEqual("Specific Location in L4", sel.get_table("//div[@id='rheader']/div/table.1.1"))

class LocationSelectSpecific(LocationSelector):
    def test_locationSelectSpecific(self):
        """ Create a new Shelter with a pre-existing specific location """
        sel = self.selenium
        self.header()
        # Fill in the mandatory fields
        sel.type("cr_shelter_name", "Shelter with a pre-existing specific Location")
        # Select the L0
        sel.select("gis_location_L0", "label=Haiti")
        # Check that L1 dropdown appears correctly
        time.sleep(3)
        self.assertEqual("Select a location...Ouest", sel.get_table("//div[@id='content']/div[2]/form/table.11.0"))
        # Select the L1
        sel.select("gis_location_L1", "label=Ouest")
        # Check that L2 dropdown appears correctly
        time.sleep(3)
        self.assertEqual("Select a location...Port-Au-Prince", sel.get_table("//div[@id='content']/div[2]/form/table.13.0"))
        # Select the L2
        sel.select("gis_location_L2", "label=Port-Au-Prince")
        # Check that L3 dropdown appears correctly
        time.sleep(3)
        self.assertEqual("Select a location...Martissant", sel.get_table("//div[@id='content']/div[2]/form/table.15.0"))
        # Select the L3
        sel.select("gis_location_L3", "label=Martissant")
        # Check that L4 dropdown appears correctly
        time.sleep(3)
        self.assertEqual("Select a location...Carrefour Feuilles", sel.get_table("//div[@id='content']/div[2]/form/table.17.0"))
        # Select the L4
        sel.select("gis_location_L4", "label=Carrefour Feuilles")
        # Check that specific location dropdown appears correctly
        time.sleep(3)
        self.assertEqual("Select a location...Clinique Communautaire de Martissant", sel.get_table("//div[@id='content']/div[2]/form/table.19.0"))
        # Select the Specific
        sel.select("gis_location_", "label=Clinique Communautaire de Martissant")
        # Save the form
        sel.click("//input[@value='Save']")
        sel.wait_for_page_to_load("30000")
        # Shelter saved
        self.assertEqual("Shelter added", sel.get_text("//div[@class=\"confirmation\"]"))
        # Shelter has correct location
        self.assertEqual("Clinique Communautaire de Martissant (N 18.528000849 W -72.3489983828)", sel.get_table("//div[@id='rheader']/div/table.1.1"))

if __name__ == "__main__":
    unittest.main()
