from sahanaTest import SahanaTest
import unittest, time, re

class Locations(SahanaTest):
    holder = "__TEST__"
    _sortList = ("loadTestData",
                 "test_locationEmpty",
                 "test_addL0Location",
                 "test_removeL0Location",
                 "test_locationNoParent",
                 "test_locationL0",
                 "test_locationInL0",
                 "test_locationL1",
                 "test_locationInL1",
                 "removeTestData",
                 )
    
    def firstRun(self):
        sel = self.selenium
        self.action.logout()
        self.useSahanaAdminAccount()
        self.action.login(self._user, self._password)
        self.assertTrue(self.selenium.is_element_present("link=admin@example.com"))
        # Now add the locations
        Locations.shelter = []
        self.initFormDetails()
        
    def initFormDetails(self):
        Locations.formDetails = (
                               ["input", "cr_shelter_location_id", False, None],  #0
                               ["select", "gis_location_L0", True],               #1
                               ["label", "gis_location_label_L0", True],          #2
                               ["a", "gis_location_add-btn", True],               #3
                               ["input", "cr_shelter_location_id", False],        #4
                               ["select", "gis_location_L1", False],              #5
                               ["label", "gis_location_label_L1", False],         #6
                               ["select", "gis_location_L2", False],              #7
                               ["label", "gis_location_label_L2", False],         #8
                               ["select", "gis_location_L3", False],              #9
                               ["label", "gis_location_label_L3", False],         #10
                               ["select", "gis_location_L4", False],              #11
                               ["label", "gis_location_label_L4", False],         #12
                               ["select", "gis_location_", False],                #13
                               ["label", "gis_location_label_", False],           #14
                               ["input", "gis_location_name", False],             #15
                               ["div", "gis_location_name_label", False],         #16
                               ["a", "gis_location_details-btn", False],          #17
                               ["a", "gis_location_cancel-btn", False],           #18
                               ["a", "gis_location_search-btn", True],            #19
                               ["textarea", "gis_location_addr_street", False, None],   #20
                               ["label", "gis_location_addr_street_label", False],#21
                               ["label", "gis_location_lat_label", False],        #22
                               ["input", "gis_location_lat", False, None],        #23
                               ["label", "gis_location_lon_label", False],        #24
                               ["input", "gis_location_lon", False, None],        #25
                               ["a", "gis_location_map-btn", False],              #26
                               ["div", "gis_location_advanced_div", False],       #27
                           )
        Locations.formHeading = {"Name:"     : "-",
                                 "Location:" : "-"
                                }

    def makeNameUnique(self, name):
        return self.holder + name + self.holder
    
    def loadLocations(self):
        """ Create locations for testing the Locations Selector """
        sel = self.selenium
        Locations.line = []
        source = open("../data/location.txt", "r")
        values = source.readlines()
        source.close()
        # wrap all location names with the holder __TEST__
        # This makes deletion of a unique name possible
        for location in values:
            name = level = parent = lat = lon = None
            details = location.split(",")
            if len(details) >= 1:
                name = details[0].strip()
            if len(details) >= 2:
                level = details[1].strip()
            if len(details) >= 3:
                parent = details[2].strip()
            if len(details) >= 4:
                lat = details[3].strip()
            if len(details) >= 5:
                lon = details[4].strip()
            # Load the Create Location page
            sel.open("/eden/gis/location")
            if self.action.search(self.makeNameUnique(name), "Showing 0 to 0 of 0 entries"):
                self.action.addLocation(self.holder, name, level, parent, lat, lon)
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

    def loadTestData(self):
        """ Load all the test location """
        self.loadLocations()
    
    def removeTestData(self):
        """ Remove all the data added by this test case """
        sel = self.selenium
        self.useSahanaAdminAccount()
        self.action.login(self._user, self._password )
        for shelter in Locations.shelter:
            self.action.deleteObject("eden/cr/shelter", shelter, "Shelter")
        #return # remove comment to keep the locations for testing purposes
        for location in Locations.line:
            self.action.deleteLocation(location)

    
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
        self.action.saveForm("Shelter added")
        Locations.shelter.append("Shelter with no Location")
        print "New shelter created"
        # Load the Shelter
        self.openRecord("Shelter with no Location")
        # Check that the location is currently blank
        self.action.checkForm(Locations.formDetails,
                              (),
                              ()
                             )

        # Save the form (without changes)
        self.action.saveForm("Shelter updated")
        # Shelter has correct location
        Locations.formHeading["Name:"] = "Shelter with no Location"
        self.action.checkHeading(Locations.formHeading)

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
        # Save the form (with changes)
        self.action.saveForm("Shelter updated")
        print "Level 0 Location added "
        # Load again
        self.openRecord("Shelter with no Location")
        # Check that the location is set
        self.action.checkHeading({"Name:" : "Shelter with no Location",
                                  "Location:" : "Haiti",
                                 })

        location = sel.get_attribute("//a[starts-with(@onclick, 's3_viewMap')]/@onclick")
        location_id = location.split("(")[1].split(")")[0]
        
        Locations.formDetails[0][3] = location_id
        Locations.formDetails[5][2] = True
        Locations.formDetails[6][2] = True
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
        self.action.checkHeading({"Name:" : "Shelter with no Location",
                                  "Location:" : "Haiti",
                                 })
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
        # Save the form (with changes)
        self.action.saveForm("Shelter updated")
        # Load again
        self.openRecord("Shelter with no Location")
        self.action.checkHeading({"Name:" : "Shelter with no Location",
                                  "Location:" : "-",
                                 })
        Locations.formDetails[0][3] = ""
        Locations.formDetails[5][2] = False
        Locations.formDetails[6][2] = False
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
        Locations.line.append("Location with no Parent")
        self.action.saveForm("Shelter added")
        # Load again
        self.openRecord("Shelter with no Parent")
        # Shelter has correct location
        self.action.checkHeading({"Name:" : "Shelter with no Parent",
                                  "Location:" : "Location with no Parent",
                                 })
        location = sel.get_attribute("//a[starts-with(@onclick, 's3_viewMap')]/@onclick")
        location_id = location.split("(")[1].split(")")[0]
        
        Locations.formDetails[13][2] = True
        Locations.formDetails[14][2] = True
        Locations.formDetails[17][2] = True
        Locations.formDetails[0][3] = location_id
        self.action.checkForm(Locations.formDetails,
                              (),
                              ()
                             )
        # Deselect the L0 location
        sel.select("gis_location_", "label=Select a location...")
        # Check that the real location has been set to blank
        self.assertEqual("", sel.get_text("cr_shelter_location_id"))
        # Save the form (with changes)
        self.action.saveForm("Shelter updated")
        # Load again
        self.openRecord("Shelter with no Parent")
        self.action.checkHeading({"Name:" : "Shelter with no Parent",
                                  "Location:" : "-",
                                 })
        Locations.formDetails[0][3] = ""
        Locations.formDetails[13][2] = False
        Locations.formDetails[14][2] = False
        Locations.formDetails[17][2] = False
        self.action.checkForm(Locations.formDetails,
                              (),
                              ()
                             )
        sel.click("gis_location_add-btn")
        # Fill in a Name & Address
        sel.type("gis_location_name", "New parentless Location")
        sel.type("gis_location_addr_street", "45 Sheep Street")

        # Open Map
        sel.click("gis_location_map-btn")
        # Check it's now visible
        time.sleep(1)
        self.failUnless(sel.is_visible("gis-map-window"))
        # Close Map
        sel.click("//div[@id='gis-map-window']/div/div/div/div/div[contains(@class, 'x-tool-close')]")
        # Check it's not visible
        self.failIf(sel.is_visible("gis-map-window"))
        # Open the Advanced Tab
        sel.click("gis_location_advanced_checkbox")
        # Check that the components appear correctly
        # Fill in Lat & Lon
        Locations.formDetails[3][2] = False
        Locations.formDetails[15][2] = True
        Locations.formDetails[16][2] = True
        Locations.formDetails[18][2] = True
        Locations.formDetails[20][2] = True
        Locations.formDetails[21][2] = True
        Locations.formDetails[22][2] = True
        Locations.formDetails[23][2] = True
        Locations.formDetails[24][2] = True
        Locations.formDetails[25][2] = True
        Locations.formDetails[26][2] = True
        Locations.formDetails[27][2] = True
        self.action.checkForm(Locations.formDetails,
                              (),
                              ()
                             )
        sel.type("gis_location_lat", "51")
        sel.type("gis_location_lon", "1")

        # Open Converter
        sel.click("gis_location_converter-btn")
        # Check it's now visible
        time.sleep(1)
        self.failUnless(sel.is_visible("gis-convert-win"))
        # @ToDo: Use this to do a conversion
        # Close Converter
        sel.click("//div[@id='gis-convert-win']/div/div/div/div/div[contains(@class, 'x-tool-close')]")
        # Check it's not visible
        self.failIf(sel.is_visible("gis-convert-win"))
        # Fill in Lat & Lon
        sel.type("gis_location_lat", "51")
        sel.type("gis_location_lon", "1")

        self.action.saveForm("Shelter updated")
        Locations.line.append("New parentless Location")
        # Load again
        self.openRecord("Shelter with no Parent")
        self.action.checkHeading({"Name:" : "Shelter with no Parent",
                                  "Location:" : "New parentless Location (N 51.0 E 1.0)",
                                 })

        self.initFormDetails()
        location = sel.get_attribute("//a[starts-with(@onclick, 's3_viewMap')]/@onclick")
        location_id = location.split("(")[1].split(")")[0]
        Locations.formDetails[0][3] = location_id
        Locations.formDetails[13][2] = True
        Locations.formDetails[14][2] = True
        Locations.formDetails[17][2] = True
        Locations.formDetails[23][3] = '51.0'
        Locations.formDetails[25][3] = '1.0'
        self.action.checkForm(Locations.formDetails,
                              (),
                              ()
                             )
        # Click on 'Details' button
        sel.click("gis_location_details-btn")
        Locations.formDetails[20][2] = True
        Locations.formDetails[20][3] = "45 Sheep Street"
        Locations.formDetails[21][2] = True
        Locations.formDetails[26][2] = True
        Locations.formDetails[27][2] = True
        self.action.checkForm(Locations.formDetails,
                              (),
                              ()
                             )
        # Open the Advanced Tab
        sel.click("gis_location_advanced_checkbox")
        Locations.formDetails[22][2] = True
        Locations.formDetails[23][2] = True
        Locations.formDetails[24][2] = True
        Locations.formDetails[25][2] = True
        self.action.checkForm(Locations.formDetails,
                              (),
                              ()
                             )
        # Following save is required because the advanced checkbox has been pressed
        # see ticket #885 http://eden.sahanafoundation.org/ticket/885
        self.action.saveForm("Shelter updated")

        # Now update the shelter to have a L0 location
        self.openRecord("Shelter with no Parent")
        # Select the L0
        sel.select("gis_location_L0", "label=Haiti")
        self.initFormDetails()
        Locations.formDetails[5][2] = True
        Locations.formDetails[6][2] = True
        self.action.checkForm(Locations.formDetails,
                              (),
                              ()
                             )
        self.action.saveForm("Shelter updated")
        
    def test_locationL0(self):
        """ Create a new Shelter with an L0 location """
        sel = self.selenium
        # Login
        self.useSahanaUserAccount()
        self.action.login(self._user, self._password )
        sel.open("/eden/cr/shelter/create")
        # Fill in the mandatory fields
        sel.type("cr_shelter_name", "Shelter with an L0 Location")
        # Select the L0
        sel.select("gis_location_L0", "label=Haiti")
        # Save the form
        Locations.shelter.append("Shelter with an L0 Location")
        self.action.saveForm("Shelter added")
        # Load again
        self.openRecord("Shelter with an L0 Location")

        self.action.checkHeading({"Name:" : "Shelter with an L0 Location",
                                  "Location:" : "Haiti",
                                 })
        location = sel.get_attribute("//a[starts-with(@onclick, 's3_viewMap')]/@onclick")
        self.initFormDetails()
        location_id = location.split("(")[1].split(")")[0]
        Locations.formDetails[0][3] = location_id
        Locations.formDetails[5][2] = True
        Locations.formDetails[6][2] = True
        self.action.checkForm(Locations.formDetails,
                              (),
                              ()
                             )

    def test_locationInL0(self):
        """ Create a new Shelter inside an L0 location
            NB This should fail if deployment_settings.gis.strict_hierarchy = True
        """
        sel = self.selenium
        # Login
        self.useSahanaUserAccount()
        self.action.login(self._user, self._password )
        sel.open("/eden/cr/shelter/create")
        # Fill in the mandatory fields
        sel.type("cr_shelter_name", "Shelter within L0 Location")
        # Select the L0
        sel.select("gis_location_L0", "label=Haiti")
        # Create a new location
        sel.click("gis_location_add-btn")
        sel.type("gis_location_name", "Specific Location in L0")
        # Save the form
        Locations.shelter.append("Shelter within L0 Location")
        Locations.line.append("Specific Location in L0")
        self.action.saveForm("Shelter added")
        # Load again
        self.openRecord("Shelter within L0 Location")
        self.action.checkHeading({"Name:" : "Shelter within L0 Location",
                                  "Location:" : "Specific Location in L0",
                                 })
        location = sel.get_attribute("//a[starts-with(@onclick, 's3_viewMap')]/@onclick")
        location_id = location.split("(")[1].split(")")[0]
        Locations.formDetails[0][3] = location_id
        Locations.formDetails[5][2] = True
        Locations.formDetails[6][2] = True
        Locations.formDetails[13][2] = True
        Locations.formDetails[14][2] = True
        Locations.formDetails[17][2] = True
        self.action.checkForm(Locations.formDetails,
                              (),
                              ()
                             )

    def test_locationL1(self):
        """ Create a new Shelter with an L1 location """
        sel = self.selenium
        # Login
        self.useSahanaUserAccount()
        self.action.login(self._user, self._password )
        sel.open("/eden/cr/shelter/create")
        # Fill in the mandatory fields
        sel.type("cr_shelter_name", "Shelter with an L1 Location")
        # Select the L0
        sel.select("gis_location_L0", "label=Haiti")
        # wait for the L1 list to be populated
        L1 = self.makeNameUnique("Ouest")
        for i in range(10):
            try:
                # Select the L1
                sel.select("gis_location_L1", "label=%s" % L1)
                break
            except:
                time.sleep(1)

        # Save the form
        Locations.shelter.append("Shelter with an L1 Location")
        self.action.saveForm("Shelter added")
        # Load again
        self.openRecord("Shelter with an L1 Location")
        self.action.checkHeading({"Name:" : "Shelter with an L1 Location",
                                  "Location:" : "%s (Haiti)" % L1,
                                 })
        location = sel.get_attribute("//a[starts-with(@onclick, 's3_viewMap')]/@onclick")
        location_id = location.split("(")[1].split(")")[0]
        self.initFormDetails()
        Locations.formDetails[0][3] = location_id
        Locations.formDetails[5][2] = True
        Locations.formDetails[6][2] = True
        Locations.formDetails[7][2] = True
        Locations.formDetails[8][2] = True
        self.action.checkForm(Locations.formDetails,
                              (),
                              ()
                             )


    def test_locationInL1(self):
        """ Create a new Shelter inside an L1 location """
        sel = self.selenium
        # Login
        self.useSahanaUserAccount()
        self.action.login(self._user, self._password )
        sel.open("/eden/cr/shelter/create")

        # Fill in the mandatory fields
        sel.type("cr_shelter_name", "Shelter within L1 Location")
        # Select the L0
        sel.select("gis_location_L0", "label=Haiti")
        # wait for the L1 list to appear
        time.sleep(4)
        for i in range(10):
            if sel.is_visible("gis_location_L1"):
                break
            time.sleep(1)
        self.assertTrue(sel.is_visible("gis_location_L1"))
        # Select the L1
        L1 = self.makeNameUnique("Ouest")
        sel.select("gis_location_L1", "label=%s" % L1)
        # Create a new location
        sel.click("gis_location_add-btn")
        sel.type("gis_location_name", "Specific Location in L1")
        # Save the form
        Locations.shelter.append("Shelter within L1 Location")
        Locations.line.append("Specific Location in L1")
        self.action.saveForm("Shelter added")
        # Load again
        self.openRecord("Shelter within L1 Location")
        self.action.checkHeading({"Name:" : "Shelter within L1 Location",
                                  "Location:" : "Specific Location in L1",
                                 })
        location = sel.get_attribute("//a[starts-with(@onclick, 's3_viewMap')]/@onclick")
        location_id = location.split("(")[1].split(")")[0]
        Locations.formDetails[0][3] = location_id
        Locations.formDetails[5][2] = True
        Locations.formDetails[6][2] = True
        Locations.formDetails[7][2] = True
        Locations.formDetails[8][2] = True
        Locations.formDetails[13][2] = True
        Locations.formDetails[14][2] = True
        Locations.formDetails[17][2] = True
        self.action.checkForm(Locations.formDetails,
                              (),
                              ()
                             )


if __name__ == "__main__":
    SahanaTest.setUpHierarchy()
    unittest.main()
