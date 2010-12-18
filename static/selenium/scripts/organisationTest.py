from selenium import selenium

from sahanaTest import SahanaTest
import unittest, time, re
import actions
import inspect

class OrganisationTest(SahanaTest):
    orgs = []
    
    @classmethod
    def setUpClass(cls):
        cls.start()

    def setUp(self):
        if OrganisationTest.testcaseStartedCount == 0:
            OrganisationTest.testcaseStartedCount += 1
            self.firstRun()
                
    def firstRun(self):
        # Log in as admin an then move to the add organisation page 
        OrganisationTest.selenium.open("/eden/org/organisation/create")
        time.sleep(1)
        self.assertEqual("Not Authorised", self.selenium.get_text("//div[@class=\"error\"]"))
        self.assertEqual("Login", self.selenium.get_text("//h2"))
        self.action.login(self, "admin@example.com", "testing" )
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

        self.action.logout(self)

    def tearDown(self):
        if OrganisationTest.finish():
            self.lastRun()
            
OrganisationTest.setUpClass()
    
if __name__ == "__main__":
    SahanaTest.setUpHierarchy()
    unittest.main()
    OrganisationTest.selenium.stop()
