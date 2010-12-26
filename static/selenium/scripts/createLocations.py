from sahanaTest import SahanaTest
<<<<<<< TREE
import unittest, time, re

class Locations(SahanaTest):
    holder = "__TEST__"
    _sortList = ("test_loadTestData",
                 "test_locationEmpty",
                 "test_addL0Location",
                 "test_removeL0Location",
                 "test_locationNoParent",
                 "test_removeTestData",
                 )
    
    def firstRun(self):
        sel = self.selenium
        self.action.logout()
        self.useSahanaAdminAccount()
        self.action.login(self._user, self._password )
=======

class CreateLocations(SahanaTest):

    def header(self):
        # Login
        self.action.login("admin@example.com", "testing" )
>>>>>>> MERGE-SOURCE
        self.assertTrue(self.selenium.is_element_present("link=admin@example.com"))
        # Now add the locations
        Locations.shelter = []
        self.initFormDetails()
        
    def initFormDetails(self):
        Locations.formDetails = (
                               ["input", "cr_shelter_location_id",False, None],   #0
                               ["select", "gis_location_L0",True],                #1
                               ["label", "gis_location_label_L0",True],           #2
                               ["a", "gis_location_add-btn",True],                #3
                               ["input", "cr_shelter_location_id",False],         #4
                               ["select", "gis_location_L1",False],               #5
                               ["label", "gis_location_label_L1",False],          #6
                               ["select", "gis_location_L2",False],               #7
                               ["label", "gis_location_label_L2",False],          #8
                               ["select", "gis_location_L3",False],               #9
                               ["label", "gis_location_label_L3",False],          #10
                               ["select", "gis_location_L4",False],               #11
                               ["label", "gis_location_label_L4",False],          #12
                               ["select", "gis_location_", False],                #13
                               ["label", "gis_location_label_", False],           #14
                               ["input", "gis_location_name", False],             #15
                               ["div", "gis_location_name_label", False],         #16
                               ["a", "gis_location_details-btn", False],          #17
                               ["a", "gis_location_cancel-btn", False],           #18
                               ["a", "gis_location_search-btn", True],            #19
                               ["textarea", "gis_location_addr_street", False],   #20
                               ["label", "gis_location_addr_street_label", False],#21
                               ["label", "gis_location_lat_label", False],        #22
                               ["input", "gis_location_lat", False],              #23
                               ["label", "gis_location_lon_label", False],        #24
                               ["input", "gis_location_lon", False],              #25
                               ["a", "gis_location_map-btn", False],              #26
                               ["div", "gis_location_advanced_div", False],       #27
                           )


    def makeNameUnique(self, name):
        return self.holder+name+self.holder
    
    def loadLocations(self):
        """ Create locations for testing the Locations Selector """
<<<<<<< TREE
        Locations.line = []
        source = open("../data/location.txt", "r")
        values = source.readlines()
        source.close()
        # wrap all location names with the holder __TEST__
        # This makes deletion of a unique name possible
        for location in values:
            name = level = parent = lat = long = None
            details = location.split(',')
            if len(details) >= 1: name = details[0].strip()
            if len(details) >= 2: level = details[1].strip()
            if len(details) >= 3: parent = details[2].strip()
            if len(details) >= 4: lat = details[3].strip()
            if len(details) >= 5: long = details[4].strip()
            self.action.addLocation(self.holder, name, level, parent, lat, long)
            Locations.line.append(self.makeNameUnique(name))
            
    def openRecord(self, name):
        """ Open an existing record """
        sel = self.selenium
        # Load the Shelter List page
        sel.open("/eden/cr/shelter")
        # Search for the Record
        self.action.searchUnique(name)

        # Open it
        sel.click("link=Open")
        sel.wait_for_page_to_load("30000")
        # Check that the correct record is loaded
        self.assertEqual(name, sel.get_value("cr_shelter_name"))

    def test_loadTestData(self):
        """ Load all the test location """
        self.loadLocations()

    
    def test_removeTestData(self):
        """ Remove all the data added by this test case """
        pass
    
    def test_locationEmpty(self):
        """ Create a new Shelter without any Location specified """
        sel = self.selenium
        self.useSahanaUserAccount()
        self.action.login(self._user, self._password )
        sel.open("/eden/cr/shelter/create")
        self.action.checkForm(Locations.formDetails,
                              (),
                              ()
                             )
        # Fill in the mandatory fields
        sel.type("cr_shelter_name", "Shelter with no Location")
        # Save the form
        Locations.shelter.append("Shelter with no Location")
        sel.click("//input[@value='Save']")
        sel.wait_for_page_to_load("30000")
        self.action.successMsg("Shelter added")
        print "New shelter created"
        # Load the Shelter
        self.openRecord("Shelter with no Location")
        # Check that the location is currently blank
        self.action.checkForm(Locations.formDetails,
                              (),
                              ()
                             )

        # Save the form (without changes)
        sel.click("//input[@value='Save']")
        sel.wait_for_page_to_load("30000")
        self.assertTrue(self.action.successMsg("Shelter updated"))
        # Shelter has correct location
        heading = sel.get_text("//div[@id='rheader']/div/table/tbody")
        self.assertTrue(re.search(r"Name:\s*Shelter with no Location\s*Location:\s*-",heading))

    def test_addL0Location(self):
        """ Update an existing Shelter without any Location specified to an L0 """
        sel = self.selenium
        self.useSahanaUserAccount()
        self.action.login(self._user, self._password )
        self.openRecord("Shelter with no Location")
        # Check that the location is still blank
        
        self.action.checkForm(Locations.formDetails,
                              (),
                              ()
                             )
        # Select the L0
        sel.select("gis_location_L0", "label=Haiti")
        # Check that L1 dropdown appears correctly
        time.sleep(4)
        self.assertTrue(re.search("Select a location..."
                                  , sel.get_table("//div[@id='content']/div[2]/form/table.11.0")
                                  ))
        # Save the form (with changes)
        sel.click("//input[@value='Save']")
        sel.wait_for_page_to_load("30000")
        self.assertTrue(self.action.successMsg("Shelter updated"))
        # Shelter has correct location
        print "Level 0 Location added "
        # Load again
        self.openRecord("Shelter with no Location")
        # Check that the location is set
        heading = sel.get_text("//div[@id='rheader']/div/table/tbody")
        self.assertTrue(re.search(r"Name:\s*Shelter with no Location\s*Location:\s*Haiti",heading))
        location = sel.get_attribute("//a[starts-with(@onclick, 's3_viewMap')]/@onclick")
        location_id = location.split("(")[1].split(")")[0]
        
        Locations.formDetails[0][3]=location_id
        Locations.formDetails[5][2]=True
        Locations.formDetails[6][2]=True
        self.action.checkForm(Locations.formDetails,
                              (),
                              ()
                             )

    def test_removeL0Location(self):
        """ Update an existing Shelter with an L0 Location to have no location """
        sel = self.selenium
        self.useSahanaUserAccount()
        self.action.login(self._user, self._password )
        self.openRecord("Shelter with no Location")
        # Check that the details are correct
        heading = sel.get_text("//div[@id='rheader']/div/table/tbody")
        self.assertTrue(re.search(r"Name:\s*Shelter with no Location\s*Location:\s*Haiti",heading))
        # Check that the location is currently set
        location = sel.get_attribute("//a[starts-with(@onclick, 's3_viewMap')]/@onclick")
        location_id = location.split("(")[1].split(")")[0]
        self.assertEqual(location_id, sel.get_value("cr_shelter_location_id"))
        # Check that the dropdown is set
        self.assertEqual(location_id, sel.get_value("gis_location_L0"))
        self.action.checkForm(Locations.formDetails,
                              (),
                              ()
                             )



        # De-select the L0
        sel.select("gis_location_L0", "label=Select a location...")
        # Check that the real location has been set to blank
        self.assertEqual("", sel.get_value("cr_shelter_location_id"))
        # Check that L1 dropdown disappears correctly
        time.sleep(1)
        Locations.formDetails[0][3]=""
        Locations.formDetails[5][2]=False
        Locations.formDetails[6][2]=False
        self.action.checkForm(Locations.formDetails,
                              (),
                              ()
                             )
        # Save the form (with changes)
        sel.click("//input[@value='Save']")
        sel.wait_for_page_to_load("30000")
        self.assertTrue(self.action.successMsg("Shelter updated"))
        # Load again
        self.openRecord("Shelter with no Location")
        heading = sel.get_text("//div[@id='rheader']/div/table/tbody")
        self.assertTrue(re.search(r"Name:\s*Shelter with no Location\s*Location:\s*-",heading))
        Locations.formDetails[0][3]=""
        Locations.formDetails[5][2]=False
        Locations.formDetails[6][2]=False
        self.action.checkForm(Locations.formDetails,
                              (),
                              ()
                             )

    def test_locationNoParent(self):
        """ Create a new Shelter with a parentless Location """
        sel = self.selenium
        self.useSahanaUserAccount()
        self.action.login(self._user, self._password )
        sel.open("/eden/cr/shelter/create")
        self.initFormDetails()
        self.action.checkForm(Locations.formDetails,
                              (),
                              ()
                             )
        # Fill in the mandatory fields
        sel.type("cr_shelter_name", "Shelter with no Parent")
        # Create a new location
        sel.click("gis_location_add-btn")
        sel.type("gis_location_name", "Location with no Parent")
        # Save the form
        Locations.shelter.append("Shelter with no Parent")
        sel.click("//input[@value='Save']")
        sel.wait_for_page_to_load("30000")
        self.action.successMsg("Shelter added")
        # Load again
        self.openRecord("Shelter with no Parent")
        # Shelter has correct location
        heading = sel.get_text("//div[@id='rheader']/div/table/tbody")
        self.assertTrue(re.search(r"Name:\s*Shelter with no Parent\s*Location:\s*Location with no Parent",heading))
        location = sel.get_attribute("//a[starts-with(@onclick, 's3_viewMap')]/@onclick")
        location_id = location.split("(")[1].split(")")[0]
        
        Locations.formDetails[13][2]=True
        Locations.formDetails[14][2]=True
        Locations.formDetails[17][2]=True
        Locations.formDetails[0][3]=location_id
        self.action.checkForm(Locations.formDetails,
                              (),
                              ()
                             )
        
    def lastRun(self):
        # Delete the test organisations
        sel = self.selenium
        self.useSahanaAdminAccount()
        self.action.login(self._user, self._password )
        for location in Locations.line:
            self.action.deleteLocation(location)
        for shelter in Locations.shelter:
            self.action.deleteObject("eden/cr/shelter",shelter,"Shelter")

=======
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
        self.action.successMsg("Location added")
>>>>>>> MERGE-SOURCE

if __name__ == "__main__":
    SahanaTest.setUpHierarchy()
    unittest.main()
