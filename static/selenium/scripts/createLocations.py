from sahanaTest import SahanaTest

class CreateLocations(SahanaTest):

    def header(self):
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
        self.createLocation("Turgeau", "L3", "Port-Au-Prince")
        self.createLocation("Babiole", "L4", "Turgeau")
        self.createLocation("Clinique Communautaire de Martissant", "", "Carrefour Feuilles", lat=18.528000848953, lon=-72.348998382827)
        self.createLocation("L2inL0", "L2", "Haiti")
        self.createLocation("L1withNoParent", "L1", None)
        self.createLocation("L2inL1withNoParent", "L2", "L1withNoParent")
        self.createLocation("L3inL0", "L3", "Haiti")
        self.createLocation("L3inL1withL0", "L3", "Ouest")
        self.createLocation("L3inL1withNoParent", "L3", "L1withNoParent")
        self.createLocation("L4inL0", "L4", "Haiti")
        self.createLocation("L4inL1withL0", "L4", "Ouest")
        self.createLocation("L4inL1withNoParent", "L4", "L1withNoParent")
        self.createLocation("L4inL2withL1L0", "L4", "Port-Au-Prince")
        self.createLocation("L4inL2withL1only", "L4", "L2inL1withNoParent")
        self.createLocation("L4inL2withL0only", "L4", "L2inL0")
        self.createLocation("L2withNoParent", "L2", None)
        self.createLocation("L4inL2withNoParent", "L4", "L2withNoParent")

    def createLocation(self, name, level, parent, lat=None, lon=None):
        sel = self.selenium
        # Load the Create Location page
        sel.open("/eden/gis/location/create")
        sel.wait_for_page_to_load("30000")
        # Create the Location
        sel.type("gis_location_name", name)
        if level:
            sel.select("gis_location_level", "value=%s" % level)
        if parent:
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

if __name__ == "__main__":
    SahanaTest.setUpHierarchy()
    unittest.main()
