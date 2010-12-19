from selenium import selenium

from sahanaTest import SahanaTest
import unittest, time, re
import actions
import inspect

class OrganisationTest(SahanaTest):
    orgs = []
                
    def firstRun(self):
        self.action.logout(self)
        # Log in as admin an then move to the add organisation page 
        OrganisationTest.selenium.open("/eden/org/organisation/create")
        self.action.errorMsg(self, "Not Authorised")
        self.assertEqual("Login", self.selenium.get_text("//h2"))
        self.useSahanaAdminAccount()
        self.action.login(self, self._user, self._password )
        # Add the test organisations
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
        self.action.successMsg(self,"Organization added")
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
        self.action.checkForm (self,(("input", "org_organisation_name"),
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

    def test_OpenOrgUI(self):
        """ Test to check the elements of the list organisation form
        
        In turn it will check each of the tabs on the list screen
        and ensure that the data on the screen has been properly displayed.   
        """ 
        sel = OrganisationTest.selenium
        sel.open("/eden/org/organisation")
        self.action.searchUnique(self,self.orgs[0])
        sel.click("link=Open")
        sel.wait_for_page_to_load("30000")
        # check that the UI controls are present
        self.action.checkForm (self,(("input", "org_organisation_name"),
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
        self.action.clickTab(self, "Staff")
        self.action.btnLink (self, "show-add-btn", "Add Staff")
            
        self.action.clickTab(self, "Offices")
        self.action.btnLink (self, "show-add-btn", "Add Office")

        self.action.clickTab(self, "Warehouses")
        self.action.btnLink (self, "show-add-btn", "Add Warehouse")

        self.action.clickTab(self, "Assessments")
#        self.action.btnLink (self, "show-add-btn", "Add Assessment")

        self.action.clickTab(self, "Projects")
        self.action.btnLink (self, "show-add-btn", "Add Project")

        self.action.clickTab(self, "Activities")
        self.action.btnLink (self, "show-add-btn", "Add Activity")

    def lastRun(self):
        # Delete the test organisations
        sel = OrganisationTest.selenium
        sel.open("/eden/org/organisation")
        for org in OrganisationTest.orgs:
            self.action.searchUnique(self,org)
            sel.click("link=Delete")
            self.assertTrue(re.search(r"^Sure you want to delete this object[\s\S]$", sel.get_confirmation()))
            # pause to allow the delete to work
            self.action.successMsg(self,"Organization deleted")
    
if __name__ == "__main__":
    SahanaTest.setUpHierarchy()
    unittest.main()
    OrganisationTest.selenium.stop()
