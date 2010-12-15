from selenium import selenium
import unittest, time, re
import actions

class OrganisationTest(unittest.TestCase):
    def setUp(self):
        self.verificationErrors = []
        self.action = actions.Action()
        self.selenium = selenium("localhost", 4444, "*chrome", "http://127.0.0.1:8000/")
        self.selenium.start()
    
    def create_organisation(self, name, acronym, type, cluster, country, website):
        sel = self.selenium

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
        time.sleep(1)
        self.assertEqual("Organization added", sel.get_text("//div[@class=\"confirmation\"]"))
        self.assertEqual("List Organizations", sel.get_text("//h2"))
        
    def test_org_add(self):
        sel = self.selenium
        sel.open("/eden/default/index")
        sel.click("link=Organisation Registry")
        sel.wait_for_page_to_load("30000")
        sel.click("link=Add")
        sel.wait_for_page_to_load("30000")
        time.sleep(1)
        self.assertEqual("Not Authorised", sel.get_text("//div[@class=\"error\"]"))
        self.assertEqual("Login", sel.get_text("//h2"))
        self.action.login(self, "admin@example.com", "testing" )
        
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
        self.action.logout(self)

    def test_org_UI(self):
        sel = self.selenium
        # Log in as admin an then move to the add organisation page 
        self.action.login(self, "admin@example.com", "testing" )
        sel.open("/eden/org/organisation/create")
        # check that the UI controls are present
        self.action.element(self,"input", "org_organisation_name")
        self.action.element(self,"input", "org_organisation_acronym")
        self.action.element(self,"select", "org_organisation_type")
        self.action.element(self,"select", "org_organisation_cluster_id")
        self.action.element(self,"select", "org_organisation_country")
        self.action.element(self,"input", "org_organisation_website")
        self.action.element(self,"input", "org_organisation_twitter")
        self.action.element(self,"input", "org_organisation_donation_phone")
        self.action.element(self,"textarea", "org_organisation_comments")
        self.action.button(self,"Save")
        
        # check the help balloons
        self.action.helpBallon(self, "Twitter")
        self.action.helpBallon(self, "Donation")
        self.action.helpBallon(self, "Comments")
        # Log out
        self.action.logout(self)

            
    def tearDown(self):
        self.selenium.stop()
        self.assertEqual([], self.verificationErrors)

if __name__ == "__main__":
    unittest.main()
