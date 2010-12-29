from sahanaTest import SahanaTest
import unittest, re

class OrganisationTest(SahanaTest):
    """ Test the Organisation registry """
    _sortList = ("test_CreateOrgUI", "test_OpenOrgUIAdmin", "test_OpenOrgUIUser")
    
    def firstRun(self):
        sel = OrganisationTest.selenium
        self.action.logout()
        # Log in as admin an then move to the add organisation page 
        sel.open("/eden/org/organisation/create")
        self.action.errorMsg("Not Authorised")
        self.assertEqual("Login", self.selenium.get_text("//h2"))
        self.useSahanaAdminAccount()
        self.action.login(self._user, self._password )
        # Add the test organisations
        OrganisationTest.orgs = []
        self.addOrg()

    
    def create_organisation(self, name, acronym, type, cluster, country, website):
        sel = OrganisationTest.selenium

        name = name.strip()
        acronym = acronym.strip()
        type = type.strip()
        cluster = cluster.strip()
        country = country.strip()
        website = website.strip()
        
        sel.open("eden/org/organisation/create")
        self.assertEqual("Add Organization", sel.get_text("//h2"))
        sel.type("org_organisation_name", name)
        sel.type("org_organisation_acronym", acronym)
        sel.select("org_organisation_type", "label="+type)
        sel.click("//option[@value='10']")
        sel.select("org_organisation_cluster_id", "label="+cluster)
        sel.select("org_organisation_country", "label="+country)
        sel.type("org_organisation_website", website)
        sel.click("//input[@value='Save']")
        sel.wait_for_page_to_load("30000")
        self.action.successMsg("Organization added")
        self.assertEqual("List Organizations", sel.get_text("//h2"))
        print "Organisation %s created" % (name)
        
    def addOrg(self):
        sel = OrganisationTest.selenium
        source = open("../data/organisation.txt", "r")
        values = source.readlines()
        source.close()
        for org in values:
            details = org.split(',')
            if len(details) == 6:
                self.create_organisation(details[0].strip(),
                                         details[1].strip(),
                                         details[2].strip(),
                                         details[3].strip(),
                                         details[4].strip(),
                                         details[5].strip(),
                                         )
                OrganisationTest.orgs.append(details[0].strip())

    def test_CreateOrgUI(self):
        """ Test to check the elements of the create organisation form """ 
        sel = OrganisationTest.selenium
        sel.open("/eden/org/organisation/create")
        # check that the UI controls are present
        self.action.checkForm ((("input", "org_organisation_name"),
                    ("input", "org_organisation_acronym"),
                    ("select", "org_organisation_type"),
                    ("select", "org_organisation_cluster_id"),
                    ("select", "org_organisation_country"),
                    ("input", "org_organisation_website"),
                    ("input", "org_organisation_twitter"),
                    ("input", "org_organisation_donation_phone"),
                    ("textarea", "org_organisation_comments")
                   ),
                   ("Save",),
                   ("Twitter", "Donation", "Comments")
                  )

    def test_OpenOrgUIAdmin(self):
        """ Test to check the elements of the list organisation form logged in with the admin account
        
        In turn it will check each of the tabs on the list screen
        and ensure that the data on the screen has been properly displayed.   
        """ 
        sel = OrganisationTest.selenium
        self.useSahanaAdminAccount()
        self.action.login(self._user, self._password )
        sel.open("/eden/org/organisation")
        self.action.searchUnique(self.orgs[0])
        sel.click("link=Open")
        sel.wait_for_page_to_load("30000")
        # check that the UI controls are present
        self.action.checkForm ((("input", "org_organisation_name"),
                    ("input", "org_organisation_acronym"),
                    ("select", "org_organisation_type"),
                    ("select", "org_organisation_cluster_id"),
                    ("select", "org_organisation_country"),
                    ("input", "org_organisation_website"),
                    ("input", "org_organisation_twitter"),
                    ("input", "org_organisation_donation_phone"),
                    ("textarea", "org_organisation_comments")
                   ),
                   ("Save",),
                   ("Twitter", "Donation", "Comments")
                  )
        self.action.clickTab("Staff")
        self.action.btnLink ("show-add-btn", "Add Staff")
            
        self.action.clickTab("Offices")
        self.action.btnLink ("show-add-btn", "Add Office")

        self.action.clickTab("Warehouses")
        self.action.btnLink ("show-add-btn", "Add Warehouse")

        self.action.clickTab("Assessments")
        self.action.btnLink ("add-btn", "Add Assessment")

        self.action.clickTab("Projects")
        self.action.btnLink ("show-add-btn", "Add Project")

        self.action.clickTab("Activities")
        self.action.btnLink ("show-add-btn", "Add Activity")

    def test_OpenOrgUIUser(self):
        """ Test to check the elements of the list organisation form when not logged in 
        
        In turn it will check each of the tabs on the list screen
        and ensure that the data on the screen has been properly displayed.   
        """ 
        sel = OrganisationTest.selenium
        self.action.logout()
        sel.open("/eden/org/organisation")
        self.action.searchUnique(self.orgs[0])
        sel.click("link=Open")
        sel.wait_for_page_to_load("30000")
        
        self.action.clickTab("Staff")
        self.action.noBtnLink ("show-add-btn", "Add Staff")
            
        self.action.clickTab("Offices")
        self.action.noBtnLink ("show-add-btn", "Add Office")

        self.action.clickTab("Warehouses")
        self.action.noBtnLink ("show-add-btn", "Add Warehouse")

        self.action.clickTab("Assessments")
        self.action.noBtnLink ("add-btn", "Add Assessment")

        self.action.clickTab("Projects")
        self.action.noBtnLink ("show-add-btn", "Add Project")

        self.action.clickTab("Activities")
        self.action.noBtnLink ("show-add-btn", "Add Activity")

    def lastRun(self):
        # Delete the test organisations
        sel = OrganisationTest.selenium
        self.useSahanaAdminAccount()
        self.action.login(self._user, self._password )
        sel.open("/eden/org/organisation")
        for org in OrganisationTest.orgs:
            self.action.searchUnique(org)
            sel.click("link=Delete")
            self.assertTrue(re.search(r"^Sure you want to delete this object[\s\S]$", sel.get_confirmation()))
            self.action.successMsg("Organization deleted")
    
if __name__ == "__main__":
    SahanaTest.setUpHierarchy()
    unittest.main()
    OrganisationTest.selenium.stop()
