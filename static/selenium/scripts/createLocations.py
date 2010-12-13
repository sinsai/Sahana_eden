from selenium import selenium
import unittest, time, re
import testSuite
import actions

class CreateLocations(unittest.TestCase):
    def setUp(self):
        self.verificationErrors = []
        self.action = actions.Action()
        self.selenium = testSuite.SahanaTestSuite.selenium

    def header(self):
        sel = self.selenium
        # Login
        self.action.login(self, "admin@example.com", "testing" )
        self.assertTrue(self.selenium.is_element_present("link=admin@example.com"))

    def test_createLocations(self):
        """ Create locations for testing the Locations Selector """
        sel = self.selenium
        self.header()
        self.createLocation("Ouest", "L1", "Haiti")
        self.createLocation("Port-Au-Prince", "L2", "Ouest")
        self.createLocation("Martissant", "L3", "Port-Au-Prince")
        self.createLocation("Carrefour Feuilles", "L4", "Martissant")
        self.createLocation("Clinique Communautaire de Martissant", "", "Carrefour Feuilles", lat=18.528000848953, lon=-72.348998382827)

    def createLocation(self, name, level, parent, lat=None, lon=None):
        sel = self.selenium
        # Load the Create Location page
        sel.open("/eden/gis/location/create")
        # Create the Location
        sel.type("gis_location_name", name)
        if level:
            sel.select("gis_location_level", "value=%s" % level)
        sel.select("gis_location_parent", "label=%s" % parent)
        if lat:
            sel.type("gis_location_lat", lat)
        if lon:
            sel.type("gis_location_lon", lon)
        # Save the form
        sel.click("//input[@value='Save']")
        sel.wait_for_page_to_load("30000")
        # Location saved
        self.assertEqual("Location added", sel.get_text("//div[@class=\"confirmation\"]"))

    def tearDown(self):
        #self.assertEqual([], self.verificationErrors)
        pass

if __name__ == "__main__":
    unittest.main()
